import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import ssl
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Global variables for caching active cameras
active_cameras = []
cameras_lock = threading.Lock()
last_update_time = 0

# Bypass SSL verification for Caltrans feeds
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def load_env():
    """
    Loads environment variables from a local .env file.
    """
    env_path = os.path.join(DIRECTORY, '.env')
    if os.path.exists(env_path):
        print(f"[Server] Loading environment from {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

def check_single_camera(cam):
    """
    Checks if a camera is active by doing a HEAD request.
    Filters out cameras that return 'Temporarily Unavailable' placeholder images (approx 13KB).
    """
    try:
        req = urllib.request.Request(
            cam['img_url'], 
            method='HEAD',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            content_length = response.getheader('Content-Length')
            if content_length:
                size = int(content_length)
                # "Temporarily Unavailable" is typically ~13100 to ~13300 bytes due to timestamp differences
                if 12500 <= size <= 13500:
                    return None
            return cam
    except Exception:
        return None

def update_cameras_worker():
    """
    Background worker that updates the list of active cameras.
    """
    global active_cameras, last_update_time
    
    while True:
        print("[Server] Updating traffic camera list from Caltrans...")
        url = 'https://cwwp2.dot.ca.gov/data/d4/cctv/cctvStatusD04.json'
        
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
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
                        'name': name,
                        'nearby': nearby,
                        'img_url': img_url,
                        'county': location.get('county', ''),
                        'route': location.get('route', ''),
                        'direction': location.get('direction', ''),
                        'latitude': float(location.get('latitude', 0.0)),
                        'longitude': float(location.get('longitude', 0.0))
                    })
            
            print(f"[Server] Found {len(all_cams)} total cameras. Verifying active status concurrently...")
            
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
                results = executor.map(check_single_camera, cams_to_check)
                for res in results:
                    if res:
                        verified_cams.append(res)
            
            with cameras_lock:
                active_cameras = verified_cams
                last_update_time = time.time()
                
            print(f"[Server] Update complete. Found {len(active_cameras)} verified active cameras.")
            
        except Exception as e:
            print(f"[Server] Error updating cameras: {e}")
            
        # Update every 5 minutes
        time.sleep(300)

class CameraProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        # Intercept and dynamically inject API key into index.html
        if path in ('/', '/index.html'):
            try:
                index_path = os.path.join(DIRECTORY, 'index.html')
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
                content = content.replace('{{GOOGLE_MAPS_API_KEY}}', api_key)
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f"Error rendering index: {e}")
            return

        # API Endpoint: Get list of active cameras
        elif path == '/api/cameras':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with cameras_lock:
                response_data = {
                    'last_updated': last_update_time,
                    'cameras': active_cameras
                }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        # API Endpoint: Proxy image requests to bypass CORS/SSL issues if they occur
        elif path == '/api/proxy':
            image_url = query.get('url', [None])[0]
            if not image_url:
                self.send_error(400, "Missing 'url' parameter")
                return
                
            try:
                req = urllib.request.Request(
                    image_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, context=ssl_context, timeout=8) as response:
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response.read())
            except Exception as e:
                self.send_error(500, f"Error proxying image: {e}")
            return
            
        # Fall back to standard static file serving
        return super().do_GET()

def start_server():
    # Load .env variables
    load_env()
    
    # Start the background update thread
    threading.Thread(target=update_cameras_worker, daemon=True).start()
    
    # Wait a few seconds for the initial scan to get some cameras
    print("[Server] Starting initial camera scan, please wait a moment...")
    time.sleep(3)
    
    handler = CameraProxyHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"[Server] Running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[Server] Shutting down...")

if __name__ == '__main__':
    start_server()
