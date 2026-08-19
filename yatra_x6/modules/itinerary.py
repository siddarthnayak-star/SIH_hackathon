import json
import os
import re

import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def generate_itinerary(destination, days, budget, interests):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    prompt = f"""
    You are a travel planning assistant. Create a {days}-day itinerary for {destination}.
    Budget: {budget} INR total. Interests: {', '.join(interests or [])}.
    Return ONLY valid JSON, no markdown, in this exact shape:
    {{
      "destination": "...",
      "total_estimated_cost": 0,
      "days": [
        {{"day": 1, "theme": "...", "activities": [
            {{"time": "09:00", "place": "...", "cost": 0, "notes": "..."}}
        ]}}
      ]
    }}
    """

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )

    if response.status_code >= 400:
        try:
            error_details = response.json()
        except ValueError:
            error_details = response.text
        raise RuntimeError(f"Gemini API request failed ({response.status_code}): {error_details}")

    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini API returned no candidates: {payload}")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError(f"Gemini API response did not include content parts: {payload}")

    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text:
        raise ValueError(f"Gemini API returned empty text in response: {payload}")

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini response was not valid JSON: {text}") from exc