import os
import json
import time
import asyncio
import threading
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import every, TriggerContext

from outputs.notifier import Notifier
from agents.surveillance_agent import LOG_PATH, log_lock

notifier = Notifier()

# =============================================================================
# Agent Custom Tools
# =============================================================================

def read_new_surveillance_logs() -> str:
    """Reads all surveillance logs that have not yet been processed by the alert agent.
    """
    with log_lock:
        if not os.path.exists(LOG_PATH):
            return "[]"
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    return "[]"
                # Filter for unprocessed logs
                unprocessed = [l for l in logs if not l.get("processed", False)]
                return json.dumps(unprocessed)
        except Exception as e:
            return f"Error reading logs: {e}"

def trigger_alert(camera_name: str, reason: str) -> str:
    """Dispatches a safety alert notification to the user / console / webhooks.

    Args:
        camera_name: The name of the camera where the warning/hazard was observed.
        reason: Concise description of the safety alert or anomaly.
    """
    notifier.notify(f"🚨 Surveillance Alert on {camera_name}: {reason}")
    return "Alert notification dispatched."

def mark_log_as_processed(camera_id: str, timestamp: float, alert_triggered: bool, alert_reason: str = "") -> str:
    """Updates the surveillance log marking a specific entry as processed, indicating whether an alert was triggered.

    Args:
        camera_id: The ID of the camera entry to update.
        timestamp: The exact timestamp of the log entry.
        alert_triggered: True if a safety alert was triggered for this entry, otherwise False.
        alert_reason: The reason for the alert, if triggered.
    """
    with log_lock:
        if not os.path.exists(LOG_PATH):
            return "Error: Log file does not exist."
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    return "Error: Invalid log format."
            
            modified = False
            for entry in logs:
                if entry.get("camera_id") == camera_id and abs(entry.get("timestamp", 0) - timestamp) < 0.01:
                    entry["processed"] = True
                    entry["alert_triggered"] = alert_triggered
                    entry["alert_reason"] = alert_reason
                    modified = True
                    break
            
            if modified:
                with open(LOG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2)
                return f"Entry for {camera_id} at {timestamp} successfully marked as processed."
            return f"Error: No matching log entry found for {camera_id} at {timestamp}."
        except Exception as e:
            return f"Error saving processed log: {e}"

# =============================================================================
# Agent Periodic Trigger Function
# =============================================================================

async def review_logs(ctx: TriggerContext):
    print("[AlertAgent] Trigger fired. Scanning surveillance logs for alerts...")
    await ctx.send(
        "Alert Review Cycle: Read the new surveillance logs using read_new_surveillance_logs. "
        "For each unprocessed entry, evaluate if the report contains any safety issue or critical anomaly (e.g. traffic accidents, blockages, animal escapes, or dangerous behavior). "
        "If an issue is found, call trigger_alert to send a notification. Finally, update the entry status using mark_log_as_processed."
    )

# =============================================================================
# AlertAgent Class Wrapper
# =============================================================================

class AlertAgent:
    def __init__(self, analyzer, notifier):
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
        timer_trigger = every(15, review_logs)
        config = LocalAgentConfig(
            system_instructions=(
                "You are a safety alerting supervisor agent. Your job is to scan the surveillance log for new unprocessed reports, "
                "determine if any of the observations warrant a safety alert, notify the user, and mark the logs as processed. "
                "When triggered, you must perform these steps:\n"
                "1. Retrieve new log entries using read_new_surveillance_logs.\n"
                "2. For each entry, evaluate its analysis_result. If it contains details indicating a traffic hazard, vehicle collision, blocked lane, construction delay, high animal activity, splashing, escaping behavior, or abnormal rest/climbing, decide to raise an alert.\n"
                "3. If an alert is raised, trigger the notification using trigger_alert.\n"
                "4. Mark the log entry as processed using mark_log_as_processed, specifying whether you triggered an alert and the alert reason."
            ),
            tools=[read_new_surveillance_logs, trigger_alert, mark_log_as_processed],
            triggers=[timer_trigger],
        )
        
        async with Agent(config) as agent:
            print("[AlertAgent] Running with Antigravity SDK triggers...")
            while self.running:
                await asyncio.sleep(1)
