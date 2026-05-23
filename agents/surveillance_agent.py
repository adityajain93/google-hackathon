import os
import json
import time
import asyncio
import threading
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import every, TriggerContext

from inputs.caltrans import CaltransFeed
from inputs.zoo_feed import ZooFeed
from intelligence.analyzer import Analyzer

# Global singletons for tools to reference
caltrans_feed = CaltransFeed()
zoo_feed = ZooFeed()
analyzer = Analyzer()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'intelligence', 'surveillance_config.json')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'outputs', 'surveillance_log.json')

# Lock to make log writes thread-safe
log_lock = threading.Lock()

# =============================================================================
# Agent Custom Tools
# =============================================================================

def get_cameras_to_inspect(feed_type: str) -> str:
    """Retrieves the list of active camera nodes and their current image URLs.

    Args:
        feed_type: The type of feed, either 'traffic' or 'zoo'.
    """
    feed = caltrans_feed if feed_type == 'traffic' else zoo_feed
    devices = feed.get_devices()
    if not devices:
        return "No active cameras found."
    return json.dumps([{"id": d["id"], "name": d["name"], "img_url": d["img_url"]} for d in devices])

def get_surveillance_config() -> str:
    """Loads the surveillance dynamic configuration (target prompts and details) from intelligence/surveillance_config.json.
    """
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
            print(f"[SurveillanceAgentTool] Error reading config: {e}")
    return json.dumps(default_config)

def analyze_camera_frame(feed_type: str, camera_id: str, prompt: str) -> str:
    """Analyzes a specific camera feed using Gemini multimodal analysis.

    Args:
        feed_type: Either 'traffic' or 'zoo'.
        camera_id: The unique identifier of the camera.
        prompt: The surveillance target prompt to check the image against.
    """
    feed = caltrans_feed if feed_type == 'traffic' else zoo_feed
    img_url = feed.get_latest_frame(camera_id)
    if not img_url:
        return f"Error: Could not retrieve latest frame URL for camera {camera_id}."
    
    result = analyzer.analyze(feed_type, img_url, 'custom', prompt)
    return result

def write_to_surveillance_log(camera_id: str, camera_name: str, feed_type: str, prompt_used: str, analysis_result: str) -> str:
    """Writes the camera surveillance analysis results to the shared surveillance log file.

    Args:
        camera_id: Unique ID of the camera.
        camera_name: Friendly name of the camera.
        feed_type: Either 'traffic' or 'zoo'.
        prompt_used: The prompt string used for the inspection.
        analysis_result: The raw text report returned by the camera analysis.
    """
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
# Agent Periodic Trigger Function
# =============================================================================

async def check_feeds(ctx: TriggerContext):
    print("[SurveillanceAgent] Trigger fired. Inspecting camera feeds...")
    await ctx.send(
        "Surveillance Check Cycle: Retrieve the surveillance configuration, fetch all active cameras in 'traffic' and 'zoo' feeds, inspect each camera using analyze_camera_frame with the target details prompt, and write each inspection report to the surveillance log using write_to_surveillance_log."
    )

# =============================================================================
# SurveillanceAgent Class Wrapper
# =============================================================================

class SurveillanceAgent:
    def __init__(self, caltrans_feed, zoo_feed, analyzer, notifier):
        self.caltrans_feed = caltrans_feed
        self.zoo_feed = zoo_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False

    def start(self):
        self.running = True
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_async())
            
        threading.Thread(target=run, daemon=True).start()

    async def _run_async(self):
        timer_trigger = every(60, check_feeds)
        config = LocalAgentConfig(
            system_instructions=(
                "You are an automated camera surveillance agent. Your job is to monitor feeds and log analysis reports. "
                "When triggered, you must perform these steps in order:\n"
                "1. Read the surveillance configuration using get_surveillance_config.\n"
                "2. Fetch the active cameras for 'traffic' and 'zoo' using get_cameras_to_inspect.\n"
                "3. For each camera, run analyze_camera_frame using the correct target prompt from the config.\n"
                "4. Log the result for each camera using write_to_surveillance_log."
            ),
            tools=[get_cameras_to_inspect, get_surveillance_config, analyze_camera_frame, write_to_surveillance_log],
            triggers=[timer_trigger],
        )
        
        async with Agent(config) as agent:
            print("[SurveillanceAgent] Running with Antigravity SDK triggers...")
            while self.running:
                await asyncio.sleep(1)
