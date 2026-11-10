from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"
ALLOWED_TAGS = {"story", "comment", "ask_hn", "show_hn", "all"}


def _hn_item(raw: dict[str, Any]) -> dict[str, Any]:
    object_id = str(raw.get("objectID") or "").strip()
    hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
    url = (raw.get("url") or "").strip() or hn_url
    title = (raw.get("title") or raw.get("story_title") or "").strip()
    text = (raw.get("comment_text") or raw.get("story_text") or "").strip()
    points = raw.get("points")
    comments = raw.get("num_comments")
    if not text:
        meta_parts = []
        if points is not None:
            meta_parts.append(f"{points} points")
        if comments is not None:
            meta_parts.append(f"{comments} comments")
        if raw.get("author"):
            meta_parts.append(f"by {raw['author']}")
        text = ", ".join(meta_parts) or title
    return {
        "title": title or text[:120],
        "url": url,
        "hn_url": hn_url,
        "source": domain(url) or "news.ycombinator.com",
        "summary": text[:500],
        "author": raw.get("author"),
        "points": points,
        "num_comments": comments,
        "created_at": raw.get("created_at"),
    }


def search_hacker_news(
    query: str = "",
    tags: str = "story",
    sort_by: str = "relevance",
    limit: int = 5,
) -> dict[str, Any]:
    """Search Hacker News discussions and stories using the Algolia HN API."""
    try:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        cleaned_query = query.strip()
        if not cleaned_query:
            return {
                "tool": "search_hacker_news",
                "query": query,
                "tags": tags,
                "sort_by": sort_by,
                "items": [],
            }

        normalized_tags = (tags or "story").strip().lower()
        if normalized_tags not in ALLOWED_TAGS:
            normalized_tags = "story"

        parsed_limit = 5 if limit is None else int(limit)
        if parsed_limit <= 0:
            return {
                "tool": "search_hacker_news",
                "query": cleaned_query,
                "tags": normalized_tags,
                "sort_by": sort_by,
                "items": [],
            }
        bounded_limit = min(parsed_limit, 20)

        endpoint = HN_SEARCH_BY_DATE_URL if sort_by == "date" else HN_SEARCH_URL
        params: dict[str, Any] = {"query": cleaned_query, "hitsPerPage": bounded_limit}
        if normalized_tags != "all":
            params["tags"] = normalized_tags

        response = requests.get(endpoint, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        hits = response.json().get("hits") or []
        items = [_hn_item(hit) for hit in hits[:bounded_limit]]
        return {
            "tool": "search_hacker_news",
            "query": cleaned_query,
            "tags": normalized_tags,
            "sort_by": "date" if sort_by == "date" else "relevance",
            "items": items,
        }
    except Exception as exc:
        return err("search_hacker_news", exc)

