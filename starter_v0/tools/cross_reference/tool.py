from __future__ import annotations

from typing import Any

from tools._shared import err, terms


def cross_reference_claims(claim: str = "", sources: list[str] | None = None) -> dict[str, Any]:
    try:
        clean_claim = (claim or "").strip()
        if not clean_claim:
            return {"tool": "cross_reference", "error": "ValueError", "message": "Claim cannot be empty"}
        source_list = sources or []
        claim_set = terms(clean_claim)
        findings = []
        supported_count = 0
        for idx, src in enumerate(source_list):
            src_set = terms(src or "")
            overlap = claim_set & src_set
            ratio = len(overlap) / max(1, len(claim_set))
            is_supported = ratio >= 0.35
            if is_supported:
                supported_count += 1
            findings.append({
                "source_index": idx,
                "overlap_terms": sorted(list(overlap)),
                "overlap_ratio": round(ratio, 2),
                "supported": is_supported,
            })
        verdict = "confirmed" if supported_count >= 2 else ("corroborated" if supported_count == 1 else "unverified")
        return {
            "tool": "cross_reference",
            "claim": clean_claim,
            "sources_checked": len(source_list),
            "supported_count": supported_count,
            "verdict": verdict,
            "findings": findings,
        }
    except Exception as exc:
        return err("cross_reference", exc)

