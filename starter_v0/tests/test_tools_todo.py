"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tài khoản A", "Tài khoản B"]
    result = TOOL_FUNCTIONS["clarify"]("Chọn tài khoản", response_type="choice", options=options)
    assert result["options"] == options
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [{"section": s, "title": s} for s in ["A", "B", "A"]]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    markdown = TOOL_FUNCTIONS["format"](items=[{"title": "A"}, {"title": "B"}], template="thread")["markdown"]
    assert markdown.splitlines()[0].startswith("1/")
    assert markdown.splitlines()[2].startswith("2/")


def test_format_empty_items_does_not_crash() -> None:
    for items in (None, []):
        assert TOOL_FUNCTIONS["format"](items=items, template="bullets")["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)
    assert result["status"] == "sent"
    assert len(calls) == 1
    assert "test-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "test-chat"
    assert calls[0]["json"]["text"] == "Bản tin"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    result = TOOL_FUNCTIONS["lookup"](query="AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"data": {"markdown": "Content", "metadata": {"title": "T", "sourceURL": "https://example.org/a"}}}))
    item = TOOL_FUNCTIONS["fetch"]("https://example.org/a")["items"][0]
    assert item["title"] == "T"
    assert item["url"] == "https://example.org/a"
    assert item["source"] == "example.org"
    assert item["summary"] == "Content"
    assert calls[0]["json"]["formats"] == ["markdown"]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000}}))
    result = TOOL_FUNCTIONS["fetch"]("https://example.org/a")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    tweets = [{"text": "missing id", "screen_name": "sample"}] + [
        {"tweet_id": str(i), "text": f"Post {i}", "screen_name": "sample"} for i in range(6)
    ]
    calls = fake_http(FakeResponse({"timeline": tweets}))
    result = TOOL_FUNCTIONS["timeline"]("sample", limit=3)
    assert len(result["items"]) == 3
    assert all(item["url"].startswith("https://x.com/sample/status/") for item in result["items"])
    assert calls[0]["params"]["screenname"] == "sample"


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    TOOL_FUNCTIONS["social_search"]("OpenAI", search_type="Top")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert TOOL_FUNCTIONS["policy"](query="")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = TOOL_FUNCTIONS["policy"](query="data", policy_area="data_privacy")
    assert "error" not in result
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = TOOL_FUNCTIONS["policy"](query="source citation", policy_area="source_citation", top_k=20)
    assert result["results"]
    untrusted = " ".join(" ".join(hit["untrusted_text"]) for hit in result["results"])
    facts = " ".join(hit["facts"] for hit in result["results"])
    assert "ignore" in untrusted.lower() or "bỏ qua" in untrusted.lower()
    assert "ignore previous" not in facts.lower()


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

def test_my_new_tool_happy_path() -> None:
    result = TOOL_FUNCTIONS["source_validator"]("https://arxiv.org/abs/1706.03762", "Attention Is All You Need", "Vaswani et al.")
    assert result["valid"] is True
    assert result["category"] == "academic"
    assert result["citation_complete"] is True


def test_my_new_tool_bad_input_from_model() -> None:
    result = TOOL_FUNCTIONS["source_validator"]("javascript:alert(1)")
    assert result["valid"] is False
    assert "error" in result


def test_my_new_tool_failure_returns_error_dict() -> None:
    result = TOOL_FUNCTIONS["source_validator"](None)  # type: ignore[arg-type]
    assert result["valid"] is False
    assert "error" in result
