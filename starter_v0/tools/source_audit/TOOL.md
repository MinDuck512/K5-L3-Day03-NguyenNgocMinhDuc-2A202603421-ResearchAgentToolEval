---
name: source_audit
track: bonus
kind: local_formatter
provider: local
requires_env: []
inputs: [items]
outputs: [items, issues, input_count, unique_count, domain_count, limitation]
side_effect: false
requires_confirmation: false
---

# Source audit

Use when the user asks to audit already supplied sources, identify missing links,
count source domains, or remove duplicate URLs before a digest. Do not use for
source discovery, fact checking, or fetching page contents.

`items` must be a list of at most 500 objects. Invalid/missing URLs become issues;
invalid object types return an error dictionary. Removes fragments and tracking
query parameters, normalizes host case and default ports, and preserves meaningful
query parameters and path case. Returns the first occurrence of each URL.
Domain count does not establish editorial independence. No network or file writes.
