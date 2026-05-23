import yt_dlp
import cv2
import urllib.request
import ssl
import re
import os
import tempfile
import time

class YoutubeFrameGrabber:
    _cache = {}        # Key: yt_url, Value: (m3u8_url, expire_time)
    _frame_cache = {}  # Key: yt_url, Value: (frame, timestamp)

    @classmethod
    def grab_frame(cls, yt_url):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Check frame cache (5-second caching for concurrent/immediate requests)
        now = time.time()
        if yt_url in cls._frame_cache:
            frame, cached_at = cls._frame_cache[yt_url]
            if now - cached_at < 5.0:
                print("[YoutubeGrabber] Returning cached frame (instant)")
                return frame
        
        # Check HLS URL cache
        m3u8_url = None
        if yt_url in cls._cache:
            cached_url, expire_at = cls._cache[yt_url]
            if now < expire_at - 120:  # 2 minute safety buffer
                m3u8_url = cached_url
                print(f"[YoutubeGrabber] Using cached HLS URL (expires in {int(expire_at - now)} seconds)")

        try:
            if not m3u8_url:
                print(f"[YoutubeGrabber] Fetching new HLS playlist via yt-dlp for {yt_url}...")
                ydl_opts = {
                    'format': 'worst',
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(yt_url, download=False)
                    m3u8_url = info.get('url')
                    if not m3u8_url:
                        print(f"[YoutubeGrabber] Error: No streaming URL found for {yt_url}")
                        return None
                    
                    # Parse expiration timestamp (usually /expire/1234567/)
                    expire_time = now + 900  # Fallback to 15 mins cache
                    match = re.search(r'/expire/(\d+)', m3u8_url)
                    if match:
                        expire_time = int(match.group(1))
                    cls._cache[yt_url] = (m3u8_url, expire_time)
                    print(f"[YoutubeGrabber] Cached new HLS URL. Expires at {expire_time} (in {int(expire_time - now)} seconds)")
            
            # Fetch latest segment list from m3u8 playlist
            req = urllib.request.Request(m3u8_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                playlist_content = response.read().decode('utf-8')
            
            urls = re.findall(r'(https?://[^\s#]+)', playlist_content)
            if not urls:
                print("[YoutubeGrabber] Error: No segment URLs found in HLS playlist.")
                # Clear cache in case the playlist URL expired early or returned invalid content
                if yt_url in cls._cache:
                    del cls._cache[yt_url]
                return None
            
            # Take the latest segment
            latest_segment_url = urls[-1]
            
            # Download segment to a unique temp file
            with tempfile.NamedTemporaryFile(suffix='.ts', delete=False) as temp_ts:
                temp_path = temp_ts.name
                
            req_seg = urllib.request.Request(latest_segment_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_seg, context=ssl_context, timeout=5) as response:
                with open(temp_path, 'wb') as f:
                    f.write(response.read())
            
            # Read frame using OpenCV
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                print("[YoutubeGrabber] Error: Failed to open downloaded TS segment using OpenCV.")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if ret:
                cls._frame_cache[yt_url] = (frame, now)
                return frame
            else:
                print("[YoutubeGrabber] Error: Failed to read frame from TS segment.")
                return None
        except Exception as e:
            print(f"[YoutubeGrabber] Exception during frame extraction: {e}")
            # Clear cache on exception to force retry next time
            if yt_url in cls._cache:
                del cls._cache[yt_url]
            return None

if __name__ == '__main__':
    # Simple self-test to measure performance improvement
    print("First run (cache cold):")
    t0 = time.time()
    frame1 = YoutubeFrameGrabber.grab_frame('https://www.youtube.com/watch?v=cTi5sCsUSfc')
    t1 = time.time()
    print(f"Time: {t1 - t0:.2f} seconds. Success: {frame1 is not None}")

    print("\nSecond run (cache hot):")
    t2 = time.time()
    frame2 = YoutubeFrameGrabber.grab_frame('https://www.youtube.com/watch?v=cTi5sCsUSfc')
    t3 = time.time()
    print(f"Time: {t3 - t2:.2f} seconds. Success: {frame2 is not None}")
