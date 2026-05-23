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
        self.mock_cams = [
            {
                'id': 'caltrans_mock_0',
                'name': 'I-80 : Bay Bridge Toll Plaza',
                'nearby': 'Oakland',
                'img_url': 'https://images.unsplash.com/photo-1542362567-b07eac790acd?w=800&auto=format&fit=crop&q=80',
                'county': 'Alameda',
                'route': '80',
                'direction': 'West',
                'latitude': 37.8252,
                'longitude': -122.3168
            },
            {
                'id': 'caltrans_mock_1',
                'name': 'US-101 : Golden Gate Bridge',
                'nearby': 'San Francisco',
                'img_url': 'https://images.unsplash.com/photo-1506012787146-f92b2d7d6d96?w=800&auto=format&fit=crop&q=80',
                'county': 'San Francisco',
                'route': '101',
                'direction': 'North',
                'latitude': 37.8199,
                'longitude': -122.4783
            },
            {
                'id': 'caltrans_mock_2',
                'name': 'I-580 : Richmond-San Rafael Bridge',
                'nearby': 'Richmond',
                'img_url': 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=800&auto=format&fit=crop&q=80',
                'county': 'Contra Costa',
                'route': '580',
                'direction': 'West',
                'latitude': 37.9358,
                'longitude': -122.4278
            }
        ]
        self.active_cameras = self.mock_cams
        self.last_update_time = time.time()
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
                
                if verified_cams:
                    with self.lock:
                        old_cams_map = {c['id']: c for c in self.active_cameras}
                        for new_cam in verified_cams:
                            old_cam = old_cams_map.get(new_cam['id'])
                            if old_cam:
                                if 'latest_count_summary' in old_cam:
                                    new_cam['latest_count_summary'] = old_cam['latest_count_summary']
                                if 'latest_count_details' in old_cam:
                                    new_cam['latest_count_details'] = old_cam['latest_count_details']
                                if 'last_analyzed_time' in old_cam:
                                    new_cam['last_analyzed_time'] = old_cam['last_analyzed_time']
                        self.active_cameras = verified_cams
                        self.last_update_time = time.time()
                    print(f"[CaltransFeed] Update complete. Found {len(self.active_cameras)} verified cameras.")
                else:
                    print(f"[CaltransFeed] Verification yielded 0 cameras. Retaining existing active cameras.")
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
