import urllib.request
import urllib.parse
import json
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from inputs.base import BaseFeed

class CaltransFeed(BaseFeed):
    def __init__(self):
        self.active_cameras = []
        self.last_update_time = 0
        self.lock = threading.Lock()
        
        # Bypass SSL verification
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Start background thread to keep list fresh
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _check_single_camera(self, cam):
        try:
            req = urllib.request.Request(
                cam['img_url'], 
                method='HEAD',
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=5) as response:
                content_length = response.getheader('Content-Length')
                if content_length:
                    size = int(content_length)
                    # Filter placeholders
                    if 12500 <= size <= 13500:
                        return None
                return cam
        except Exception:
            return None

    def _update_loop(self):
        while True:
            print("[CaltransFeed] Updating traffic camera list...")
            url = 'https://cwwp2.dot.ca.gov/data/d4/cctv/cctvStatusD04.json'
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                items = data.get('data', [])
                all_cams = []
                for item in items:
                    cctv = item.get('cctv', {})
                    location = cctv.get('location', {})
                    name = location.get('locationName', '')
                    nearby = location.get('nearbyPlace', '')
                    img_url = cctv.get('imageData', {}).get('static', {}).get('currentImageURL', '')
                    
                    if img_url:
                        all_cams.append({
                            'id': f"caltrans_{len(all_cams)}",
                            'name': name,
                            'nearby': nearby,
                            'img_url': img_url,
                            'county': location.get('county', ''),
                            'route': location.get('route', ''),
                            'direction': location.get('direction', ''),
                            'latitude': float(location.get('latitude', 0.0)),
                            'longitude': float(location.get('longitude', 0.0))
                        })
                
                # Prioritize major commute routes
                major_routes = ['80', '101', '280', '580', '680', '880', '24', '92', '4', '84']
                target_cams = []
                other_cams = []
                for cam in all_cams:
                    route = cam['route'].upper()
                    if any(r in route for r in major_routes):
                        target_cams.append(cam)
                    else:
                        other_cams.append(cam)
                
                cams_to_check = (target_cams + other_cams)[:250]
                
                verified_cams = []
                with ThreadPoolExecutor(max_workers=20) as executor:
                    results = executor.map(self._check_single_camera, cams_to_check)
                    for res in results:
                        if res:
                            verified_cams.append(res)
                
                with self.lock:
                    self.active_cameras = verified_cams
                    self.last_update_time = time.time()
                print(f"[CaltransFeed] Update complete. Found {len(self.active_cameras)} verified cameras.")
            except Exception as e:
                print(f"[CaltransFeed] Error updating cameras: {e}")
            
            time.sleep(300)

    def get_devices(self):
        with self.lock:
            return self.active_cameras

    def get_latest_frame(self, device_id):
        # Returns the static image URL for proxying
        with self.lock:
            for cam in self.active_cameras:
                if cam['id'] == device_id:
                    return cam['img_url']
        return None
