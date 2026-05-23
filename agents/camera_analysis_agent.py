"""
CameraAnalysisAgent — unified background agent replacing:
  - TrafficAgent (hazard checks)
  - ZooAgent (activity monitoring)
  - CarCountAgent (vehicle/animal counting)
  - SafetyAgent (safety status)
  - SurveillanceAgent (custom prompt surveillance)

Makes ONE structured Gemini call per camera per cycle, populates:
  1. Camera device metadata (dev['safety_summary'], dev['latest_count_summary']) → UI badges
  2. outputs/analysis_log.json → AlertAgent reads this for notification decisions
"""

import os
import json
import time
import asyncio
import threading

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'intelligence', 'surveillance_config.json')
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'outputs', 'analysis_log.json')

# Shared lock for log file access (used by AlertAgent too)
log_lock = threading.Lock()

# Default surveillance targets (used if config file missing)
DEFAULT_CONFIG = {
    "traffic": {
        "surveillance_target": "Look for accidents, lane blockages, stalled vehicles, emergency response vehicles, road construction, debris, or heavy traffic jams.",
        "check_interval_seconds": 300
    },
    "zoo": {
        "surveillance_target": "Observe animal welfare and activity. Flag any escaping behavior, distress, injury, aggression, or unusually high excitement.",
        "check_interval_seconds": 300
    }
}


def load_config() -> dict:
    """Load surveillance config, falling back to defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[CameraAnalysisAgent] Error reading config: {e}")
    return DEFAULT_CONFIG


def append_to_log(entry: dict):
    """Thread-safe append to the analysis log file (capped at 200 entries)."""
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
        if len(logs) > 200:
            logs = logs[-200:]

        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[CameraAnalysisAgent] Error writing log: {e}")


GEMINI_PARALLEL_CALLS = 30  # Max concurrent Gemini image analysis calls

class CameraAnalysisAgent:
    """Unified background agent: one structured Gemini call per camera, populating
    both UI badge metadata and the analysis log for downstream alert processing.
    """

    LOOP_POLL_SECONDS = 10  # Tight loop to catch newly-added cameras quickly

    def __init__(self, caltrans_feed, zoo_feed, analyzer, notifier):
        self.caltrans_feed = caltrans_feed
        self.zoo_feed = zoo_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False
        self._thread = None
        self._last_analyzed: dict[str, float] = {}  # camera_id → timestamp

    def start(self):
        if self.running:
            print("[CameraAnalysisAgent] Already running.")
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, name="CameraAnalysisAgent", daemon=True)
        self._thread.start()
        print("[CameraAnalysisAgent] Started unified camera analysis agent.")

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
        print(f"[CameraAnalysisAgent] Agent loop started. Checking cameras every {self.LOOP_POLL_SECONDS}s.")
        await asyncio.sleep(5)

        sem = asyncio.Semaphore(GEMINI_PARALLEL_CALLS)

        async def _analyze_with_sem(dev, feed_type, target, now):
            async with sem:
                await self._analyze_camera(dev, feed_type, target, now)

        while self.running:
            try:
                config = load_config()
                now = time.time()

                # --- Traffic cameras ---
                traffic_cfg = config.get("traffic", DEFAULT_CONFIG["traffic"])
                traffic_target = traffic_cfg.get("surveillance_target", DEFAULT_CONFIG["traffic"]["surveillance_target"])
                traffic_interval = traffic_cfg.get("check_interval_seconds", 300)

                traffic_devices = self.caltrans_feed.get_devices() or []
                due_traffic = [
                    dev for dev in traffic_devices
                    if now - self._last_analyzed.get(dev["id"], 0) >= traffic_interval
                ]

                # --- Zoo cameras ---
                zoo_cfg = config.get("zoo", DEFAULT_CONFIG["zoo"])
                zoo_target = zoo_cfg.get("surveillance_target", DEFAULT_CONFIG["zoo"]["surveillance_target"])
                zoo_interval = zoo_cfg.get("check_interval_seconds", 300)

                zoo_devices = self.zoo_feed.get_devices() or []
                due_zoo = [
                    dev for dev in zoo_devices
                    if now - self._last_analyzed.get(dev["id"], 0) >= zoo_interval
                ]

                # Run all due cameras in parallel (capped at 5 concurrent)
                tasks = (
                    [_analyze_with_sem(dev, "traffic", traffic_target, now) for dev in due_traffic]
                    + [_analyze_with_sem(dev, "zoo", zoo_target, now) for dev in due_zoo]
                )
                if tasks:
                    print(f"[CameraAnalysisAgent] Launching {len(tasks)} camera analyses (≤{GEMINI_PARALLEL_CALLS} parallel).")
                    await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                print(f"[CameraAnalysisAgent] Unhandled error in loop: {e}")

            await asyncio.sleep(self.LOOP_POLL_SECONDS)

    async def _analyze_camera(self, dev: dict, feed_type: str, surveillance_target: str, now: float):
        """Run one structured analysis for a single camera and update all downstream outputs."""
        dev_id = dev["id"]
        dev_name = dev.get("name", dev_id)

        img_url = (
            self.caltrans_feed.get_latest_frame(dev_id)
            if feed_type == "traffic"
            else self.zoo_feed.get_latest_frame(dev_id)
        )
        if not img_url:
            return

        print(f"[CameraAnalysisAgent] Analyzing {feed_type} camera: {dev_name}")

        try:
            result = await self.analyzer.analyze_structured_async(feed_type, img_url, surveillance_target)
        except Exception as e:
            print(f"[CameraAnalysisAgent] Analysis failed for {dev_name}: {e}")
            return

        self._last_analyzed[dev_id] = now

        # --- 1. Update camera device metadata for UI badges ---
        safety_status = result.get("safety_status", "Safe")
        dev["safety_summary"] = safety_status
        dev["safety_details"] = result.get("safety_detail", "")
        dev["latest_count_summary"] = result.get("count_summary", result.get("count_summary", "N/A"))
        dev["latest_count_details"] = json.dumps(result)
        dev["last_analyzed_time"] = now
        dev["fun_moment"] = result.get("fun_moment", False)
        dev["fun_description"] = result.get("fun_description", "")

        # --- 2. Write to analysis log for AlertAgent ---
        log_entry = {
            "timestamp": now,
            "feed_type": feed_type,
            "camera_id": dev_id,
            "camera_name": dev_name,
            "surveillance_target": surveillance_target,
            "result": result,
            "processed": False
        }
        append_to_log(log_entry)
