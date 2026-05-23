import threading
import time

def extract_safety_summary(text):
    if not text:
        return "Checking..."
    
    clean_text = text.replace("[SIMULATION]", "").strip()
    lower_text = clean_text.lower()
    
    if "accident" in lower_text:
        return "Accident"
    if "collision" in lower_text:
        return "Collision"
    if any(k in lower_text for k in ["hazard", "stalled", "parked", "closure", "blockage", "debris", "stopped"]):
        return "Hazard"
    if "safe" in lower_text or "clear" in lower_text or "normal" in lower_text:
        return "Safe"
        
    return "Safe"

class SafetyAgent:
    def __init__(self, caltrans_feed, analyzer, notifier):
        self.feed = caltrans_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        print("[SafetyAgent] Started autonomous safety/collision monitoring loop.")
        # Wait a few seconds initially
        time.sleep(7)
        
        while self.running:
            try:
                now = time.time()
                devices = self.feed.get_devices()
                if devices:
                    for dev in devices:
                        last_analyzed = dev.get('last_safety_analyzed_time', 0)
                        # Check every 5 minutes (300 seconds)
                        if now - last_analyzed > 300:
                            dev_id = dev['id']
                            img_url = self.feed.get_latest_frame(dev_id)
                            if img_url:
                                print(f"[SafetyAgent] Analyzing safety for traffic camera: {dev['name']}")
                                result = self.analyzer.analyze('traffic', img_url, 'safety')
                                
                                # Store safety in camera metadata
                                dev['safety_summary'] = extract_safety_summary(result)
                                dev['safety_details'] = result
                                dev['last_safety_analyzed_time'] = now
                                
                                # Trigger alert if accident/collision/hazard is detected
                                if dev['safety_summary'] in ["Accident", "Collision", "Hazard"]:
                                    self.notifier.notify(f"⚠️ Safety Alert on {dev['name']} ({dev['route']}): {result}")
            except Exception as e:
                print(f"[SafetyAgent] Error in safety loop: {e}")
            
            # Sleep a short duration to check for new/un-analyzed cameras
            time.sleep(10)
