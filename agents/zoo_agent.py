import threading
import time

class ZooAgent:
    def __init__(self, zoo_feed, analyzer, notifier):
        self.feed = zoo_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        print("[ZooAgent] Started autonomous zoo monitoring loop.")
        # Wait a few seconds
        time.sleep(10)
        
        while self.running:
            try:
                devices = self.feed.get_devices()
                if devices:
                    # Check all zoo cameras
                    for dev in devices:
                        print(f"[ZooAgent] Agent autonomously inspecting camera: {dev['name']}")
                        # Analyze activity levels (mapped to 'hazard' prompt which evaluates behavior)
                        result = self.analyzer.analyze('zoo', dev['img_url'], 'hazard')
                        # Trigger alert if high activity or playing is detected
                        if any(keyword in result.lower() for keyword in ["high", "play", "splashing", "running", "active"]):
                            self.notifier.notify(f"🐼 Animal Activity Alert on {dev['name']} ({dev['nearby']}): {result}")
            except Exception as e:
                print(f"[ZooAgent] Error in zoo monitor loop: {e}")
            
            # Check every 5 minutes
            time.sleep(300)
