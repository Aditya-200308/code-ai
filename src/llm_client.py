# ============================================================
# FILE: src/llm_client.py
# PURPOSE: Google Gemini Cloud AI Client (High-Speed Cloud Inference)
# ============================================================

from typing import Dict, Any, List, Optional
import os
import json
import re
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class LLMClient:
    """High-speed Gemini AI client with automatic model fallback."""

    # Priority order for fastest response and lowest latency
    GEMINI_MODELS = ["gemini-3.8-flash"]

    def __init__(self, api_key: Optional[str] = None, engine_mode: str = "cloud_turbo"):
        self.api_key = api_key or self._get_secret("GEMINI_API_KEY")
        self.engine_mode = "cloud_turbo"

    def _get_secret(self, key_name: str) -> str:
        """Fetches API key from env vars or Streamlit Cloud secrets."""
        val = os.environ.get(key_name)
        if not val:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and key_name in st.secrets:
                    val = st.secrets[key_name]
            except Exception:
                pass
        return val or ""

    def generate(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.15, max_tokens: int = 2048) -> str:
        """
        Generates text using Google Gemini API with automatic model fallback.
        """
        gemini_key = self.api_key or self._get_secret("GEMINI_API_KEY")
        if not gemini_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing! Please configure GEMINI_API_KEY in your .env file."
            )

        combined = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER REQUEST:\n{user_prompt}"
        last_error = ""

        for attempt in range(2):
            for model in self.GEMINI_MODELS:
                try:
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/"
                        f"models/{model}:generateContent?key={gemini_key}"
                    )
                    payload = {
                        "contents": [{"parts": [{"text": combined}]}],
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens,
                        },
                    }
                    res = requests.post(url, json=payload, timeout=20)

                    if res.status_code == 200:
                        data = res.json()
                        return (
                            data["candidates"][0]["content"]["parts"][0]["text"]
                            .strip()
                        )
                    elif res.status_code == 429:
                        last_error = f"Rate limit on {model}, rotating to next model..."
                        continue
                    else:
                        last_error = f"Gemini API error on {model} (HTTP {res.status_code})"
                        continue
                except Exception as e:
                    last_error = str(e)
                    continue

        raise RuntimeError(
            last_error or "Unable to reach Gemini API. Please check your API key and internet connection."
        )

    def generate_json(self, system_prompt: str, user_prompt: str,
                      max_tokens: int = 350) -> Dict[str, Any]:
        """Generates validated JSON output with regex recovery fallback."""
        json_system = (
            f"{system_prompt}\n"
            "CRITICAL: Respond ONLY with a valid JSON object. "
            "No Markdown code fences or extra text."
        )

        raw = self.generate(json_system, user_prompt, temperature=0.1, max_tokens=max_tokens)

        # Strip markdown fences
        clean = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
        clean = re.sub(r"^```\s*", "", clean, flags=re.MULTILINE).strip()

        try:
            return json.loads(clean)
        except Exception:
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            return {"error": "Failed to parse JSON response", "raw": clean}
