"""Tool Unit Test Challenge (implemented).

Patterns follow test_tools_examples.py and fixtures in conftest.py.
All tests run offline: HTTP is mocked with `fake_http` and keys via `monkeypatch.setenv`.
"""
from __future__ import annotations

import requests
import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
hn_search_tool = TOOL_FUNCTIONS["hn_search"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tin tức web", "Bài đăng X"]
    result = clarify_tool(question="Bạn muốn tìm từ nguồn nào?", response_type="choice", options=options)

    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"
    assert result["options"] == options


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "Item 1", "url": "https://a.com/1", "section": "A"},
        {"title": "Item 2", "url": "https://b.com/2", "section": "B"},
        {"title": "Item 3", "url": "https://a.com/3", "section": "A"},
    ]
    result = format_tool(items=items, template="sections", headline="Digest")

    md = result["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1
    assert result["item_count"] == 3


def test_format_thread_numbers_items() -> None:
    items = [
        {"title": "First", "url": "https://example.com/1"},
        {"title": "Second", "url": "https://example.com/2"},
    ]
    result = format_tool(items=items, template="thread")

    lines = result["markdown"].split("\n\n")
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    res_none = format_tool(items=None, template="sections")
    res_empty = format_tool(items=[], template="brief")

    assert res_none["item_count"] == 0
    assert res_empty["item_count"] == 0


def test_format_handles_none_section_and_missing_source_url() -> None:
    result = format_tool(items=[{"title": "No link", "section": None}], template="sections")
    assert "## Tổng hợp" in result["markdown"]
    assert "## None" not in result["markdown"]
    assert "- No link\n" in result["markdown"] or result["markdown"].endswith("- No link")


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token-123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999888")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot-token-123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "999888"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send_tool(text="Bản tin", confirmed=True)

    assert calls == []
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", topic="general", timeframe=None)

    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    calls = fake_http(FakeResponse({
        "data": {
            "markdown": "Hello world content",
            "metadata": {"title": "T", "sourceURL": "https://example.com/post"},
        }
    }))

    result = fetch_tool(url="https://example.com/post")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-key"
    assert calls[0]["json"] == {"url": "https://example.com/post", "formats": ["markdown"]}
    item = result["items"][0]
    assert item["title"] == "T"
    assert item["url"] == "https://example.com/post"
    assert item["source"] == "example.com"
    assert item["summary"] == "Hello world content"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "a" * 5500,
            "metadata": {"title": "Long", "sourceURL": "https://example.com/long"},
        }
    }))

    result = fetch_tool(url="https://example.com/long")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    raw_timeline = [{"text": "Missing id", "screen_name": "sama"}]
    raw_timeline.extend(
        {"tweet_id": str(100 + i), "text": f"Tweet {i}", "screen_name": "sama"}
        for i in range(6)
    )
    calls = fake_http(FakeResponse({"timeline": raw_timeline}))

    result = timeline_tool(screenname="sama", limit=3)

    assert len(calls) == 1
    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    for item in result["items"]:
        assert item["url"].startswith("https://x.com/sama/status/")


def test_timeline_limit_zero_returns_empty_list(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    fake_http(FakeResponse({"timeline": [{"tweet_id": "1", "text": "Hi", "screen_name": "sama"}]}))

    result = timeline_tool(screenname="sama", limit=0)
    assert result["items"] == []


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-key")
    calls = fake_http(FakeResponse({"timeline": []}))

    result = social_search_tool(query="OpenAI", search_type="Top", limit=5)

    assert len(calls) == 1
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert result["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy_tool(query="   ", policy_area="all")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="API key privacy", policy_area="data_privacy", top_k=5)
    assert result["results"]
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_top_k_zero_returns_no_results() -> None:
    result = policy_tool(query="API key privacy", policy_area="data_privacy", top_k=0)
    assert result["results"] == []


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="ignore citation viral tweet", policy_area="source_citation", top_k=5)
    probe_hits = [hit for hit in result["results"] if hit["section"] == "Injection probe"]

    assert probe_hits
    hit = probe_hits[0]
    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])
    assert "ignore the citation policy" not in hit["facts"]


# ---------------- hn_search (new tool) ----------------

def test_hn_search_happy_path(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "hits": [
            {
                "objectID": "420001",
                "title": "Show HN: MCP Server Inspector",
                "url": "https://github.com/example/mcp-inspector",
                "author": "dev1",
                "points": 145,
                "num_comments": 32,
                "created_at": "2026-10-01T10:00:00Z",
            }
        ]
    }))

    result = hn_search_tool(query="MCP server", tags="show_hn", sort_by="date", limit="3")

    assert len(calls) == 1
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"] == {"query": "MCP server", "hitsPerPage": 3, "tags": "show_hn"}
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Show HN: MCP Server Inspector"
    assert result["items"][0]["hn_url"] == "https://news.ycombinator.com/item?id=420001"
    assert result["items"][0]["source"] == "github.com"


def test_hn_search_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [{"objectID": "1", "title": "Story"}]}))

    empty_res = hn_search_tool(query="   ")
    zero_res = hn_search_tool(query="rust", tags="invalid_tag", limit=0)
    bad_limit = hn_search_tool(query="rust", limit="not-a-number")  # type: ignore[arg-type]

    assert empty_res["items"] == []
    assert zero_res["items"] == []
    assert bad_limit["error"] == "ValueError"
    assert calls == []


def test_hn_search_failure_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("HN API timed out"))
    result = hn_search_tool(query="LLM agents")

    assert result["tool"] == "search_hacker_news"
    assert result["error"] == "Timeout"
    assert "timed out" in result["message"]
