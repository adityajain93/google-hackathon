import json

ROUTE_PROMPT = (
    "You are previewing a California highway traffic camera for a driver who will pass this location soon. "
    "Look for anything worth flagging — construction, congestion, fog, a stalled vehicle, an unusual load, "
    "an animal on the road, something quirky or unexpected, or anything a driver would want a heads-up about.\n\n"
    "Respond in this exact format: [CATEGORY] one short sentence, max 15 words.\n"
    "CATEGORY must be one of: CONGESTION, CONSTRUCTION, WEATHER, HAZARD, QUIRKY, or ALL_CLEAR.\n"
    "Use QUIRKY for anything fun or unexpected that isn't a safety hazard.\n"
    "Examples:\n"
    "  [CONGESTION] Heavy stop-and-go traffic backed up across all lanes.\n"
    "  [CONSTRUCTION] Lane closure ahead with cones and workers on the right shoulder.\n"
    "  [WEATHER] Dense fog reducing visibility to under a quarter mile.\n"
    "  [HAZARD] Stalled vehicle on the right shoulder with hazard lights on.\n"
    "  [QUIRKY] Oversized load shaped like a rocket taking up two lanes.\n"
    "  [ALL_CLEAR]\n"
    "If everything looks completely normal, respond with only: [ALL_CLEAR]"
)

CATEGORY_EMOJI = {
    "CONGESTION":   "🚗",
    "CONSTRUCTION": "🚧",
    "WEATHER":      "🌫️",
    "HAZARD":       "🚨",
    "QUIRKY":       "✨",
}


class ScavengerAgent:
    def __init__(self, caltrans_feed, gemini_client):
        self.feed = caltrans_feed
        self.gemini = gemini_client

    def scan_route_cameras(self, cameras):
        """Scan a list of cameras along a route. Returns only notable findings."""
        print(f"[ScavengerAgent] Scanning {len(cameras)} cameras along route:")
        for c in cameras:
            print(f"  → {c.get('name')} | {c.get('img_url')}")

        findings = []
        for cam in cameras:
            try:
                print(f"[ScavengerAgent] Asking Gemini about: {cam.get('name')}")
                raw = self.gemini.analyze_image(cam["img_url"], ROUTE_PROMPT).strip()
                print(f"[ScavengerAgent] Gemini: {raw}")
                if raw.upper().startswith("[ALL_CLEAR]") or "ALL_CLEAR" in raw.upper():
                    continue

                category, observation = self._parse_response(raw)
                if not observation:
                    continue

                findings.append({
                    "name":        cam.get("name", ""),
                    "location":    cam.get("nearby") or cam.get("name", ""),
                    "route":       cam.get("route", ""),
                    "img_url":     cam.get("img_url", ""),
                    "category":    category,
                    "emoji":       CATEGORY_EMOJI.get(category, "📍"),
                    "observation": observation,
                })
            except Exception as e:
                print(f"[ScavengerAgent] Error on {cam.get('name', '?')}: {e}")

        return findings

    def _parse_response(self, raw):
        """Extract [CATEGORY] and observation text from Gemini response."""
        if raw.startswith("["):
            end = raw.find("]")
            if end > 0:
                category = raw[1:end].strip().upper()
                observation = raw[end + 1:].strip()
                return category, observation
        return "HAZARD", raw
