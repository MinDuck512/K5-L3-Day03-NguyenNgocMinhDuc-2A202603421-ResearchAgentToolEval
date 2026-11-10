---
name: export_report
track: custom
kind: pure_local
provider: Local
requires_env: []
inputs: [content, filename, format_type]
outputs: [status, filename, path, size_bytes]
side_effect: true
---
# export_report

Saves research digests, findings, and analysis reports to the exports/ directory.

