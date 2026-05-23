import random
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
                'count': "Count every vehicle visible in this image (cars, trucks, motorcycles, vans, buses). Be precise. Output exactly one line in this format: 'Total: N vehicles' where N is the exact number you count. Do not approximate.",
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
                total = random.randint(4, 32)
                return f"[SIMULATION] Total: {total} vehicles"
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
