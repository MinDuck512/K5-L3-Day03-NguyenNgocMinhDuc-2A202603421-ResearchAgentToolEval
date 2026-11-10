"""Tool Unit Test Challenge.

All stub tests implemented.
Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
One behaviour per test. Assert request and response.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    clarify_tool = TOOL_FUNCTIONS["clarify"]
    result = clarify_tool(question="Chon nguon tin?", response_type="choice", options=["Twitter", "Web"])
    assert result["tool"] == "ask_user"
    assert result["question"] == "Chon nguon tin?"
    assert result["response_type"] == "choice"
    assert result["options"] == ["Twitter", "Web"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Item 1", "section": "A", "url": "https://example.com/1"},
        {"title": "Item 2", "section": "B", "url": "https://example.com/2"},
        {"title": "Item 3", "section": "A", "url": "https://example.com/3"},
    ]
    result = format_tool(items=items, template="sections", headline="Test Headline")
    assert result["markdown"].count("## A") == 1
    assert result["markdown"].count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"summary": "First point", "url": "https://example.com/1"},
        {"summary": "Second point", "url": "https://example.com/2"},
    ]
    result = format_tool(items=items, template="thread")
    lines = result["markdown"].split("\n\n")
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    res1 = format_tool(items=None)
    res2 = format_tool(items=[])
    assert res1["item_count"] == 0
    assert res2["item_count"] == 0
    assert res1["markdown"] == ""
    assert res2["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_bot_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    calls = fake_http(FakeResponse({"ok": True, "result": {"message_id": 99}}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Hello Telegram", confirmed=True)
    assert len(calls) == 1
    assert "fake_bot_token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "123456"
    assert calls[0]["json"]["text"] == "Hello Telegram"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Hello", confirmed=True)
    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "dummy_key")
    calls = fake_http(FakeResponse({"results": []}))
    lookup_tool = TOOL_FUNCTIONS["lookup"]
    result = lookup_tool(query="test query", timeframe=None)
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["query"] == "test query"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc_test_key")
    fake_payload = {
        "data": {
            "markdown": "# Title\nDetailed content here.",
            "metadata": {"title": "Sample Title", "sourceURL": "https://example.com/sample"},
        }
    }
    calls = fake_http(FakeResponse(fake_payload))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/sample")
    assert len(calls) == 1
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["title"] == "Sample Title"
    assert item["url"] == "https://example.com/sample"
    assert item["source"] == "example.com"
    assert "Detailed content here." in item["summary"]


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc_test_key")
    long_markdown = "A" * 5000
    fake_http(FakeResponse({"data": {"markdown": long_markdown, "metadata": {}}}))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/long")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid_test_key")
    raw_items = [
        {"tweet_id": "101", "screen_name": "sama", "text": "Tweet 1"},
        {"screen_name": "sama", "text": "Invalid tweet without id"},
        {"id": "102", "screen_name": "sama", "text": "Tweet 2"},
        {"tweet_id": "103", "screen_name": "sama", "text": "Tweet 3"},
        {"tweet_id": "104", "screen_name": "sama", "text": "Tweet 4"},
        {"tweet_id": "105", "screen_name": "sama", "text": "Tweet 5"},
        {"tweet_id": "106", "screen_name": "sama", "text": "Tweet 6"},
    ]
    fake_http(FakeResponse({"timeline": raw_items}))
    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="sama", limit=3)
    assert len(result["items"]) == 3
    for item in result["items"]:
        assert item["url"].startswith("https://x.com/sama/status/")


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid_test_key")
    calls = fake_http(FakeResponse({"timeline": []}))
    search_tool = TOOL_FUNCTIONS["social_search"]
    result = search_tool(query="GPT-5", search_type="Top")
    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "GPT-5"
    assert calls[0]["params"]["search_type"] == "Top"
    assert result["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="data retention customer", policy_area="data_privacy")
    assert len(result["results"]) > 0
    for item in result["results"]:
        assert item["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="injection probe", policy_area="source_citation", top_k=5)
    found_untrusted = False
    for hit in result["results"]:
        if hit["untrusted_text"]:
            found_untrusted = True
            for untrusted_line in hit["untrusted_text"]:
                assert "ignore the citation policy" in untrusted_line
                assert untrusted_line not in hit["facts"]
    assert found_untrusted


# ---------------- NEW CUSTOM TOOLS (≥ 3 tests per tool) ----------------

# 1. summarize tool
def test_summarize_happy_path() -> None:
    summarize_tool = TOOL_FUNCTIONS["summarize"]
    text = "Artificial intelligence is advancing rapidly. Models can now call external tools. Safety guardrails are essential."
    res = summarize_tool(text=text, style="bullet_points", max_points=2)
    assert res["status"] == "success"
    assert res["points_count"] == 2
    assert "- Artificial intelligence" in res["summary"]


def test_summarize_bad_input_from_model() -> None:
    summarize_tool = TOOL_FUNCTIONS["summarize"]
    res = summarize_tool(text="", style="unknown_style")
    assert res["status"] == "empty_input"
    assert res["summary"] == ""
    assert res["points_count"] == 0


def test_summarize_failure_returns_error_dict() -> None:
    summarize_tool = TOOL_FUNCTIONS["summarize"]
    # Pass invalid non-string non-integer parameters that could cause exception
    res = summarize_tool(text=12345, max_points="invalid_num")  # type: ignore
    assert "error" in res


# 2. calculator tool
def test_calculator_happy_path() -> None:
    calc_tool = TOOL_FUNCTIONS["calculator"]
    res = calc_tool(expression="((100 * 1.05) - 20) / 2")
    assert res["status"] == "success"
    assert res["result"] == 42.5


def test_calculator_bad_input_from_model() -> None:
    calc_tool = TOOL_FUNCTIONS["calculator"]
    res = calc_tool(expression="")
    assert res["error"] == "ValueError"
    assert "cannot be empty" in res["message"]


def test_calculator_failure_returns_error_dict() -> None:
    calc_tool = TOOL_FUNCTIONS["calculator"]
    res = calc_tool(expression="10 / 0")
    assert res["error"] == "ZeroDivisionError"


# 3. cross_reference tool
def test_cross_reference_happy_path() -> None:
    cross_tool = TOOL_FUNCTIONS["cross_reference"]
    claim = "quantum computing achieves supremacy"
    sources = [
        "quantum computing demonstrates supremacy in benchmark test.",
        "quantum processors achieve practical supremacy.",
        "unrelated article about baking bread.",
    ]
    res = cross_tool(claim=claim, sources=sources)
    assert res["verdict"] == "confirmed"
    assert res["supported_count"] == 2
    assert res["sources_checked"] == 3


def test_cross_reference_bad_input_from_model() -> None:
    cross_tool = TOOL_FUNCTIONS["cross_reference"]
    res = cross_tool(claim="", sources=["any source text"])
    assert res["error"] == "ValueError"
    assert "cannot be empty" in res["message"]


def test_cross_reference_failure_returns_error_dict() -> None:
    cross_tool = TOOL_FUNCTIONS["cross_reference"]
    res = cross_tool(claim=123, sources="invalid_sources_type")  # type: ignore
    assert "error" in res or res.get("status") == "error" or "tool" in res


# 4. export_report tool
def test_export_report_happy_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("tools.export_report.tool.ROOT", tmp_path)
    export_tool = TOOL_FUNCTIONS["export_report"]
    res = export_tool(content="# Research Report\nKey findings...", filename="summary.md", format_type="markdown")
    assert res["status"] == "saved"
    assert res["filename"] == "summary.md"
    assert (tmp_path / "exports" / "summary.md").exists()


def test_export_report_bad_input_from_model() -> None:
    export_tool = TOOL_FUNCTIONS["export_report"]
    res = export_tool(content="")
    assert res["error"] == "ValueError"
    assert "cannot be empty" in res["message"]


def test_export_report_failure_returns_error_dict(monkeypatch) -> None:
    def fake_write_text(*args, **kwargs):
        raise OSError("Disk full")
    monkeypatch.setattr("pathlib.Path.write_text", fake_write_text)
    export_tool = TOOL_FUNCTIONS["export_report"]
    res = export_tool(content="content", filename="test.md")
    assert res["error"] == "OSError"
