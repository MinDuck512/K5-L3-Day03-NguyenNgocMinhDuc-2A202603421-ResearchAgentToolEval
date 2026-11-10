from __future__ import annotations

from typing import Any

from tools._shared import err


def summarize_text(text: str = "", style: str = "bullet_points", max_points: int = 5) -> dict[str, Any]:
    try:
        if not text or not text.strip():
            return {"tool": "summarize", "status": "empty_input", "summary": "", "points_count": 0}
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if len(s.strip()) > 8]
        limit = max(1, min(int(max_points or 5), 20))
        selected = sentences[:limit]
        if style == "paragraph":
            summary = ". ".join(selected) + ("." if selected else "")
        elif style == "numbered":
            summary = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(selected))
        else:
            summary = "\n".join(f"- {s}" for s in selected)
        return {
            "tool": "summarize",
            "status": "success",
            "style": style,
            "points_count": len(selected),
            "summary": summary,
        }
    except Exception as exc:
        return err("summarize", exc)

