from __future__ import annotations

import re
import os
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30


def err(tool: str, exc: Exception) -> dict[str, Any]:
    message = str(exc)
    for name, value in os.environ.items():
        if value and any(marker in name.upper() for marker in ("API_KEY", "TOKEN", "SECRET")):
            message = message.replace(value, "[REDACTED]")
    return {"tool": tool, "error": type(exc).__name__, "message": message}


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to",
        "ban", "bao", "can", "cho", "co", "cua", "duoc", "gi", "giup", "la", "lam", "minh", "mot", "nay",
        "nen", "the", "thi", "trong", "va", "ve", "voi",
    }
    folded = fold_text(text)
    return {term for term in re.findall(r"[a-z0-9]+", folded) if len(term) > 1 and term not in stopwords}


def bounded_int(value: Any, name: str, minimum: int = 1, maximum: int = 100) -> int:
    """Accept integer strings from models, but never truncate floats or replace zero."""
    if isinstance(value, bool) or not re.fullmatch(r"[+-]?\d+", str(value).strip()):
        raise ValueError(f"{name} must be an integer")
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return number


def nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value.strip()


def http_url(value: Any) -> str:
    value = nonempty(value, "url")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("url must be an HTTP(S) URL without credentials")
    try:
        parsed.port
    except ValueError:
        raise ValueError("url has an invalid port") from None
    return value

