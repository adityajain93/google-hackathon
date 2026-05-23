import os
import json
import time
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.surveillance_agent import (
    get_cameras_to_inspect,
    get_surveillance_config,
    analyze_camera_frame,
    write_to_surveillance_log,
    LOG_PATH
)
from agents.alert_agent import (
    read_new_surveillance_logs,
    trigger_alert,
    mark_log_as_processed
)

def run_tests():
    print("[TEST] Running validation for Google Antigravity SDK Agent Tools...")
    
    # 1. Test get_surveillance_config
    print("\n[TEST 1] Loading surveillance config...")
    cfg_str = get_surveillance_config()
    cfg = json.loads(cfg_str)
    assert "traffic" in cfg, "Config should contain traffic settings"
    assert "zoo" in cfg, "Config should contain zoo settings"
    print("Success: Config is valid JSON and contains target settings.")

    # 2. Test get_cameras_to_inspect
    print("\n[TEST 2] Retrieving cameras for zoo feed...")
    cameras_str = get_cameras_to_inspect("zoo")
    cameras = json.loads(cameras_str)
    assert len(cameras) > 0, "Zoo feed should return at least one camera"
    print(f"Success: Retrieved {len(cameras)} cameras from zoo feed.")

    # 3. Test write_to_surveillance_log
    print("\n[TEST 3] Writing a mock entry to surveillance log...")
    # Clean old logs for testing if exist
    if os.path.exists(LOG_PATH):
        try:
            os.remove(LOG_PATH)
        except Exception:
            pass
            
    res = write_to_surveillance_log(
        camera_id="test_cam",
        camera_name="Test Chamber",
        feed_type="zoo",
        prompt_used="Observe animal behavior",
        analysis_result="[SIMULATION] The penguin is escaping from the enclosure, running towards the exit!"
    )
    print(f"Log write result: {res}")
    assert os.path.exists(LOG_PATH), "Log file should have been created"
    print("Success: Mock log entry successfully written.")

    # 4. Test read_new_surveillance_logs
    print("\n[TEST 4] Reading unprocessed logs...")
    unprocessed_str = read_new_surveillance_logs()
    unprocessed = json.loads(unprocessed_str)
    assert len(unprocessed) == 1, "Should retrieve 1 unprocessed entry"
    entry = unprocessed[0]
    assert entry["camera_id"] == "test_cam", "Camera ID should match"
    print("Success: Unprocessed logs successfully retrieved.")

    # 5. Test trigger_alert
    print("\n[TEST 5] Testing alert dispatcher...")
    alert_res = trigger_alert(entry["camera_name"], "Test warning: Animal is escaping!")
    print(f"Alert result: {alert_res}")
    print("Success: Notification alert successfully dispatched.")

    # 6. Test mark_log_as_processed
    print("\n[TEST 6] Marking entry as processed...")
    mark_res = mark_log_as_processed(
        camera_id=entry["camera_id"],
        timestamp=entry["timestamp"],
        alert_triggered=True,
        alert_reason="Animal is escaping!"
    )
    print(f"Mark result: {mark_res}")
    
    # Read logs again to verify processed status
    unprocessed_str_after = read_new_surveillance_logs()
    unprocessed_after = json.loads(unprocessed_str_after)
    assert len(unprocessed_after) == 0, "Unprocessed logs list should now be empty"
    print("Success: Log entry successfully marked as processed.")

    print("\n[TEST] All SDK agent tool checks PASSED successfully!")

if __name__ == "__main__":
    run_tests()
