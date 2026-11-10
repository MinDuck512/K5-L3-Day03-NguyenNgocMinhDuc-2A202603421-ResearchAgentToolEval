from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err, http_url


def read_url(url: str = "") -> dict[str, Any]:
    try:
        url = http_url(url)
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            raise RuntimeError("Missing FIRECRAWL_API_KEY env var")
        response = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") is False:
            raise RuntimeError("Firecrawl reported an unsuccessful scrape")
        data = payload.get("data", {})
        meta = data.get("metadata", {}) or {}
        return {"tool": "read_url", "url": url, "items": [{
            "title": meta.get("title") or url,
            "url": meta.get("sourceURL") or url,
            "source": domain(url),
            "summary": (data.get("markdown") or "")[:4000],
        }]}
    except Exception as exc:
        return err("read_url", exc)

