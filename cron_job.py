import os
import sys
import time
from inputs.caltrans import CaltransFeed
from inputs.zoo_feed import ZooFeed
from intelligence.analyzer import Analyzer
from outputs.notifier import Notifier
from agents.car_count_agent import extract_count_summary

# Load environment variables
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(DIRECTORY, '.env')
if os.path.exists(env_path):
    print(f"[CronJob] Loading environment from {env_path}")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

def main():
    print("[CronJob] Starting vehicle/object counting cron execution...")
    caltrans_feed = CaltransFeed()
    zoo_feed = ZooFeed()
    analyzer = Analyzer()
    notifier = Notifier()

    # Wait for Caltrans feed to fetch and verify at least some cameras
    print("[CronJob] Waiting for Caltrans feed to fetch active cameras...")
    start_time = time.time()
    devices = []
    while time.time() - start_time < 20:
        devices = caltrans_feed.get_devices()
        if devices:
            break
        time.sleep(1)

    if not devices:
        print("[CronJob] Warning: No active Caltrans cameras found (timed out waiting for feed update).")
    else:
        print(f"[CronJob] Found {len(devices)} active Caltrans cameras.")

    # 1. Traffic Feed counting (all cameras)
    if devices:
        for dev in devices:
            dev_id = dev['id']
            img_url = caltrans_feed.get_latest_frame(dev_id)
            if img_url:
                print(f"[CronJob] Counting vehicles for traffic camera: {dev['name']}")
                result = analyzer.analyze('traffic', img_url, 'count')
                
                # Store count in camera metadata
                dev['latest_count_summary'] = extract_count_summary('traffic', result)
                dev['latest_count_details'] = result
                
                notifier.notify(f"📊 [CronJob] Vehicle Count on {dev['name']} ({dev['route']}): {result}")

    # 2. Zoo Feed counting (all active enclosures)
    zoo_devices = zoo_feed.get_devices()
    if zoo_devices:
        for dev in zoo_devices:
            dev_id = dev['id']
            img_url = zoo_feed.get_latest_frame(dev_id)
            if img_url:
                print(f"[CronJob] Counting animals/objects for zoo camera: {dev['name']}")
                result = analyzer.analyze('zoo', img_url, 'count')
                
                # Store count in camera metadata
                dev['latest_count_summary'] = extract_count_summary('zoo', result)
                dev['latest_count_details'] = result
                
                notifier.notify(f"📊 [CronJob] Animal Count on {dev['name']} ({dev['nearby']}): {result}")

    print("[CronJob] Cron execution complete.")

if __name__ == '__main__':
    main()

