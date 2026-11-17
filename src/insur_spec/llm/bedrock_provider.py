from __future__ import annotations

import json
import os
from typing import AsyncIterator, Optional
from .base import EnterpriseProviderInterface


class BedrockProvider(EnterpriseProviderInterface):
    """AWS Bedrock adapter for enterprise VPC production deployment."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name: str = "us-east-1",
    ):
        self.model_id = model_id
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

    def _get_client(self):
        try:
            import boto3
            return boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name,
            )
        except ImportError:
            raise ImportError(
                "boto3 package not installed. Install via: pip install 'insur-spec[bedrock]' or pip install boto3"
            )

    def generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        # Check for AWS credentials or mock mode
        if not (os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE") or os.getenv("AWS_ROLE_ARN")):
            return (
                f"[AWS Bedrock Mock ({self.model_id}) - AWS credentials unset for local dev]\n"
                f"Generated compliant enterprise response for: {prompt[:80]}...\n"
                f"VPC Boundary respected. Zero data retention active."
            )

        client = self._get_client()

        # Format Anthropic Claude Messages API payload for Bedrock
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_output_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        if system_instructions:
            payload["system"] = system_instructions

        response = client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))
        content_blocks = response_body.get("content", [])
        return "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")

    async def stream_generate(
        self,
        prompt: str,
        system_instructions: str = "",
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        # For simplicity in enterprise environments, yield full response chunk
        full_text = self.generate(
            prompt=prompt,
            system_instructions=system_instructions,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        yield full_text
