import urllib.request
import json
import base64
import ssl
import os
import asyncio

class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        
        # Bypass SSL verification for downloading camera feeds
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def fetch_image_base64(self, img_url):
        """Downloads an image from URL and encodes it to base64."""
        try:
            if "youtube.com" in img_url or "youtu.be" in img_url:
                from inputs.youtube_grabber import YoutubeFrameGrabber
                import cv2
                print(f"[GeminiClient] Intercepted YouTube URL: {img_url}. Grabbing frame...")
                frame = YoutubeFrameGrabber.grab_frame(img_url)
                if frame is not None:
                    success, encoded_image = cv2.imencode('.jpg', frame)
                    if success:
                        return base64.b64encode(encoded_image.tobytes()).decode('utf-8')
                raise ValueError("Failed to capture frame from YouTube stream")
            else:
                req = urllib.request.Request(
                    img_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=10) as response:
                    img_data = response.read()
                    return base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            print(f"[GeminiClient] Error downloading/capturing image {img_url}: {e}")
            raise

    def analyze_image(self, img_url, prompt):
        """Sends the image and prompt to the Gemini API."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        try:
            # 1. Download image and encode to base64
            img_b64 = self.fetch_image_base64(img_url)
            
            # 2. Prepare payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Use gemini-3.5-flash which is widely available and supports multimodal input
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=20) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                
            # Extract response text
            candidates = resp_data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', 'No analysis returned from Gemini.')
            
            return "Gemini API returned an empty response."

        except Exception as e:
            print(f"[GeminiClient] Error in analyze_image: {e}")
            raise

    def analyze_image_b64(self, img_b64, prompt):
        """Sends pre-fetched base64 image bytes + prompt to Gemini. No re-download."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": img_b64
                            }
                        }
                    ]
                }
            ]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=20) as response:
            resp_data = json.loads(response.read().decode('utf-8'))

        candidates = resp_data.get('candidates', [])
        if candidates:
            parts = candidates[0].get('content', {}).get('parts', [])
            if parts:
                return parts[0].get('text', 'No analysis returned from Gemini.')
        return "Gemini API returned an empty response."

    def analyze_text(self, prompt):
        """Sends a text-only prompt to the Gemini API."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=20) as response:
                resp_data = json.loads(response.read().decode('utf-8'))
                
            candidates = resp_data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', 'No analysis returned from Gemini.')
            
            return "Gemini API returned an empty response."

        except Exception as e:
            print(f"[GeminiClient] Error in analyze_text: {e}")
            raise

    def analyze_image_structured(self, img_url, feed_type: str, surveillance_target: str) -> str:
        """Single multi-task Gemini call: returns a JSON string covering count, safety, and surveillance notes.
        
        Replaces separate count, safety, and surveillance calls with one efficient request.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        if feed_type == 'traffic':
            prompt = f"""You are an expert traffic surveillance analyst reviewing a live highway camera feed.
Analyze this image and respond ONLY with a valid JSON object — no markdown, no explanation, just raw JSON.

{{
  "vehicle_count": <integer count of all visible vehicles>,
  "count_summary": "<X> Vehicles",
  "safety_status": "<one of: Safe | Hazard | Accident | Collision>",
  "safety_detail": "<1-2 sentence description of road conditions and any incidents>",
  "surveillance_notes": "<observations relevant to: {surveillance_target}. Write 'Nothing to flag.' if all clear.>"
}}"""
        else:  # zoo
            prompt = f"""You are a wildlife camera analyst with a sharp eye for delightful animal moments. Review this live zoo enclosure image.
Respond ONLY with a valid JSON object — no markdown, no explanation, just raw JSON.

{{
  "animal_count": <integer count of all visible animals>,
  "count_summary": "<X> Animals",
  "activity_level": "<one of: Low | Normal | High>",
  "safety_status": "<one of: Safe | Concern | Emergency>",
  "safety_detail": "<1-2 sentence description of animal welfare>",
  "fun_moment": <true if something delightful, quirky, or rare is visibly happening — rolling, splashing, playing, funny pose, baby animal antics, unexpected behavior — false if animals are just resting or eating normally>,
  "fun_description": "<if fun_moment is true: an enthusiastic 1-sentence description of what's happening that would make someone want to rush over, e.g. 'The panda is doing full somersaults down the hill!' — otherwise empty string>",
  "surveillance_notes": "<observations relevant to: {surveillance_target}. Write 'Nothing to flag.' if all clear.>"
}}"""

        try:
            img_b64 = self.fetch_image_base64(img_url)

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,  # Low temp for consistent structured output
                    "responseMimeType": "application/json"
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                resp_data = json.loads(response.read().decode('utf-8'))

            candidates = resp_data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                if parts:
                    return parts[0].get('text', '{}')

            return '{}'

        except Exception as e:
            print(f"[GeminiClient] Error in analyze_image_structured: {e}")
            raise

    # ------------------------------------------------------------------
    # Async wrappers — run blocking urllib calls in a thread-pool executor
    # so the asyncio event loop is never blocked.
    # ------------------------------------------------------------------

    async def fetch_image_base64_async(self, img_url: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_image_base64, img_url)

    async def analyze_image_async(self, img_url: str, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_image, img_url, prompt)

    async def analyze_text_async(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_text, prompt)

    async def analyze_image_structured_async(self, img_url: str, feed_type: str, surveillance_target: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_image_structured, img_url, feed_type, surveillance_target)
