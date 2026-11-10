from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit


def validate_source(url: str = "", title: str = "", author: str = "") -> dict[str, Any]:
    """Validate citation metadata and classify source type without fetching it."""
    if not isinstance(url, str) or not url.strip():
        return {"error": "url must be a non-empty string", "valid": False}
    if not isinstance(title, str) or not isinstance(author, str):
        return {"error": "title and author must be strings", "valid": False}
    try:
        parts = urlsplit(url.strip())
        hostname = (parts.hostname or "").lower()
        if (parts.scheme not in ("http", "https") or not hostname
                or any(ch.isspace() for ch in hostname) or "." not in hostname):
            return {"error": "url must be a valid HTTP(S) URL", "valid": False}
    except ValueError:
        return {"error": "url must be a valid HTTP(S) URL", "valid": False}

    if hostname == "arxiv.org" or hostname.endswith(".arxiv.org") or hostname == "doi.org":
        category = "academic"
    elif hostname.endswith(".gov") or hostname.endswith(".gov.vn"):
        category = "government"
    elif hostname.endswith(".edu") or hostname.endswith(".edu.vn"):
        category = "education"
    else:
        category = "other"

    missing = [field for field, value in (("title", title), ("author", author)) if not value.strip()]
    return {
        "valid": True,
        "url": url.strip(),
        "domain": hostname,
        "category": category,
        "missing_metadata": missing,
        "citation_complete": not missing,
        "note": "Syntax and metadata check only; source accuracy and accessibility are not verified.",
    }
