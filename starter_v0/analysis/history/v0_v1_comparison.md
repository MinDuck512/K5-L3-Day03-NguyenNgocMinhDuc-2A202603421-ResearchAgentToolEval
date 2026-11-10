# So sánh v0–v1 trên cùng model OpenRouter

Model: `nvidia/nemotron-3.5-lightning:free`. Cùng tập base 20 case, tool declarations và cấu hình chạy (interval 4s; max retries 1; delay 10s; max wait 30s). Hai lần đều đo đủ 20 case và không có provider_error.

Thay đổi duy nhất của v1: thay một đoạn system prompt khuyến khích đoán account/URL bằng quy tắc gọi clarify khi thiếu dữ kiện trong cả yêu cầu hiện tại lẫn lịch sử hội thoại.

| Metric | v0 | v1 |
|---|---:|---:|
| case_accuracy | 0.6 | 0.65 |
| tool_routing_accuracy | 0.75 | 0.9 |
| argument_accuracy | 0.6 | 0.65 |
| multiturn_accuracy | 0.6667 | 0.6667 |
| measured_cases | 20 | 20 |
| provider_error_cases | 0 | 0 |

Case accuracy tăng 0.60 → 0.65, tức +5 điểm phần trăm. Hai case mục tiêu R10/R11 đã PASS. Đây là bằng chứng từ một lần chạy mỗi version; chưa khẳng định mọi thay đổi ở các case khác đều do riêng quy tắc hỏi lại.

## Các case đổi trạng thái

| Case | v0 | v1 | Actual calls v1 |
|---|---|---|---|
| R08_out_of_scope | FAIL | PASS | `[]` |
| R10_missing_handle | FAIL | PASS | `[{"name": "clarify", "args": {"question": "Which account's latest 5 tweets would you like me to summarize? Please provide the Twitter (X) handle.", "response_type": "text"}}]` |
| R11_missing_url | FAIL | PASS | `[{"name": "clarify", "args": {"question": "Bạn có thể cung cấp đường link (URL) hoặc nội dung bài viết bạn muốn tóm tắt không?", "response_type": "text"}}]` |
| M02_carryover_timeframe | FAIL | PASS | `[{"name": "lookup", "args": {"query": "robotics", "topic": "news", "timeframe": "day", "max_results": 5}}]` |
| R01_user_tweets_routing | PASS | FAIL | `[{"name": "social_search", "args": {"query": "Sam Altman", "search_type": "Latest", "limit": 1}}]` |
| R09_no_tool_capability | PASS | FAIL | `[{"name": "send", "args": {"text": "Bạn có thể gọi tôi Nemotron, và tôi đã được huấn luyện bởi NVIDIA như một mô hình ngôn ngữ. Tôi có thể giúp bạn với nhiều nhiệm vụ khác nhau, chẳng hạn như trả lời câu hỏi, sáng tạo nội dung, viết mã, tóm tắt tài liệu, tra cứu thông tin và nhiều hơn nữa. Tôi cũng có thể sử dụng các công cụ để tìm kiếm dữ liệu mới, phân tích trang web hoặc tổng hợp các bài viết gần đây. Chỉ cần cho tôi biết bạn cần gì, tôi sẽ làm ngay!", "confirmed": true}}]` |
| M03_correction_handle | PASS | FAIL | `[{"name": "timeline", "args": {"screenname": "Andrej Karpathy", "limit": 3}}]` |

## Các lỗi còn lại cần xử lý riêng

- R01: dùng social_search cho bài đăng của một tài khoản, thay vì timeline.
- R03: dùng đúng lookup nhưng query mở rộng không khớp chính xác chuỗi mà bộ chấm yêu cầu; cần ghi nhận giới hạn phép chấm.
- R09: gọi send cho câu hỏi giới thiệu khả năng. Tool trả lỗi do chưa cấu hình Telegram; không có bài đăng thật. Cần sửa ranh giới hành động gửi và làm rõ send chỉ dành cho Telegram theo yêu cầu/xác nhận của người dùng.
- R12: agent đã hỏi xin nội dung bằng clarify(text); bộ chấm đòi clarify(yes_no). Cần phân biệt hành vi hỏi lại có ích và việc khớp chính xác convention trong eval khi phân tích thủ công.
- R13: đã gọi cả lookup và social_search nhưng query/topic của lookup chưa đúng convention.
- M03: truyền tên hiển thị Andrej Karpathy vào screenname thay vì handle; tool cũng trả JSONDecodeError.
- M05: không áp dụng sửa số lượng 10 → 3 trong hội thoại.

Tool execution errors của v1: R09/send RuntimeError; M03/timeline JSONDecodeError. PASS/FAIL eval của model không thay thế việc đọc kết quả thực thi tool.

## Hạn mức và bước tiếp theo

Lần kiểm tra sau v1: còn 10/50 request miễn phí, chưa đủ chạy trọn v2 (20 case). Giữ cùng model và lấy thêm quota hợp lệ khi được phép trước khi chạy v2/v3. Trong lúc chờ, triển khai tool mới + unit tests, 10 group eval case và UI.

Đề xuất một giả thuyết riêng cho v2: sửa chỉ dẫn gửi ngay thành quy tắc chỉ dùng send khi có yêu cầu đăng Telegram và xác nhận rõ ràng; đo tác động lên R09/R12. Chưa sửa prompt hay chạy v2.

## Bằng chứng

- V0: `runs/v0_B_base_openrouter_20261110T124056248410.json`.
- V1: `runs/v1_B_base_openrouter_20261110T124451769886.json`.
- Hash tools giống nhau; prompt hashes tương ứng snapshot v0/v1.
