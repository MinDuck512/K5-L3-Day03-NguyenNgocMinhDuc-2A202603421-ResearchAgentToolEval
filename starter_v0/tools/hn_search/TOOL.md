---
name: hn_search
track: bonus
kind: live_api
provider: Algolia Hacker News API
requires_env: []
inputs: [query, tags, sort_by, limit]
outputs: [items]
side_effect: false
---
# hn_search

Searches Hacker News stories, Ask HN, Show HN, and comments via the public Algolia HN Search API (no API key required).

