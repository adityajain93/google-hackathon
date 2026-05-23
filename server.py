import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import ssl
import threading
import time
import os

from inputs.caltrans import CaltransFeed
from inputs.zoo_feed import ZooFeed
from intelligence.analyzer import Analyzer
from outputs.notifier import Notifier
from agents.camera_analysis_agent import CameraAnalysisAgent
from agents.alert_agent import AlertAgent
import cv2
from agents.scavenger_agent import ScavengerAgent
from inputs.youtube_grabber import YoutubeFrameGrabber
from agents.air_quality_agent import AirQualityAgent


PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
UI_DIRECTORY = os.path.join(DIRECTORY, 'outputs', 'ui')

# Load environment variables
def load_env():
    env_path = os.path.join(DIRECTORY, '.env')
    if os.path.exists(env_path):
        print(f"[Server] Loading environment from {env_path}")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

# Load env before instantiating clients so API keys are available
load_env()

# Initialize modules
caltrans_feed = CaltransFeed()
zoo_feed = ZooFeed()
analyzer = Analyzer()
notifier = Notifier()

# Start unified analysis pipeline
camera_agent = CameraAnalysisAgent(caltrans_feed, zoo_feed, analyzer, notifier)
air_quality_agent = AirQualityAgent(caltrans_feed)
scavenger_agent = ScavengerAgent(caltrans_feed, analyzer.gemini_client)
alert_agent = AlertAgent(analyzer, notifier)

print("[Server] Starting CameraAnalysisAgent + AlertAgent pipeline...")
camera_agent.start()
air_quality_agent.start()
alert_agent.start()


# Bypass SSL context for image proxying
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class CameraProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from UI_DIRECTORY
        super().__init__(*args, directory=UI_DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        # Intercept and dynamically inject API key into index.html
        if path in ('/', '/index.html'):
            try:
                index_path = os.path.join(UI_DIRECTORY, 'index.html')
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

        # API Endpoint: Get list of active cameras (from selected feed)
        elif path == '/api/cameras':
            feed_type = query.get('feed', ['traffic'])[0]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if feed_type == 'zoo':
                cams = zoo_feed.get_devices()
                last_updated = time.time()
                is_loading = False
            else:
                cams = caltrans_feed.get_devices()
                last_updated = caltrans_feed.last_update_time
                is_loading = not caltrans_feed.first_update_done
                
            response_data = {
                'last_updated': last_updated,
                'cameras': cams,
                'is_loading': is_loading
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
            
        # API Endpoint: Proxy image requests to bypass CORS/SSL issues
        elif path == '/api/proxy':
            image_url = query.get('url', [None])[0]
            if not image_url:
                self.send_error(400, "Missing 'url' parameter")
                return
                
            try:
                if "youtube.com" in image_url or "youtu.be" in image_url:
                    frame = YoutubeFrameGrabber.grab_frame(image_url)
                    if frame is not None:
                        success, encoded_image = cv2.imencode('.jpg', frame)
                        if success:
                            self.send_response(200)
                            self.send_header('Content-Type', 'image/jpeg')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(encoded_image.tobytes())
                            return
                    self.send_error(500, "Failed to capture frame from YouTube stream")
                else:
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

        # API Endpoint: Run AI analysis (the Intelligence Playground)
        elif path == '/api/analyze':
            feed_type = query.get('feed', ['traffic'])[0]
            img_url = query.get('url', [None])[0]
            prompt = query.get('prompt', ['describe'])[0]
            custom_prompt = query.get('custom_prompt', [None])[0]

            if not img_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Missing 'url' parameter"}).encode('utf-8'))
                return

            try:
                # Call intelligence analyzer
                result = analyzer.analyze(feed_type, img_url, prompt, custom_prompt)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "result": result}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        # API Endpoint: Get analysis logs (also aliased from old /api/surveillance/logs)
        elif path in ('/api/analysis/logs', '/api/surveillance/logs'):
            from agents.camera_analysis_agent import LOG_PATH as ANALYSIS_LOG, log_lock
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            logs = []
            if os.path.exists(ANALYSIS_LOG):
                try:
                    with log_lock:
                        with open(ANALYSIS_LOG, 'r', encoding='utf-8') as f:
                            logs = json.load(f)
                            if not isinstance(logs, list):
                                logs = []
                except Exception as e:
                    print(f"[Server] Error reading analysis log: {e}")

            logs.reverse()  # Latest first
            self.wfile.write(json.dumps({"status": "success", "logs": logs}).encode('utf-8'))
            return
            
        # Fall back to standard static file serving
        return super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == '/api/scavenger/route':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                cameras = body.get('cameras', [])
                findings = scavenger_agent.scan_route_cameras(cameras)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'findings': findings}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # POST /api/analyze_frame — analyze the EXACT frame the browser already fetched.
        # Accepts JSON: { feed, prompt, image_b64 }
        # Passes the pre-fetched base64 bytes directly to Gemini — no re-download, no frame drift.
        elif path == '/api/analyze_frame':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                feed_type = body.get('feed', 'traffic')
                prompt_key = body.get('prompt', 'count')
                img_b64 = body.get('image_b64', '')

                if not img_b64:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'error', 'message': 'Missing image_b64'}).encode('utf-8'))
                    return

                result = analyzer.analyze_b64(feed_type, img_b64, prompt_key)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'result': result}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return

        self.send_error(404)

def start_server():
    print("[Server] Starting server.py...")
    # Wait a moment for initial caltrans fetch to complete
    time.sleep(2)
    
    handler = CameraProxyHandler
    socketserver.TCPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("", PORT), handler) as httpd:
        print(f"[Server] Running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[Server] Shutting down...")

if __name__ == '__main__':
    start_server()
