# Đối chiếu TODO — 10/11/2026

Trạng thái được dựng từ file thật; chưa đo không được đánh dấu hoàn thành.

| Yêu cầu | Trạng thái | Bằng chứng |
|---|---|---|
| Provider và preflight | Đã có lịch sử PASS; run v2 gặp quota | scripts/preflight_provider.py; runs/v2*.json |
| Baseline và phân loại lỗi | Đạt | v0/v1 JSON; analysis/all_failures.csv |
| Bỏ chỉ dẫn xấu, routing, descriptions/args | Đạt về artifact; chờ eval đầy đủ | artifacts/versions/v2–v6 |
| v1/v2/v3 một giả thuyết + metric thật | Chưa đủ | version_log.csv; không lấy 7/10 làm 7/20 |
| v4/v5/v6 theo yêu cầu bổ sung | Đã chuẩn bị; chưa đo đủ | artifacts/REPORT.md B1; artifacts/versions/ |
| Tool mới + TOOL.md + registry + schema | Đạt: source_audit | tools/source_audit; artifacts/tools.yaml |
| ≥3 tests/tool mới; tất cả TODO stubs | Đạt | tests/test_tools_todo.py; analysis/pytest.xml |
| 10 group case, 5 single + 5 multi | Đã viết; chưa đo live | data/eval_group.json |
| Pytest 0 failed, 0 skipped | Đạt | {'tests': 148, 'failures': 0, 'errors': 0, 'skipped': 0} |
| UI Streamlit + link | Local đã chạy; public chưa tạo | http://localhost:8501; tests/test_app.py |
| Chat live ≥3 lượt + transcript | Chưa đủ bằng chứng | chat.py; transcripts/ |
| REPORT A/B | Đã điền trạng thái thật; số liệu còn chờ quota | artifacts/REPORT.md |
| Bonus send confirmation | Code + mock tests đạt; Telegram live chưa cấu hình | tests/test_chat.py; tools/send |
| Bonus hơn 3 tool mới | Chưa làm; không bắt buộc | Hiện có 1 tool mới |
| Bonus 2 model local + tối ưu | Chưa có Ollama/server/model | REPORT B7 |

Tiếp tục: `python scripts/complete_lab.py` → `python chat.py --provider openrouter --model nvidia/nemotron-3.5-lightning:free --version v6` (ít nhất 3 lượt) → `python scripts/parse_runs.py runs/ --output analysis/all_runs.csv` → `python scripts/build_report.py`.
