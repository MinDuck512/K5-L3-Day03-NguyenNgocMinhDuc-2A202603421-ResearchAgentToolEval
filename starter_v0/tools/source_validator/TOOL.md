---
name: source_validator
track: core
kind: local_formatter
provider: none
requires_env: []
inputs: [url, title, author]
outputs: [valid, url, domain, category, missing_metadata, citation_complete, note]
side_effect: false
---
# source_validator

Checks HTTP(S) URL syntax and required citation metadata, and classifies the domain.
Does not fetch URLs or establish factual reliability. Invalid inputs return an error dict.
