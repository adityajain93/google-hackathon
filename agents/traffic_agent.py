import threading
import time

class TrafficAgent:
    def __init__(self, caltrans_feed, analyzer, notifier):
        self.feed = caltrans_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        print("[TrafficAgent] Started autonomous monitoring loop.")
        # Wait a few seconds for the initial feed download to finish
        time.sleep(10)
        
        while self.running:
            try:
                devices = self.feed.get_devices()
                if devices:
                    # Check first 3 major commute cameras periodically
                    target_devices = devices[:3]
                    for dev in target_devices:
                        print(f"[TrafficAgent] Agent autonomously inspecting camera: {dev['name']}")
                        # Analyze for hazards
                        result = self.analyzer.analyze('traffic', dev['img_url'], 'hazard')
                        # Trigger alert if potential issue is detected
                        if any(keyword in result.lower() for keyword in ["hazard", "parked", "shoulder", "closure", "accident", "delay"]):
                            self.notifier.notify(f"🚨 Traffic Alert on {dev['name']} ({dev['route']}): {result}")
            except Exception as e:
                print(f"[TrafficAgent] Error in monitor loop: {e}")
            
            # Check every 5 minutes
            time.sleep(300)
