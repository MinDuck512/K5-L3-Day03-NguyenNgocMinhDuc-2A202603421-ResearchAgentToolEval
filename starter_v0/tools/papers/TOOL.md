---
name: papers
track: bonus
kind: live_api
provider: arXiv API
requires_env: []
inputs: [query, max_results, sort_by]
outputs: [items, total_results]
side_effect: false
---
# papers

Searches arXiv via the official Atom API. Rate-limited (waits ~3s between
in-process requests).
`ARXIV_USER_AGENT` is optional. Empty queries, invalid sort enums and result counts
outside 1–10 return an error dictionary before making a request.
