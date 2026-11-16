import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from backend.config.settings import settings

logger = logging.getLogger("CareCoord.LLMClient")

class LLMClient:
    """
    Unified LLM Client for CareCoord.
    Prioritizes local Ollama (e.g. qwen2.5:3b) on the user's laptop for fast, private, offline inference,
    with graceful fallback to Gemini API or deterministic extraction.
    """
    def __init__(self):
        self.ollama_base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.ollama_model = getattr(settings, "OLLAMA_MODEL", "qwen2.5:3b")
        self.provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

    def is_ollama_available(self, timeout: float = 2.0) -> bool:
        """Check if local Ollama daemon is reachable and responding."""
        try:
            url = f"{self.ollama_base_url.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = False,
        timeout: int = 45
    ) -> Optional[str]:
        """
        Generate text completion using local Ollama, falling back to Gemini if configured.
        """
        # 1. Try local Ollama first
        if self.provider == "ollama" or not self.gemini_api_key:
            ollama_resp = self._generate_ollama(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                json_mode=json_mode,
                timeout=timeout
            )
            if ollama_resp:
                return ollama_resp

        # 2. Try Gemini API fallback if API key exists
        if self.gemini_api_key:
            gemini_resp = self._generate_gemini(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )
            if gemini_resp:
                return gemini_resp

        return None

    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = False,
        timeout: int = 45
    ) -> Optional[str]:
        """Calls local Ollama API endpoint."""
        try:
            url = f"{self.ollama_base_url.rstrip('/')}/api/generate"
            payload: Dict[str, Any] = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 384
                }
            }
            if system_prompt:
                payload["system"] = system_prompt
            if json_mode:
                payload["format"] = "json"

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read().decode("utf-8"))
                    text = body.get("response", "").strip()
                    if text:
                        return text
        except Exception as exc:
            logger.warning(f"Local Ollama generation failed: {exc}")
        return None

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> Optional[str]:
        """Fallback to Google Gemini SDK if key is configured."""
        try:
            import google.genai as genai
            client = genai.Client(api_key=self.gemini_api_key)
            full_content = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_content
            )
            if response.text and response.text.strip():
                return response.text.strip()
        except Exception as exc:
            logger.warning(f"Gemini API fallback failed: {exc}")
        return None

# Singleton instance for CareCoord
llm_client = LLMClient()
