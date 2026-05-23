import os
import json
import time
import asyncio
import threading
from intelligence.analyzer import Analyzer
from inputs.caltrans import CaltransFeed
from inputs.zoo_feed import ZooFeed

# Global singletons for tools to reference
caltrans_feed = CaltransFeed()
zoo_feed = ZooFeed()
analyzer = Analyzer()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'intelligence', 'surveillance_config.json')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'outputs', 'surveillance_log.json')

# Lock to make log writes thread-safe
log_lock = threading.Lock()
last_analyzed = {}

# =============================================================================
# Agent Tools (reusable functions)
# =============================================================================

def get_cameras_to_inspect(feed_type: str) -> str:
    """Retrieves the list of active camera nodes and their current image URLs."""
    feed = caltrans_feed if feed_type == 'traffic' else zoo_feed
    devices = feed.get_devices()
    if not devices:
        return "No active cameras found."
    return json.dumps([{"id": d["id"], "name": d["name"], "img_url": d["img_url"]} for d in devices])

def get_surveillance_config() -> str:
    """Loads the surveillance dynamic configuration from intelligence/surveillance_config.json."""
    default_config = {
        "traffic": {
            "target_details": "Inspect for accidents, lane blockages, stalled vehicles, emergency response vehicles, road construction, hazards, or heavy traffic jams.",
            "check_interval_seconds": 60
        },
        "zoo": {
            "target_details": "Observe animal activities. Look for any active play, running, escaping behaviors, abnormal resting positions, distress, or physical interaction.",
            "check_interval_seconds": 60
        }
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[SurveillanceAgent] Error reading config: {e}")
    return json.dumps(default_config)

def analyze_camera_frame(feed_type: str, camera_id: str, prompt: str) -> str:
    """Analyzes a specific camera feed using Gemini multimodal analysis."""
    feed = caltrans_feed if feed_type == 'traffic' else zoo_feed
    img_url = feed.get_latest_frame(camera_id)
    if not img_url:
        return f"Error: Could not retrieve latest frame URL for camera {camera_id}."
    result = analyzer.analyze(feed_type, img_url, 'custom', prompt)
    return result

def write_to_surveillance_log(camera_id: str, camera_name: str, feed_type: str, prompt_used: str, analysis_result: str) -> str:
    """Writes the camera surveillance analysis results to the shared surveillance log file."""
    entry = {
        "timestamp": time.time(),
        "feed_type": feed_type,
        "camera_id": camera_id,
        "camera_name": camera_name,
        "prompt_used": prompt_used,
        "analysis_result": analysis_result,
        "processed": False
    }

    with log_lock:
        logs = []
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []

        logs.append(entry)

        # Keep only latest 100 entries
        if len(logs) > 100:
            logs = logs[-100:]

        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
            return "Successfully written to surveillance log."
        except Exception as e:
            return f"Error writing log: {e}"

# =============================================================================
# Core Surveillance Task (called periodically)
# =============================================================================

async def check_feeds():
    """Run one full cycle of surveillance across all cameras."""
    print("[SurveillanceAgent] Running surveillance cycle...")
    try:
        config_str = get_surveillance_config()
        config = json.loads(config_str)
        now = time.time()

        # 1. Process Traffic Feed
        traffic_cfg = config.get("traffic", {})
        traffic_prompt = traffic_cfg.get("target_details", "")
        traffic_interval = traffic_cfg.get("check_interval_seconds", 60)

        devices_str = get_cameras_to_inspect("traffic")
        try:
            devices = json.loads(devices_str)
        except Exception:
            devices = []

        for dev in devices:
            dev_id = dev["id"]
            last_time = last_analyzed.get(dev_id, 0)
            if now - last_time >= traffic_interval:
                print(f"[SurveillanceAgent] Analyzing traffic camera: {dev['name']}")
                analysis = analyze_camera_frame("traffic", dev_id, traffic_prompt)
                write_to_surveillance_log(dev_id, dev["name"], "traffic", traffic_prompt, analysis)
                last_analyzed[dev_id] = now

        # 2. Process Zoo Feed
        zoo_cfg = config.get("zoo", {})
        zoo_prompt = zoo_cfg.get("target_details", "")
        zoo_interval = zoo_cfg.get("check_interval_seconds", 60)

        zoo_devices_str = get_cameras_to_inspect("zoo")
        try:
            zoo_devices = json.loads(zoo_devices_str)
        except Exception:
            zoo_devices = []

        for dev in zoo_devices:
            dev_id = dev["id"]
            last_time = last_analyzed.get(dev_id, 0)
            if now - last_time >= zoo_interval:
                print(f"[SurveillanceAgent] Analyzing zoo camera: {dev['name']}")
                analysis = analyze_camera_frame("zoo", dev_id, zoo_prompt)
                write_to_surveillance_log(dev_id, dev["name"], "zoo", zoo_prompt, analysis)
                last_analyzed[dev_id] = now

    except Exception as e:
        print(f"[SurveillanceAgent] Error during surveillance cycle: {e}")


# =============================================================================
# SurveillanceAgent Class
# =============================================================================

class SurveillanceAgent:
    """Background surveillance agent that periodically scans all camera feeds
    using Gemini multimodal analysis and writes results to the surveillance log.
    
    Uses a direct asyncio event loop (no external SDK wrapper) for maximum
    stability when embedded in a long-running server process.
    """

    POLL_INTERVAL_SECONDS = 30  # How often to check (config may gate individual cameras)

    def __init__(self, caltrans_feed_ref, zoo_feed_ref, analyzer_ref, notifier_ref):
        self.running = False
        self._thread = None

    def start(self):
        """Start the agent in a background daemon thread."""
        if self.running:
            print("[SurveillanceAgent] Already running.")
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, name="SurveillanceAgent", daemon=True)
        self._thread.start()
        print("[SurveillanceAgent] Started background surveillance agent.")

    def stop(self):
        self.running = False

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._loop())
        finally:
            loop.close()

    async def _loop(self):
        print(f"[SurveillanceAgent] Agent loop started. Polling every {self.POLL_INTERVAL_SECONDS}s.")
        while self.running:
            try:
                await check_feeds()
            except Exception as e:
                print(f"[SurveillanceAgent] Unhandled error in loop: {e}")
            # Wait before next cycle
            await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
