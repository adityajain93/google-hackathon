import urllib.request
import json
import base64
import ssl
import os

class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        
        # Bypass SSL verification for downloading camera feeds
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def fetch_image_base64(self, img_url):
        """Downloads an image from URL and encodes it to base64."""
        try:
            if "youtube.com" in img_url or "youtu.be" in img_url:
                from inputs.youtube_grabber import YoutubeFrameGrabber
                import cv2
                print(f"[GeminiClient] Intercepted YouTube URL: {img_url}. Grabbing frame...")
                frame = YoutubeFrameGrabber.grab_frame(img_url)
                if frame is not None:
                    success, encoded_image = cv2.imencode('.jpg', frame)
                    if success:
                        return base64.b64encode(encoded_image.tobytes()).decode('utf-8')
                raise ValueError("Failed to capture frame from YouTube stream")
            else:
                req = urllib.request.Request(
                    img_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                    img_data = response.read()
                    return base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            print(f"[GeminiClient] Error downloading/capturing image {img_url}: {e}")
            raise

    def analyze_image(self, img_url, prompt):
        """Sends the image and prompt to the Gemini API."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        try:
            # 1. Download image and encode to base64
            img_b64 = self.fetch_image_base64(img_url)
            
            # 2. Prepare payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Use gemini-1.5-flash which is widely available and supports multimodal input
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=20) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                
            # Extract response text
            candidates = resp_data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', 'No analysis returned from Gemini.')
            
            return "Gemini API returned an empty response."

        except Exception as e:
            print(f"[GeminiClient] Error in analyze_image: {e}")
            raise
