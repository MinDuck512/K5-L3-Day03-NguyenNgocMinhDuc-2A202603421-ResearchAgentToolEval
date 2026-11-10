"""Provider regression tests; all SDK and HTTP calls are simulated."""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
import requests

from conftest import FakeResponse
from providers.openai_provider import OpenAIProvider


def install_blocked_sdk(monkeypatch) -> None:
    class BlockedClient:
        def __init__(self, **kwargs):
            pass

        @property
        def chat(self):
            raise ImportError(
                "DLL load failed while importing jiter: "
                "An Application Control policy has blocked this file."
            )

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=BlockedClient))


def completion_payload(arguments: str = '{"screenname":"sama"}') -> dict:
    return {"choices": [{"message": {"content": None, "tool_calls": [
        {"type": "function", "function": {"name": "timeline", "arguments": arguments}},
    ]}}]}


def test_blocked_sdk_uses_same_request_and_normalizes_tool_calls(monkeypatch, fake_http):
    install_blocked_sdk(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    payload = completion_payload()
    calls = fake_http(FakeResponse(payload))
    messages = [{"role": "user", "content": "Latest tweets?"}]
    tools = [{"type": "function", "function": {"name": "timeline"}}]

    result = OpenAIProvider().complete(messages, tools, model="test-model", tool_choice="required")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0]["timeout"] == (10, 60)
    assert calls[0]["json"] == {
        "model": "test-model", "messages": messages, "temperature": 0.0,
        "tools": tools, "tool_choice": "required",
    }
    assert result.tool_calls[0].name == "timeline"
    assert result.tool_calls[0].args == {"screenname": "sama"}
    assert result.raw is payload


@pytest.mark.parametrize("arguments", ["{bad json", "[]"])
def test_fallback_preserves_invalid_arguments_for_eval(monkeypatch, fake_http, arguments):
    install_blocked_sdk(monkeypatch)
    fake_http(FakeResponse(completion_payload(arguments)))

    result = OpenAIProvider(api_key_default="fake-key").complete([])

    assert result.tool_calls[0].args == {"_invalid_json_arguments": arguments}


def test_fallback_respects_custom_base_url_and_text_only_response(monkeypatch, fake_http):
    install_blocked_sdk(monkeypatch)
    calls = fake_http(FakeResponse({"choices": [{"message": {"content": "Hello"}}]}))

    result = OpenAIProvider(base_url="http://localhost:11434/v1/", api_key_default="ollama").complete([])

    assert calls[0]["url"] == "http://localhost:11434/v1/chat/completions"
    assert result.text == "Hello"
    assert result.tool_calls == []
    assert "tools" not in calls[0]["json"]
    assert "tool_choice" not in calls[0]["json"]


def test_fallback_propagates_http_error_without_sdk_retry(monkeypatch, fake_http):
    install_blocked_sdk(monkeypatch)
    calls = fake_http(FakeResponse(status_code=401))

    with pytest.raises(requests.HTTPError, match="401"):
        OpenAIProvider(api_key_default="fake-key").complete([])

    assert len(calls) == 1


def test_fallback_reports_quota_code_without_echoing_error_message(monkeypatch, fake_http):
    install_blocked_sdk(monkeypatch)
    fake_http(FakeResponse({"error": {
        "code": "insufficient_quota", "message": "sensitive-value-from-provider",
    }}, status_code=429))

    with pytest.raises(requests.HTTPError, match="insufficient_quota") as caught:
        OpenAIProvider(api_key_default="fake-key").complete([])

    assert "sensitive-value-from-provider" not in str(caught.value)


def test_healthy_sdk_still_uses_sdk_without_http_fallback(monkeypatch, fake_http):
    payload = completion_payload()
    response = SimpleNamespace(model_dump=lambda: payload)
    sdk_calls = []

    def create(**kwargs):
        sdk_calls.append(kwargs)
        return response

    def make_client(**kwargs):
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=make_client))
    http_calls = fake_http(FakeResponse())

    result = OpenAIProvider(api_key_default="fake-key").complete([])

    assert len(sdk_calls) == 1
    assert http_calls == []
    assert result.raw is response
    assert result.tool_calls[0].args == {"screenname": "sama"}
