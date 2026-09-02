from __future__ import annotations

import json
from typing import Any

from diff2tweet.config import RuntimeConfig

from .base import BaseProvider, ProviderError


class OpenAIProvider(BaseProvider):
    """OpenAI chat-completions implementation for tweet generation."""

    def generate_tweets(self, prompt_text: str, config: RuntimeConfig) -> list[str]:
        api_key = config.provider_api_key.get_secret_value() if config.provider_api_key else None
        if not api_key:
            raise ProviderError("OpenAI provider is missing an API key.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError(
                "The 'openai' package is required for provider 'openai'. Install project dependencies first."
            ) from exc

        import os
        base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("NIM_BASE_URL") or os.environ.get("NVIDIA_BASE_URL")
        # NIM endpoint par défaut si NVIDIA_API_KEY détectée
        if not base_url and (os.environ.get("NVIDIA_API_KEY") or os.environ.get("NIM_API_KEY")):
            base_url = "https://integrate.api.nvidia.com/v1"
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        tweets: list[str] = []
        for _ in range(config.num_candidates):
            response = client.chat.completions.create(
                model=config.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You generate tweet drafts from git context.",
                    },
                    {
                        "role": "user",
                        "content": prompt_text,
                    },
                ],
            )
            tweets.append(_parse_single_tweet(response))
        return tweets


def _parse_single_tweet(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if not choices:
        raise ProviderError("OpenAI returned no choices.")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if not content:
        raise ProviderError("OpenAI returned an empty response.")

    if isinstance(content, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "")
            for part in content
        )
    else:
        text = str(content)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError("OpenAI response was not valid JSON.") from exc

    tweet = payload.get("tweet")
    if not isinstance(tweet, str) or not tweet.strip():
        raise ProviderError("OpenAI response did not include a 'tweet' string.")

    return tweet.strip()
