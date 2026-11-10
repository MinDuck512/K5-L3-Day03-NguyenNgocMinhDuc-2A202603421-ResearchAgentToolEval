# Day 03 — Research Desk: báo cáo theo bằng chứng


## PHẦN A — Giới thiệu agent

### A1. Công dụng và link dùng thử

Research Desk tìm tin web, bài X/Twitter, paper arXiv và policy nội bộ; đọc URL rồi tổng hợp có nguồn. Agent hỏi lại khi thiếu dữ kiện và yêu cầu người dùng xem, xác nhận chính xác nội dung trước khi gửi Telegram.

- UI cục bộ: http://localhost:8501 (chỉ dùng trên máy đang chạy ứng dụng).
- Chạy UI: `python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false`.
- Link public: chưa tạo; localhost chưa đáp ứng việc team khác truy cập từ máy khác.
- Tab **Kiểm tra nguồn** chạy offline. Chat cần provider/tool API còn quota; không dùng câu trả lời dựng sẵn khi API lỗi.

### A2. Công cụ

| Tool | Công dụng | Nguồn |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xin xác nhận; chờ người dùng. | Có sẵn |
| timeline | Lấy bài X/Twitter do một tài khoản đăng. | Có sẵn |
| social_search | Tìm bài X/Twitter theo chủ đề, Top/Latest. | Có sẵn |
| lookup | Tìm thông tin/tin tức web qua Tavily. | Có sẵn |
| fetch | Đọc một URL qua Firecrawl. | Có sẵn |
| format | Trình bày các item đã có, giữ link nguồn. | Có sẵn |
| send | Gửi Telegram sau thao tác xác nhận cụ thể. | Có sẵn; đã sửa guardrail |
| policy | Tra handbook nội bộ giả lập có sẵn trong lab. | Có sẵn |
| papers | Tìm paper arXiv theo chủ đề. | Có sẵn |
| paper_text | Đọc PDF arXiv xác định, trích text tại máy. | Có sẵn |
| source_audit | Kiểm tra link thiếu/trùng và số tên miền; không xác minh fact. | Mới tự viết |

### A3. Câu hỏi mẫu

1. Tin AI hôm nay có gì nổi bật trên web và Twitter?
2. Lấy 3 tweet mới nhất của @karpathy.
3. Tóm tắt link: https://www.anthropic.com/research
4. Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?
5. Kiểm tra link trùng trong `[{"url":"https://example.com/a"},{"url":"https://example.com/a#x"}]`.

## PHẦN B — Chi tiết và bằng chứng

### B1. Các phiên bản v0–v6

Bảng chính chỉ so model `openrouter/nvidia/nemotron-3.5-lightning:free`. V4–v6 là các thí nghiệm cloud bổ sung theo yêu cầu; không thay thế bonus local v4-local/v5-local. Snapshot đã chuẩn bị không đồng nghĩa thí nghiệm đã hoàn thành.

| Version | Giả thuyết | Trạng thái | PASS / coverage | Routing | Args | Multi | Run JSON |
|---|---|---|---|---|---|---|---|
| v0 | Baseline starter | Đã đo đủ | 12/20 đã đo; coverage 20/20 | 0.75 | 0.6 | 0.6667 | runs/v0_B_base_openrouter_20261110T124056248410.json |
| v1 | Clarify essential missing information instead of guessing. | Đã đo đủ | 13/20 đã đo; coverage 20/20 | 0.9 | 0.65 | 0.6667 | runs/v1_B_base_openrouter_20261110T124451769886.json |
| v2 | An explicit yes/no confirmation boundary prevents premature publishing. | Chưa đủ: provider bị giới hạn | 7/10 đã đo; coverage 10/20 | 0.8 | 0.7 | None | runs/v2_B_base_openrouter_20261110T151958121676.json |
| v3 | Allowing all independent tool calls removes the forced single-tool bottleneck. | Đã chuẩn bị; chưa đo | — | — | — | — | — |
| v4 | Explicit tool descriptions and argument conventions improve routing and argument precision. | Đã chuẩn bị; chưa đo | — | — | — | — | — |
| v5 | An explicit task-state routing procedure resolves corrections and task boundaries. | Đã chuẩn bị; chưa đo | — | — | — | — | — |
| v6 | A dedicated source_audit tool handles supplied-source checks without unnecessary retrieval. | Đã chuẩn bị; chưa đo | — | — | — | — | — |

`artifacts/version_log.csv` ghi run thật; giả thuyết và trạng thái các bản chưa chạy nằm trong bảng trên. Hash prompt/tools nằm trong run JSON và version_log. V2 giữ nội dung schema giống v1 nhưng có đổi newline khi lưu snapshot, vì vậy tools_hash khác; không coi đây là cải tiến schema. Các bản từ v2 dùng code tool đã sửa; bộ đề base và hàm chấm không đổi. Giãn cách/retry khác các run cũ được lưu trong execution, nên không khẳng định mọi khác biệt điểm đều do prompt.

Lịch sử OpenRouter: v0 12/20; v1 13/20. V2 đang có 7/10 case đã đo, coverage 10/20. Run thiếu coverage không chứng minh chất lượng trên cả suite. Thư mục runs giữ cả log lịch sử Gemini và lần retry để bảo toàn bằng chứng; chúng không được dùng để so sánh chất lượng với baseline OpenRouter đầy đủ.

### B2. Phân tích lỗi

CSV phân loại lỗi: `analysis/all_failures.csv`. Bảng từng case của mọi run: `analysis/all_runs.csv`. Đọc thêm actual_tool_calls và tool_results trong run JSON khi cần chi tiết.
Ghi chú thiết lập và phân tích trước đây được giữ tại `analysis/history/`; các kết luận cần cho bài nộp đã được tập trung trong báo cáo này.

- V1 có bốn case chuyển FAIL → PASS: R08, R10, R11, M02; ba case chuyển PASS → FAIL: R01, R09, M03. Hai case mục tiêu thiếu dữ kiện R10/R11 được sửa. Tổng tăng 5 điểm phần trăm từ một lần đo, chưa chứng minh độ ổn định.
- Chấm args dùng subset và chuỗi chính xác sau strip/lower. Query "AI news today" khác "AI" vẫn FAIL; giữ nguyên phép chấm, hướng dẫn tách query/topic/timeframe ở v4.
- V2 kiểm tra xác nhận gửi; R12 chưa được đo vì quota đã hết; chưa kiểm chứng giả thuyết chính.
- Routing PASS không chứng minh tool/API thực thi thành công. Các error dict được thống kê riêng bên dưới; source_audit chỉ kiểm tra cấu trúc URL, không xác minh sự thật hoặc tính độc lập nguồn.

| Version | Case | Tool | Lỗi thực thi |
|---|---|---|---|
| v1 | R09_no_tool_capability | send | RuntimeError |
| v1 | M03_correction_handle | timeline | JSONDecodeError |

### B3. Bộ eval nhóm

Đúng 10 case mới: 5 single-turn + 5 multi-turn; G01/GM04 kiểm tra route đến source_audit. Đã kiểm tra contract offline; chưa có run thì ghi Chưa đo.

| ID | Loại | Nội dung kiểm tra | Kỳ vọng | Kết quả |
|---|---|---|---|---|
| G01_audit_supplied_sources | single | Nguồn đã có -> source_audit, không lookup/fetch. | source_audit | Chưa đo |
| G02_social_top_limit | single | Trích chủ đề, Top đúng chữ hoa và limit=4. | social_search | Chưa đo |
| G03_preserve_url | single | Bảo toàn query string của URL người dùng. | fetch | Chưa đo |
| G04_privacy_policy | single | Nội quy công ty -> local policy, không tìm web. | policy | Chưa đo |
| G05_send_requires_confirmation | single | Yêu cầu gửi ban đầu chưa phải xác nhận. | clarify | Chưa đo |
| GM01_correct_subject | multi | Thay topic, giữ news/week, không lặp task cũ. | lookup | Chưa đo |
| GM02_format_correct_template | multi | Dữ liệu đã có, đổi template theo lượt mới nhất. | format | Chưa đo |
| GM03_cancel_send | multi | Hủy action và câu meta -> không tool, không gửi. | no_tool | Chưa đo |
| GM04_audit_carry_sources | multi | Giữ sources trong hội thoại, audit local, không mạng. | source_audit | Chưa đo |
| GM05_correct_url | multi | URL sửa sau ghi đè URL trước, không fetch cả hai. | fetch | Chưa đo |

### B4. Live chat

| Transcript | Lượt | Yêu cầu | Tools | Trạng thái |
|---|---|---|---|---|
| transcripts/v6_openrouter_ui_20261110T152858_bb84e7eb.transcript.json | 1 | hôm nay là ngày bao nhiêu |  | provider_error |

Đủ ≥3 lượt thành công trong cùng transcript: **Chưa**. Chạy `python chat.py --provider openrouter --model nvidia/nemotron-3.5-lightning:free --version v6` để ghi phiên live với provider/tool thật; nhập `/exit` khi kết thúc.

### B5. Code, UI và unit test

- Pytest: **148 tests; 0 failed; 0 errors; 0 skipped** (`analysis/pytest.xml`).
- Thay toàn bộ 17 stub skip bằng test thật; source_audit có happy path, input xấu, lỗi vận hành và regression URL; mọi HTTP trong unit test đều được mock.
- Bug bắt được bằng unit test: `confirmed="false"` trước đây là truthy nên có thể gửi; nay chỉ nhận boolean True và UI/CLI cần thao tác xác nhận riêng. Eval luôn vô hiệu hóa gửi thật.
- `limit=0`, `top_k=0`, `max_results=0` trước đây bị đổi sang mặc định; nay trả ValueError, số dạng chuỗi nguyên được chấp nhận. Enum sai, URL/handle sai và items sai kiểu được kiểm tra trước mạng.
- `send` chỉ báo sent khi Telegram trả ok=true; gửi text literal để tránh lỗi Markdown; token trong thông báo lỗi được che.
- `paper_text` kiểm tra URL arXiv đúng host và giới hạn trang/ký tự trước tải; test happy path đọc/ghi text là offline.
- Loop trả kết quả sau format, giữ bằng chứng qua các lượt và có giới hạn số vòng. Eval lưu checkpoint mỗi case, resume chỉ retry lỗi provider và từ chối nếu artifact/dataset khác.
- UI dùng cùng loop với CLI; tab offline được kiểm tra bằng Streamlit AppTest (`tests/test_app.py`). Bảng Markdown tránh DLL pyarrow bị Windows Application Control chặn. Không tắt hay thay đổi chính sách Windows. Kiểm tra trực quan qua Computer Use bị dừng vì công cụ không xác định được URL trình duyệt; không có ảnh xác nhận UI thật.
- UI localhost đã chạy. Telegram live chưa cấu hình bot/chat; không thực hiện gửi thật. Bonus hơn 3 tool mới chưa làm (hiện có 1 tool mới, đủ yêu cầu bắt buộc).

Các sửa chữa và giới hạn kiểm tra được tập trung trong mục này để tránh nhiều báo cáo trùng nhau.

### B6. Nhận xét và giới hạn

Prompt và tool description cần phân biệt tác giả/chủ đề, thời gian/query, thông tin thiếu và xác nhận hành động. Dữ liệu nhiều lượt cần áp dụng sửa đổi mới nhất thay vì lặp lại task cũ. Đây là giả thuyết thiết kế cho v3–v6 cho đến khi có đủ run để kết luận. Test offline chứng minh code hoạt động trên các tình huống đã kiểm tra; không thay thế đánh giá model/API.

Các lần chạy v2 đã gặp HTTP 429 do hạn mức provider; xem failures trong run JSON. Người dùng cho biết sẽ bổ sung hạn mức/provider trong .env. Chạy `python scripts/complete_lab.py` để đọc lại cấu hình và thu tiếp bằng chứng; nếu đổi model/provider nên thêm `--include-baselines` để có đối chứng cùng model (runner tự bổ sung nếu thiếu baseline). Sau đó chạy chat.py để có ≥3 lượt live và `python scripts/build_report.py` để cập nhật báo cáo.

### B7. Bonus Small Local Model

Ollama chưa có lệnh và localhost:11434 chưa có server/model ở lần kiểm tra. Chưa chạy hai model ≤8B, v4-local/v5-local hoặc kiểm tra ngược trên cloud; không ghi kết quả giả. Cần cài/chuẩn bị Ollama và hai model phù hợp nếu muốn hoàn thành bonus này. Không tải model nhiều GB khi chưa có lựa chọn của người dùng.

## Trạng thái bàn giao

- Prompt/schema và code v1–v6: đã chuẩn bị, có snapshot và giả thuyết.
- Eval bắt buộc v1–v3 đo đủ: **Chưa đủ**; v1–v6 đo đủ: **Chưa đủ**.
- Unit test 0 failed/0 skipped: **Đạt**.
- Còn phụ thuộc bên ngoài: quota/provider live; link public; Telegram live và local models nếu làm bonus.
- `.env`, thư mục `.venv` và cache không được đưa vào bài nộp. Giữ chúng tại máy nếu cần để chạy; nộp code, artifacts, data, tests, runs, transcripts và analysis.

## Tài liệu kỹ thuật đã đối chiếu

- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search): query/topic/time_range/max_results.
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest): kiểm tra UI offline.
- [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits): kiểm tra quyền truy cập/hạn mức; lỗi provider thực tế nằm trong run JSON.
