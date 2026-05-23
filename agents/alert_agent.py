"""
AlertAgent — downstream reasoning agent that reads the analysis_log.json written by
CameraAnalysisAgent, uses Gemini text reasoning to decide if an alert is warranted,
and dispatches notifications via Notifier.
"""

import os
import json
import time
import asyncio
import threading
import re

from outputs.notifier import Notifier
from agents.camera_analysis_agent import LOG_PATH, log_lock, append_to_log
from intelligence.analyzer import Analyzer

# =============================================================================
# Helpers
# =============================================================================

def read_unprocessed_logs() -> list:
    """Thread-safe read of unprocessed analysis log entries."""
    with log_lock:
        if not os.path.exists(LOG_PATH):
            return []
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if not isinstance(logs, list):
                    return []
                return [l for l in logs if not l.get("processed", False)]
        except Exception as e:
            print(f"[AlertAgent] Error reading log: {e}")
            return []


def mark_processed(camera_id: str, timestamp: float, alert_triggered: bool, alert_reason: str = ""):
    """Thread-safe update of a specific log entry to mark it processed."""
    with log_lock:
        if not os.path.exists(LOG_PATH):
            return
        try:
            with open(LOG_PATH, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            if not isinstance(logs, list):
                return

            for entry in logs:
                if entry.get("camera_id") == camera_id and abs(entry.get("timestamp", 0) - timestamp) < 0.01:
                    entry["processed"] = True
                    entry["alert_triggered"] = alert_triggered
                    entry["alert_reason"] = alert_reason
                    break

            with open(LOG_PATH, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"[AlertAgent] Error marking entry processed: {e}")


# =============================================================================
# Core alert review task
# =============================================================================

async def _process_entry(entry: dict, analyzer: Analyzer, notifier: Notifier):
    """Evaluate one log entry and dispatch an alert if warranted."""
    result = entry.get("result", {})
    camera_name = entry.get("camera_name", "Unknown")
    camera_id = entry.get("camera_id")
    timestamp = entry.get("timestamp", 0)
    feed_type = entry.get("feed_type", "traffic")

    safety_status = result.get("safety_status", "Safe")
    safety_detail = result.get("safety_detail", "")
    surveillance_notes = result.get("surveillance_notes", "")

    # Fun-moment fast-path for zoo cameras — nudge without a second Gemini call
    if feed_type == "zoo" and result.get("fun_moment", False):
        fun_desc = result.get("fun_description", "Something fun is happening!")
        notifier.notify(f"🐼 Fun moment at {camera_name}: {fun_desc} Come check it out!")
        mark_processed(camera_id, timestamp, True, fun_desc)
        return

    # Fast-path: skip clearly safe entries without making a Gemini call
    is_clearly_safe = (
        safety_status in ("Safe",)
        and "nothing to flag" in surveillance_notes.lower()
    )
    if is_clearly_safe:
        mark_processed(camera_id, timestamp, False, "")
        return

    # Build reasoning prompt for Gemini
    prompt = f"""You are a surveillance supervisor reviewing an automated camera analysis report.
Determine if this warrants an immediate alert notification.

Camera: {camera_name} ({feed_type})
Safety Status: {safety_status}
Safety Detail: {safety_detail}
Surveillance Notes: {surveillance_notes}

Criteria for raising an alert:
- Traffic: Accident, Collision, active Hazard (stalled vehicle, debris, lane blockage)
- Zoo: Animal distress, escape behavior, injury, aggression
- NOT an alert: normal traffic, animals resting/feeding, routine activity

Respond ONLY with a valid JSON object:
{{"raise_alert": true, "alert_reason": "Short description of what was observed"}}
or
{{"raise_alert": false, "alert_reason": ""}}"""

    # Simulation fallback: use safety_status directly
    sim_alert = safety_status in ("Accident", "Collision", "Hazard", "Concern", "Emergency")
    sim_reason = f"{safety_status}: {safety_detail}" if sim_alert else ""
    mock_fallback = f'{{"raise_alert": {str(sim_alert).lower()}, "alert_reason": "{sim_reason}"}}'

    print(f"[AlertAgent] Evaluating: {camera_name} (status={safety_status})...")
    decision_raw = await analyzer.analyze_text_async(prompt, mock_fallback_response=mock_fallback)

    # Parse decision
    raise_alert = False
    alert_reason = ""
    try:
        clean = re.sub(r'^```json\s*|\s*```$', '', decision_raw.strip(), flags=re.MULTILINE)
        m = re.search(r'\{.*\}', clean, re.DOTALL)
        if m:
            clean = m.group(0)
        decision = json.loads(clean)
        raise_alert = bool(decision.get("raise_alert", False))
        alert_reason = decision.get("alert_reason", "")
    except Exception as e:
        print(f"[AlertAgent] JSON parse error: {e}. Raw: {decision_raw[:200]}")
        raise_alert = sim_alert
        alert_reason = sim_reason

    if raise_alert and alert_reason:
        notifier.notify(f"🚨 Alert — {camera_name}: {alert_reason}")
        mark_processed(camera_id, timestamp, True, alert_reason)
    else:
        mark_processed(camera_id, timestamp, False, "")
        print(f"[AlertAgent] No alert for {camera_name}.")


GEMINI_PARALLEL_CALLS = 30  # Max concurrent Gemini text reasoning calls

async def review_logs(analyzer: Analyzer, notifier: Notifier):
    """Scan unprocessed entries and raise alerts via Gemini reasoning."""
    entries = read_unprocessed_logs()
    if not entries:
        return

    print(f"[AlertAgent] Reviewing {len(entries)} unprocessed entries ({GEMINI_PARALLEL_CALLS} parallel)...")

    sem = asyncio.Semaphore(GEMINI_PARALLEL_CALLS)

    async def process_with_sem(entry):
        async with sem:
            await _process_entry(entry, analyzer, notifier)

    await asyncio.gather(*[process_with_sem(e) for e in entries], return_exceptions=True)


# =============================================================================
# AlertAgent class
# =============================================================================

class AlertAgent:
    """Background alert agent that reads analysis_log.json produced by CameraAnalysisAgent
    and uses Gemini text reasoning to decide on and dispatch alert notifications.
    """

    POLL_INTERVAL_SECONDS = 15

    def __init__(self, analyzer: Analyzer, notifier: Notifier):
        self.analyzer = analyzer
        self.notifier = notifier
        self.running = False
        self._thread = None

    def start(self):
        if self.running:
            print("[AlertAgent] Already running.")
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, name="AlertAgent", daemon=True)
        self._thread.start()
        print("[AlertAgent] Started background alert agent.")

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
        print(f"[AlertAgent] Agent loop started. Polling every {self.POLL_INTERVAL_SECONDS}s.")
        await asyncio.sleep(10)  # Wait for first analysis results
        while self.running:
            try:
                await review_logs(self.analyzer, self.notifier)
            except Exception as e:
                print(f"[AlertAgent] Unhandled error: {e}")
            await asyncio.sleep(self.POLL_INTERVAL_SECONDS)
