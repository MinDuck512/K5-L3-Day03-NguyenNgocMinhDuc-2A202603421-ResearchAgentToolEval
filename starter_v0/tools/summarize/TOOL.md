---
name: summarize
track: custom
kind: pure_local
provider: Local
requires_env: []
inputs: [text, style, max_points]
outputs: [status, summary, points_count]
side_effect: false
---
# summarize

Extracts key takeaways and summaries from article text or search results.
Supports bullet_points, numbered lists, or paragraph style.

