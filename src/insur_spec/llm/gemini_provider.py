from __future__ import annotations

import os
from typing import AsyncIterator, Optional
from .base import EnterpriseProviderInterface


class GeminiProvider(EnterpriseProviderInterface):
    """Google Cloud Vertex AI & Gemini SDK adapter for local/staging testing."""

    def __init__(self, model_name: str = "gemini-3.8-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _get_client(self):
        try:
            from google import genai
            return genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "google-genai package not installed. Install via: pip install 'insur-spec[gemini]' or pip install google-genai"
            )

    def generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        if not self.api_key:
            # Fallback mock for offline architectural validation and testing
            return (
                f"[Gemini Mock ({self.model_name}) - GEMINI_API_KEY unset]\n"
                f"Generated compliant architecture for: {prompt[:80]}...\n"
                f"Verified against Constitution and Backstage catalog-info.yaml."
            )

        client = self._get_client()
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instructions if system_instructions else None,
        )

        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text or ""

    async def stream_generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            yield f"[Gemini Mock ({self.model_name}) - Offline Mode]\nResponse to: {prompt[:60]}..."
            return

        client = self._get_client()
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instructions if system_instructions else None,
        )

        response = client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
