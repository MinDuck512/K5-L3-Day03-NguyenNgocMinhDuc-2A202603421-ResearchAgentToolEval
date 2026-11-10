---
name: paper_text
track: bonus
kind: live_api
provider: arXiv + pypdf
requires_env: []
inputs: [arxiv_url, max_pages, max_chars]
outputs: [items, pdf_path, txt_path, page_count]
side_effect: local_file_write
---
# paper_text

Downloads an arXiv PDF and extracts text locally with `pypdf`. Output is saved
under `starter_v0/arxiv_papers/`.
`ARXIV_USER_AGENT` is optional. `max_pages` accepts 1–100 and `max_chars` 1–20000;
zero is rejected. Only modern arXiv IDs or actual arxiv.org abs/pdf URLs are accepted.
