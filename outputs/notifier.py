import os
import json
import urllib.request

class Notifier:
    def __init__(self):
        # Optional Slack/Discord webhook URL from environment
        self.webhook_url = os.environ.get('NOTIFICATION_WEBHOOK_URL', '')

    def notify(self, message):
        """Dispatches an alert to log console and webhook."""
        # 1. Console Log Alert
        print(f"\n[Notifier Alert] {message}\n")
        
        # 2. Webhook Dispatch (optional)
        if self.webhook_url:
            try:
                payload = {"text": message}
                req = urllib.request.Request(
                    self.webhook_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    pass
                print("[Notifier] Webhook notification sent successfully.")
            except Exception as e:
                print(f"[Notifier] Failed to send webhook alert: {e}")
