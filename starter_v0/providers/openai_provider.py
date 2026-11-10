from __future__ import annotations

import json
import os
from typing import Any

import requests

from providers.base import ModelResponse, ToolCall


class OpenAIProvider:
    """OpenAI Chat Completions provider with normalized tool_calls output."""

    def __init__(
        self,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
        api_key_default: str | None = None,
    ) -> None:
        self.api_key_env = api_key_env
        self.api_key_default = api_key_default
        self.base_url = base_url
        self.default_model = default_model

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        api_key = os.getenv(self.api_key_env) or self.api_key_default
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {self.api_key_env}")

        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=self.base_url, timeout=60.0, max_retries=0)
            resp = client.chat.completions.create(**kwargs)
        except ImportError as exc:
            if "application control policy has blocked" not in str(exc).lower():
                raise RuntimeError("Install live provider dependency first: pip install openai") from exc
        else:
            return self._normalize_response(resp.model_dump(), raw=resp)

        # Windows may block the SDK's native JSON extension. Use the same
        # REST endpoint without loading that extension or changing OS policy.
        base_url = self.base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=kwargs,
            timeout=(10, 60),
        )
        try:
            response.raise_for_status()
        except requests.HTTPError:
            # Report the machine-readable code, not an error message that may
            # echo a credential. Keep the original response for diagnostics.
            error_code = None
            try:
                error = response.json().get("error")
                if isinstance(error, dict):
                    error_code = error.get("code")
            except (ValueError, AttributeError):
                pass
            raise requests.HTTPError(
                f"Model API HTTP {response.status_code} ({error_code or 'request_failed'}).",
                response=response,
            ) from None
        payload = response.json()
        return self._normalize_response(payload, raw=payload)

    @staticmethod
    def _normalize_response(payload: dict[str, Any], *, raw: Any) -> ModelResponse:
        msg = payload["choices"][0]["message"]
        calls: list[ToolCall] = []
        for call in msg.get("tool_calls") or []:
            function = call["function"]
            raw_args = function.get("arguments") or "{}"
            try:
                args = json.loads(raw_args)
            except (json.JSONDecodeError, TypeError):
                # Small models often emit malformed JSON. Keep the call so eval grades it
                # as a wrong-argument failure instead of hiding it as provider_error.
                args = {"_invalid_json_arguments": raw_args}
            if not isinstance(args, dict):
                args = {"_invalid_json_arguments": raw_args}
            calls.append(ToolCall(name=function["name"], args=args))
        return ModelResponse(text=msg.get("content"), tool_calls=calls, raw=raw)
