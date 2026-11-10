from __future__ import annotations

from typing import Any

from tools._shared import err, nonempty


def ask_user(question: str = "", response_type: str = "text", options: list[str] | None = None) -> dict[str, Any]:
    try:
        question = nonempty(question, "question")
        if response_type not in {"text", "yes_no", "choice"}:
            raise ValueError("response_type must be text, yes_no or choice")
        if options is not None and (not isinstance(options, list) or any(not isinstance(option, str) for option in options)):
            raise ValueError("options must be a list of strings")
        if response_type == "choice" and len(options or []) < 2:
            raise ValueError("choice requires at least two options")
    except Exception as exc:
        return err("ask_user", exc)
    return {
        "tool": "ask_user",
        "question": question,
        "response_type": response_type,
        "options": options or [],
        "awaiting_user": True,
    }

