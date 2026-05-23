import threading
import time
import urllib.request
import json

def aqi_to_summary(aqi):
    """Convert US AQI index value to human-readable label."""
    if aqi is None:
        return None, None
    aqi = int(aqi)
    if aqi <= 50:
        return "Good", "aqi-good"
    elif aqi <= 100:
        return "Moderate", "aqi-moderate"
    elif aqi <= 150:
        return "Unhealthy*", "aqi-sensitive"
    elif aqi <= 200:
        return "Unhealthy", "aqi-unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy", "aqi-very-unhealthy"
    else:
        return "Hazardous", "aqi-hazardous"


def fetch_aqi(lat, lon):
    """
    Fetch US AQI using the Open-Meteo Air Quality API (free, no key needed).
    Returns integer AQI or None on failure.
    """
    try:
        url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=us_aqi&timezone=auto&forecast_days=1"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Get the most recent non-null AQI from the hourly array
        hourly = data.get("hourly", {})
        aqis = hourly.get("us_aqi", [])
        # Walk backwards to find the latest valid reading
        for val in reversed(aqis):
            if val is not None:
                return val
    except Exception as e:
        print(f"[AirQualityAgent] AQI fetch failed for ({lat}, {lon}): {e}")
    return None


class AirQualityAgent:
    def __init__(self, caltrans_feed):
        self.feed = caltrans_feed
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        print("[AirQualityAgent] Started air quality monitoring loop.")
        # Stagger start so other agents settle first
        time.sleep(12)

        while self.running:
            try:
                now = time.time()
                devices = self.feed.get_devices()
                if devices:
                    for dev in devices:
                        last_checked = dev.get("last_aqi_checked_time", 0)
                        # Refresh every 30 minutes (AQI doesn't change rapidly)
                        if now - last_checked > 1800:
                            lat = dev.get("latitude", 0)
                            lon = dev.get("longitude", 0)
                            if lat and lon:
                                aqi_val = fetch_aqi(lat, lon)
                                summary, css_class = aqi_to_summary(aqi_val)
                                dev["air_quality_aqi"] = aqi_val
                                dev["air_quality_summary"] = summary
                                dev["air_quality_css_class"] = css_class
                                dev["last_aqi_checked_time"] = now
                                print(
                                    f"[AirQualityAgent] {dev['name']}: AQI={aqi_val} ({summary})"
                                )
            except Exception as e:
                print(f"[AirQualityAgent] Error in loop: {e}")

            # Check for cameras that haven't been refreshed every 30s
            time.sleep(30)
