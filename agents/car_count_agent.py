import threading
import time
import re

def extract_count_summary(feed_type, text):
    if not text:
        return None
    # Strip simulation prefix for parsing
    clean = text.replace('[SIMULATION]', '').strip()
    try:
        if feed_type == 'traffic':
            # Primary: match structured output "Total: N vehicles"
            match = re.search(r'Total:\s*(\d+)\s*vehicles?', clean, re.IGNORECASE)
            if match:
                return f"{match.group(1)} Vehicles"
            # Fallback: sum explicit vehicle category counts
            numbers = re.findall(r'(\d+)\s*(?:car|truck|motorcycle|vehicle)s?', clean, re.IGNORECASE)
            if numbers:
                total = sum(int(n) for n in numbers)
                return f"{total} Vehicles"
            # Last resort: first number after 'approximately'
            match = re.search(r'(?:approximately|count:?)\s*(\d+)', clean, re.IGNORECASE)
            if match:
                return f"{match.group(1)} Vehicles"
        elif feed_type == 'zoo':
            match = re.search(r'(?:animal count|total:|count:?)\s*(\d+)', clean, re.IGNORECASE)
            if match:
                return f"{match.group(1)} Animals"
        
        # Generic fallback
        match = re.search(r'(\d+)', clean)
        if match:
            label = "Vehicles" if feed_type == 'traffic' else "Animals"
            return f"{match.group(1)} {label}"
    except Exception:
        pass
    return "N/A"

class CarCountAgent:
    def __init__(self, caltrans_feed, zoo_feed, analyzer, notifier):
        self.caltrans_feed = caltrans_feed
        self.zoo_feed = zoo_feed
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        print("[CarCountAgent] Started autonomous vehicle/object counting loop.")
        # Wait a few seconds initially
        time.sleep(5)
        
        while self.running:
            try:
                now = time.time()
                # 1. Traffic Feed counting (all cameras)
                devices = self.caltrans_feed.get_devices()
                if devices:
                    for dev in devices:
                        last_analyzed = dev.get('last_analyzed_time', 0)
                        if now - last_analyzed > 300:
                            dev_id = dev['id']
                            img_url = self.caltrans_feed.get_latest_frame(dev_id)
                            if img_url:
                                print(f"[CarCountAgent] Counting vehicles for traffic camera: {dev['name']}")
                                result = self.analyzer.analyze('traffic', img_url, 'count')
                                
                                # Store count in camera metadata
                                dev['latest_count_summary'] = extract_count_summary('traffic', result)
                                dev['latest_count_details'] = result
                                dev['last_analyzed_time'] = now
                                
                                self.notifier.notify(f"📊 Vehicle Count Alert on {dev['name']} ({dev['route']}): {result}")

                # 2. Zoo Feed counting (all active enclosures)
                zoo_devices = self.zoo_feed.get_devices()
                if zoo_devices:
                    for dev in zoo_devices:
                        last_analyzed = dev.get('last_analyzed_time', 0)
                        if now - last_analyzed > 300:
                            dev_id = dev['id']
                            img_url = self.zoo_feed.get_latest_frame(dev_id)
                            if img_url:
                                print(f"[CarCountAgent] Counting animals/objects for zoo camera: {dev['name']}")
                                result = self.analyzer.analyze('zoo', img_url, 'count')
                                
                                # Store count in camera metadata
                                dev['latest_count_summary'] = extract_count_summary('zoo', result)
                                dev['latest_count_details'] = result
                                dev['last_analyzed_time'] = now
                                
                                self.notifier.notify(f"📊 Animal Count Alert on {dev['name']} ({dev['nearby']}): {result}")
            except Exception as e:
                print(f"[CarCountAgent] Error in counting loop: {e}")
            
            # Sleep a short duration to be responsive to new cameras
            time.sleep(10)

