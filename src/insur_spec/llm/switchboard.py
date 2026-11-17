from __future__ import annotations

import os
from typing import Optional
from .base import EnterpriseProviderInterface
from .gemini_provider import GeminiProvider
from .bedrock_provider import BedrockProvider


class LLMSwitchboard:
    """Enterprise multi-LLM dynamic switchboard."""

    @staticmethod
    def get_provider(
        provider_name: str = "auto",
        gemini_model: str = "gemini-3.8-flash",
        bedrock_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_region: str = "us-east-1",
    ) -> EnterpriseProviderInterface:
        resolved = (provider_name or "auto").lower()

        if resolved == "auto":
            env_override = os.getenv("INSURSPEC_LLM_PROVIDER", "").lower()
            if env_override in ("gemini", "bedrock"):
                resolved = env_override
            elif os.getenv("AWS_ROLE_ARN") or os.getenv("AWS_BEDROCK_ASSUME_ROLE"):
                resolved = "bedrock"
            else:
                # Default to Gemini for local test ergonomics
                resolved = "gemini"

        if resolved == "bedrock":
            return BedrockProvider(model_id=bedrock_model, region_name=aws_region)
        elif resolved == "gemini":
            return GeminiProvider(model_name=gemini_model)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}. Expected 'gemini', 'bedrock', or 'auto'.")
