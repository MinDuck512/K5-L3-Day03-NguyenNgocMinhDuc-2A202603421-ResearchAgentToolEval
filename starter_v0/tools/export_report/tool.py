from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err


def export_research_report(content: str = "", filename: str = "", format_type: str = "markdown") -> dict[str, Any]:
    try:
        if not content or not content.strip():
            return {"tool": "export_report", "error": "ValueError", "message": "Content cannot be empty"}
        export_dir = ROOT / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        base_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", filename or "research_brief")
        valid_exts = (".md", ".txt", ".html", ".json")
        if not any(base_name.endswith(ext) for ext in valid_exts):
            ext = ".html" if format_type == "html" else (".json" if format_type == "json" else ".md")
            base_name += ext

        out_path = export_dir / base_name
        out_path.write_text(content, encoding="utf-8")
        return {
            "tool": "export_report",
            "status": "saved",
            "filename": base_name,
            "path": str(out_path),
            "size_bytes": len(content.encode("utf-8")),
        }
    except Exception as exc:
        return err("export_report", exc)

