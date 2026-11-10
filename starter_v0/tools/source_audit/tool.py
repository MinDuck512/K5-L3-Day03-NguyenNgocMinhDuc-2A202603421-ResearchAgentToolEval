"""Audit citation completeness and duplicate URLs locally; never verifies truth."""
from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tools._shared import err, http_url


def audit_sources(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list of source objects")
        if len(items) > 500:
            raise ValueError("At most 500 sources per audit")
        seen: dict[str, int] = {}
        unique: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []
        hosts: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"items[{index}] must be an object")
            try:
                url = http_url(item.get("url"))
            except ValueError:
                issues.append({"index": index, "issue": "missing_or_invalid_url"})
                continue
            parts = urlsplit(url)
            host = (parts.hostname or "").lower().removeprefix("www.")
            port = parts.port
            if port is not None and (parts.scheme, port) not in {("https", 443), ("http", 80)}:
                host += f":{port}"
            query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                           if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"})
            canonical = urlunsplit((parts.scheme.lower(), host, parts.path or "/", urlencode(query), ""))
            if canonical in seen:
                issues.append({"index": index, "issue": "duplicate_url", "duplicate_of": seen[canonical]})
                continue
            seen[canonical] = index
            hosts.add(host)
            unique.append({**item, "url": canonical})
        return {
            "tool": "source_audit", "input_count": len(items), "unique_count": len(unique),
            "domain_count": len(hosts), "items": unique, "issues": issues,
            "limitation": "Checks URL completeness and duplicates only; does not verify claims, freshness or independent ownership.",
        }
    except Exception as exc:
        return err("source_audit", exc)
