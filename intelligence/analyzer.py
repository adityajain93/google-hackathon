import random
import json
import asyncio
from intelligence.gemini_client import GeminiClient

class Analyzer:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def analyze(self, feed_type, img_url, prompt_key, custom_prompt=None):
        """
        Analyzes a camera frame based on the feed type and selected prompt.
        If GEMINI_API_KEY is missing or fails, falls back to realistic mock responses.
        """
        # Formulate the prompt to send to Gemini
        prompt = self._get_prompt_string(feed_type, prompt_key, custom_prompt)
        
        # Try to use Gemini
        if self.gemini_client.api_key:
            try:
                print(f"[Analyzer] Running Gemini analysis on {img_url} with prompt: {prompt[:40]}...")
                return self.gemini_client.analyze_image(img_url, prompt)
            except Exception as e:
                print(f"[Analyzer] Gemini analysis failed ({e}). Falling back to simulation mode...")
                # Fall through to mock logic below if API fails
        
        # Mock Simulation Fallback
        return self._generate_mock_response(feed_type, prompt_key, custom_prompt)

    def _get_prompt_string(self, feed_type, prompt_key, custom_prompt):
        if prompt_key == 'custom' and custom_prompt:
            return custom_prompt

        presets = {
            'traffic': {
                'describe': "Describe the current traffic conditions, flow, and weather visibility in this traffic camera frame. Keep it concise.",
                'count': "Count the approximate number of vehicles (cars, trucks, motorcycles) visible in this image. Give a clear count.",
                'hazard': "Look closely at the highway lane. Check if there are any accidents, stalled vehicles, debris, construction, or hazards. Report what you find.",
                'safety': "Analyze this traffic camera frame. Check if there is a collision, accident, vehicle breakdown, lane blockage, or hazard in that area. If there is, output 'ACCIDENT ALERT', 'COLLISION ALERT' or 'HAZARD ALERT' followed by a very brief explanation (e.g., 'COLLISION ALERT: minor crash on left lane'). If the roadway/intersection looks clear and traffic is flowing normally, output 'SAFE' followed by a brief explanation (e.g., 'SAFE: clear traffic'). Keep your response under 10 words."
            },
            'zoo': {
                'describe': "Identify the animals visible in this zoo camera frame and describe what they are doing. Keep it concise and engaging.",
                'count': "Count how many animals are visible in the enclosure. Mention if any are hiding.",
                'hazard': "Assess the activity level of the animals. Are they active, sleeping, eating, or playing? Describe their behavior.",
                'safety': "Assess the safety of the animals in the enclosure. Verify that no visible hazards, debris, or anomalies exist. Respond with 'SAFE: all normal' or a brief warning if anything looks unsafe."
            }
        }
        
        feed_presets = presets.get(feed_type, presets['traffic'])
        return feed_presets.get(prompt_key, "Analyze this image and describe what you see.")

    def _generate_mock_response(self, feed_type, prompt_key, custom_prompt):
        """Generates realistic-looking mock reports for offline/fallback testing."""
        if prompt_key == 'custom':
            return f"[SIMULATION] Answer to custom prompt '{custom_prompt}': Looking at the simulated camera frame, everything looks normal. The primary subject is clearly visible, with clear lighting and no major interruptions in the field of view."

        if feed_type == 'traffic':
            if prompt_key == 'describe':
                conditions = [
                    "Traffic is flowing smoothly at normal highway speeds (~65 mph). Clear visibility and dry roads.",
                    "Moderate congestion observed. Vehicles are slowing down with brake lights active. Estimated speeds around 35-40 mph.",
                    "Heavy stop-and-go traffic detected. Vehicles are bumper-to-bumper. Visibility is slightly reduced due to overcast skies.",
                    "Light traffic observed. Main lanes are mostly clear with a few passenger cars. Flow is stable."
                ]
                return f"[SIMULATION] {random.choice(conditions)}"
            elif prompt_key == 'count':
                cars = random.randint(3, 28)
                trucks = random.randint(0, 5)
                return f"[SIMULATION] Vehicle Count: Approximately {cars} cars, {trucks} trucks, and 1 motorcycle detected in the frame. Traffic density is {'high' if cars > 18 else 'moderate' if cars > 8 else 'low'}."
            elif prompt_key == 'hazard':
                hazards = [
                    "No hazards detected. Lanes are clear, and traffic flow is normal.",
                    "No collisions detected. However, a vehicle is parked on the right shoulder with hazard lights blinking.",
                    "Road construction warning: Lane closure signs are visible in the distance, causing traffic to merge. Speed limit reduced.",
                    "Minor delay due to wet road conditions and spray from large trucks. No lane blockages observed."
                ]
                return f"[SIMULATION] {random.choice(hazards)}"
            elif prompt_key == 'safety':
                safeties = [
                    "[SIMULATION] SAFE: clear traffic flow.",
                    "[SIMULATION] SAFE: normal road conditions.",
                    "[SIMULATION] SAFE: clear roadway and flow.",
                    "[SIMULATION] HAZARD ALERT: stalled vehicle on shoulder.",
                    "[SIMULATION] ACCIDENT ALERT: multi-vehicle collision.",
                    "[SIMULATION] COLLISION ALERT: minor rear-end accident."
                ]
                # Let's bias towards Safe (80% safe)
                weights = [0.25, 0.25, 0.30, 0.10, 0.05, 0.05]
                return random.choices(safeties, weights=weights)[0]
        
        elif feed_type == 'zoo':
            if prompt_key == 'describe':
                activities = [
                    "The animal is resting comfortably in the shade of a large oak tree. It appears relaxed and is observing its surroundings.",
                    "Active play observed! The animals are interacting near the watering hole, splashing water and running along the bank.",
                    "Feeding time: The primary subject is foraging on fresh leaves and plants, showing high engagement with its food.",
                    "The animal is grooming itself near the front of the enclosure, providing excellent visibility for visitors."
                ]
                return f"[SIMULATION] {random.choice(activities)}"
            elif prompt_key == 'count':
                count = random.randint(1, 4)
                return f"[SIMULATION] Animal Count: {count} active animal(s) detected clearly in the central viewing area of the enclosure. No others are currently visible in the background."
            elif prompt_key == 'hazard': # actually mapped to activity level in presets
                levels = [
                    "Activity Level: High. The animals are moving actively, climbing branches, and playing.",
                    "Activity Level: Medium. The animals are eating bamboo/leaves and moving slowly around the habitat.",
                    "Activity Level: Low. The animal is curled up sleeping under the canopy, displaying resting behaviors."
                ]
                return f"[SIMULATION] {random.choice(levels)}"
            elif prompt_key == 'safety':
                return "[SIMULATION] SAFE: animals behavior normal."

        return "[SIMULATION] Image analysis complete. Subject is visible and stable under current lighting conditions."

    def analyze_text(self, prompt, mock_fallback_response=""):
        """Sends a text-only prompt to Gemini with simulated fallback."""
        if self.gemini_client.api_key:
            try:
                print(f"[Analyzer] Running Gemini text analysis...")
                return self.gemini_client.analyze_text(prompt)
            except Exception as e:
                print(f"[Analyzer] Gemini text analysis failed ({e}). Falling back to simulation...")
        return f"[SIMULATION] {mock_fallback_response}"

    def analyze_structured(self, feed_type: str, img_url: str, surveillance_target: str) -> dict:
        """Single structured Gemini call covering count, safety, and surveillance in one request.
        
        Returns a dict with guaranteed keys regardless of API availability.
        """
        default_traffic = {
            "vehicle_count": 0, "count_summary": "N/A",
            "safety_status": "Safe", "safety_detail": "No data available.",
            "surveillance_notes": "No data available."
        }
        default_zoo = {
            "animal_count": 0, "count_summary": "N/A",
            "activity_level": "Normal", "safety_status": "Safe",
            "safety_detail": "No data available.", "surveillance_notes": "No data available."
        }
        default = default_traffic if feed_type == 'traffic' else default_zoo

        if self.gemini_client.api_key:
            try:
                print(f"[Analyzer] Running structured Gemini analysis ({feed_type})...")
                raw = self.gemini_client.analyze_image_structured(img_url, feed_type, surveillance_target)
                result = json.loads(raw)
                # Merge with defaults to ensure all keys present
                return {**default, **result}
            except Exception as e:
                print(f"[Analyzer] Structured analysis failed ({e}). Falling back to simulation...")

        return self._generate_structured_mock(feed_type)

    async def analyze_structured_async(self, feed_type: str, img_url: str, surveillance_target: str) -> dict:
        """Async version of analyze_structured — uses thread-pool so the event loop isn't blocked."""
        default_traffic = {
            "vehicle_count": 0, "count_summary": "N/A",
            "safety_status": "Safe", "safety_detail": "No data available.",
            "surveillance_notes": "No data available."
        }
        default_zoo = {
            "animal_count": 0, "count_summary": "N/A",
            "activity_level": "Normal", "safety_status": "Safe",
            "safety_detail": "No data available.", "surveillance_notes": "No data available."
        }
        default = default_traffic if feed_type == 'traffic' else default_zoo

        if self.gemini_client.api_key:
            try:
                print(f"[Analyzer] Running async structured Gemini analysis ({feed_type})...")
                raw = await self.gemini_client.analyze_image_structured_async(img_url, feed_type, surveillance_target)
                result = json.loads(raw)
                return {**default, **result}
            except Exception as e:
                print(f"[Analyzer] Async structured analysis failed ({e}). Falling back to simulation...")

        return self._generate_structured_mock(feed_type)

    async def analyze_text_async(self, prompt: str, mock_fallback_response: str = "") -> str:
        """Async version of analyze_text."""
        if self.gemini_client.api_key:
            try:
                print(f"[Analyzer] Running async Gemini text analysis...")
                return await self.gemini_client.analyze_text_async(prompt)
            except Exception as e:
                print(f"[Analyzer] Async Gemini text analysis failed ({e}). Falling back to simulation...")
        return f"[SIMULATION] {mock_fallback_response}"

    def _generate_structured_mock(self, feed_type: str) -> dict:
        """Generates realistic structured mock data for offline/fallback testing."""
        if feed_type == 'traffic':
            cars = random.randint(3, 28)
            trucks = random.randint(0, 5)
            total = cars + trucks
            # 80% safe, 15% hazard, 5% accident
            safety = random.choices(
                ["Safe", "Safe", "Safe", "Safe", "Hazard", "Accident"],
                weights=[0.25, 0.25, 0.15, 0.15, 0.15, 0.05]
            )[0]
            detail_map = {
                "Safe": "Traffic flowing normally. Lanes clear with no visible incidents.",
                "Hazard": "Vehicle parked on shoulder with hazard lights active. Lanes passable.",
                "Accident": "Multi-vehicle incident detected. Emergency vehicles may be needed."
            }
            return {
                "vehicle_count": total,
                "count_summary": f"{total} Vehicles",
                "safety_status": safety,
                "safety_detail": f"[SIMULATION] {detail_map[safety]}",
                "surveillance_notes": "[SIMULATION] Nothing to flag." if safety == "Safe" else f"[SIMULATION] {detail_map[safety]}"
            }
        else:  # zoo
            count = random.randint(1, 4)
            activity = random.choices(["Low", "Normal", "High"], weights=[0.3, 0.5, 0.2])[0]
            detail_map = {
                "Low": "Animals resting quietly. No active movement observed.",
                "Normal": "Animals moving around enclosure normally. Feeding observed.",
                "High": "Animals highly active — playing, running, and interacting near the water."
            }
            fun_moments = [
                "The panda is doing full somersaults down the grassy hill!",
                "Two animals are splashing and chasing each other around the water feature!",
                "A baby animal is wobbling around and tumbling over its own feet!",
                "The animal just struck the most ridiculous sprawled-out pose on the rock!",
                "One animal is playing tug-of-war with an enrichment toy!",
            ]
            is_fun = activity == "High" and random.random() < 0.4
            fun_desc = random.choice(fun_moments) if is_fun else ""
            return {
                "animal_count": count,
                "count_summary": f"{count} Animals",
                "activity_level": activity,
                "safety_status": "Safe",
                "safety_detail": f"[SIMULATION] {detail_map[activity]}",
                "fun_moment": is_fun,
                "fun_description": f"[SIMULATION] {fun_desc}" if is_fun else "",
                "surveillance_notes": "[SIMULATION] Nothing to flag." if not is_fun else f"[SIMULATION] {fun_desc}"
            }
