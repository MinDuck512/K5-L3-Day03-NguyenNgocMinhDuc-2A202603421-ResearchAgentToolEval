# Day 03 Lab v2 Report — Research Agent

## Team

- Team: Nhóm Day 03
- Members: Nguyễn Văn Tùng
- Provider/model: `openrouter` (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tra cứu thông tin đa nguồn (tin tức web, bài đăng X/Twitter, thảo luận Hacker News, bài báo arXiv, policy nội bộ), đọc nội dung URL chi tiết, hỏi lại người dùng khi thiếu tham số quan trọng, tổng hợp thành markdown digest và chỉ gửi lên Telegram khi người dùng đã xác nhận rõ ràng.

**Link dùng thử (deploy):**

> Chạy local UI bằng `streamlit run app.py` (tạo link public tạm thời qua `cloudflared tunnel --url http://localhost:8501` khi demo).
>
> URL: *(chưa mở tunnel / chưa deploy)*

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận (`text` / `yes_no` / `choice`) | không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản X/Twitter cụ thể (`screenname` không có `@`) | không |
| `social_search` | Tìm bài đăng X/Twitter theo từ khóa (`Latest` hoặc `Top`) | không |
| `lookup` | Tìm kiếm tin tức hoặc thông tin tổng quát trên web qua Tavily (`topic`, `timeframe`) | không |
| `fetch` | Đọc nội dung chi tiết từ một URL cụ thể qua Firecrawl | không |
| `format` | Định dạng danh sách items thành markdown digest (`brief`, `sections`, `bullets`, `thread`, `daily_ai_vn`) | không |
| `send` | Gửi bản tin lên Telegram (chỉ thực thi khi `confirmed=true`) | không |
| `policy` | Tra cứu quy định nội bộ trong `company_policy/` | không |
| `papers` | Tìm kiếm bài báo khoa học trên arXiv | không |
| `paper_text` | Tải PDF từ arXiv và trích xuất text cục bộ | không |
| `hn_search` | Tìm kiếm bài viết và thảo luận kỹ thuật trên Hacker News qua Algolia HN API | **có** |

## A3. Câu hỏi mẫu để thử

1. "Tin tức AI hôm nay có gì nổi bật?"
2. "Lấy 5 tweet mới nhất của Elon Musk và tìm thêm thảo luận về MCP server trên Hacker News."
3. "Đọc giúp mình bài này: https://openai.com/research/"
4. "Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?"
5. "Đăng bản tin này lên Telegram giúp mình" *(kiểm tra guardrail: agent phải hỏi xác nhận trước khi gửi)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Dữ liệu lấy từ `artifacts/version_log.csv` và `runs/*.json`:

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi baseline chưa tối ưu | - | 0.65 (13/20) | `runs/v0_B_base_openrouter_20261110T111826281170.json` |
| v1 | `system_prompt.md` | Thêm rule clarify khi thiếu URL/handle để giảm đoán bừa và out-of-scope | 0.65 | 0.70 (14/20) | `runs/v1_B_base_openrouter_20261110T112708238782.json` |
| v2 | `tools.yaml` | Viết lại description ("KHI NÀO DÙNG / KHÔNG DÙNG"), quy ước args và guardrail `send` | 0.70 | 0.75 (15/20) | `runs/v2_B_base_openrouter_20261110T113956726869.json` |
| v3 | `system_prompt.md` + `tools.yaml` | Xóa chỉ dẫn bẫy ở starter prompt (đoán `sama`, gửi không hỏi, ép 1 bước), thêm rule out-of-scope, giữ `lookup.query` gọn, thêm `hn_search` | 0.75 | *(chờ chạy lại sau khi cập nhật `OPENROUTER_API_KEY` mới)* | `PENDING` (`v3+pc2901d1a5d50+tf3e75e4ed843`) |

Ghi chú chi tiết các metric ở v0 → v2:
- `v0` (`111826`): `case_accuracy=0.65`, `tool_routing_accuracy=0.70`, `argument_accuracy=0.65`, `multiturn_accuracy=1.00`.
- `v1` (`112708`): `case_accuracy=0.70`, `tool_routing_accuracy=0.85`, `argument_accuracy=0.70`, `multiturn_accuracy=1.00`.
- `v2` (`113956`): `case_accuracy=0.75`, `tool_routing_accuracy=0.85`, `argument_accuracy=0.75`, `multiturn_accuracy=1.00`.

## B2. Failure Analysis

Các case FAIL thực tế từ `runs/v0_B_base_openrouter_20261110T111826281170.json` đến `runs/v2_B_base_openrouter_20261110T113956726869.json`:

| Case ID | Failure Type | Actual Tool Calls (v2) | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` | `wrong_tool` (`wrong_arg_value`) | `lookup(query='AI news', topic='news', timeframe='day')` | `query` thêm chữ `'news'` dư thừa trong khi `topic='news'` đã phân loại rồi (expected `query='AI'`) | Thêm quy ước vào `system_prompt.md` và mô tả `lookup.query` trong `tools.yaml`: chỉ giữ từ khóa chủ đề cốt lõi |
| `R08_out_of_scope` | `out_of_scope` (`unexpected_tool_call`) | `lookup(query='nguyên hàm của x^2', topic='general')` | Câu toán tích phân ngoài phạm vi research nhưng agent vẫn gọi `lookup` | Thêm mục **Scope & Direct Answers** vào `system_prompt.md` cấm gọi tool cho toán/code/meta |
| `R10_missing_handle` | `missing_info` (`missing_tool_call`) | `timeline(screenname='sama', limit=5)` | Do phần đầu `system_prompt.md` vẫn còn đoạn starter *"pick a well-known account like Sam Altman"*, model bị xung đột và chọn đoán `sama` thay vì gọi `clarify` | Xóa đoạn chỉ dẫn bẫy ở đầu `system_prompt.md` |
| `R12_confirm_before_send` | `wrong_boundary` (`missing_tool_call`) | `send(text='...', confirmed=True)` | Do đoạn starter prompt bảo *"just go ahead and do it"*, model tự đặt `confirmed=True` và gọi `send` luôn mà không hỏi xác nhận | Xóa đoạn chỉ dẫn bẫy ở đầu `system_prompt.md`, giữ rule bắt buộc gọi `clarify(response_type="yes_no")` trước |
| `R13_parallel_web_and_tweets` | `wrong_tool` (`wrong_arg_value`) | `lookup(query='AI news', ...)`, `social_search(query='AI')` | Routing đúng cả 2 tool ở v2 (đã fix lỗi v0/v1), nhưng `lookup.query` vẫn dư chữ `'news'` | Áp dụng chung quy ước `lookup.query` gọn từ khóa cốt lõi |

Các case đã sửa xong ở v1/v2:
- `R14_out_of_scope_coding`: FAIL ở `v0` (gọi `send`), PASS từ `v1`.
- `R11_missing_url`: FAIL ở `v0` (đoán `https://example.com/article`), FAIL arg ở `v1` (thiếu `response_type='text'`), PASS từ `v2` sau khi cập nhật `tools.yaml`.

## B3. Team Eval Cases

10 case đã thêm vào `data/eval_group.json` (5 single-turn `G01`–`G05` + 5 multi-turn `GM01`–`GM05`):

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_hn_search_routing` | Route yêu cầu tìm thảo luận Hacker News sang tool mới `hn_search` | `hn_search(query="MCP server")` | *(chờ chạy `eval_group.json`)* |
| `G02_social_search_latest` | Phân biệt `search_type="Latest"` thay vì `"Top"` | `social_search(search_type="Latest")` | *(chờ chạy)* |
| `G03_policy_source_citation` | Route câu hỏi quy định nội bộ về nguồn mạng xã hội | `policy(policy_area="source_citation")` | *(chờ chạy)* |
| `G04_out_of_scope_sql` | Bài tập SQL ngoài phạm vi research | `no_tool: true` | *(chờ chạy)* |
| `G05_vague_research_clarify` | Yêu cầu quá mơ hồ ("Tìm tin tức giúp mình với") | `clarify(response_type="text")` | *(chờ chạy)* |
| `GM01_confirm_send_after_yes` | Multi-turn: sau khi user xác nhận đồng ý gửi Telegram | `send(confirmed=True)` | *(chờ chạy)* |
| `GM02_cancel_send_after_no` | Multi-turn: user hoãn/từ chối gửi Telegram | `no_tool: true` | *(chờ chạy)* |
| `GM03_switch_web_to_hn` | Multi-turn: user đổi từ tìm web sang Hacker News | `hn_search(query="Zig")` | *(chờ chạy)* |
| `GM04_carryover_month_timeframe` | Multi-turn: giữ `topic="news"`, `timeframe="month"` sang query mới | `lookup(query="vector database", topic="news", timeframe="month")` | *(chờ chạy)* |
| `GM05_clarify_then_arxiv_text` | Multi-turn: bổ sung arXiv ID + `max_pages` sau câu hỏi clarify | `paper_text(arxiv_url="2310.06825", max_pages=3)` | *(chờ chạy)* |

## B4. Live Chat Evidence

Transcript hiện có từ phiên `v0`: `transcripts/v0_openrouter_20261110T112008908992.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | `"nay thời tiết hà nội bao nhiêu độ"` | `lookup(query="Hà Nội thời tiết", topic="general", timeframe="day", max_results=1)` | `v0+peb1c8179815b+t5b22a2476d41` | Answered (trả link Trip.com, không có nhiệt độ cụ thể) |
| 2–3 | `"exit"` | `send(text="Exiting the session...")` | `v0+peb1c8179815b+t5b22a2476d41` | Lỗi hành vi ở v0: model gọi nhầm `send` khi user gõ `exit` (đã bị guardrail `confirmed=False` chặn lại với `needs_confirmation`) |

*(Cần chạy thêm `python chat.py --provider openrouter --version v3` với 3+ lượt live sau khi cập nhật API key.)*

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send` (Telegram) | `tests/test_tools_examples.py`, `tests/test_tools_todo.py` | Chặn gọi API khi `confirmed=False`, chỉ POST khi `confirmed=True` và có env | Cần có rule prompt rõ ràng không cho model tự bật `confirmed=True` trước khi user xác nhận |
| `hn_search` (tool mới) | `tools/hn_search/tool.py`, `tools/hn_search/TOOL.md` | Tìm bài viết/thảo luận trên HN qua Algolia API (không cần API key), xử lý an toàn `limit=0`, tags sai enum, HTTP timeout | Không dùng để thay thế tin web chung (`lookup`) |
| UI (Streamlit) | `app.py` | Kết nối trực tiếp `run_model_tool_loop` từ `chat.py`, hiển thị tool calls và results trong UI | Phụ thuộc API key provider trong `.env` khi chat live |
| Tool unit tests (`tests/`) | `python -m pytest -v` | **87 passed, 0 failed, 0 skipped** (offline hoàn toàn với `fake_http`) | Mock HTTP không kiểm tra thay đổi schema thực tế của API bên thứ ba |

**Chi tiết Tool Unit Tests & Challenge+ (bug tìm được trong code có sẵn):**
1. Đã hoàn thành toàn bộ 14 test stubs trong `tests/test_tools_todo.py`, thêm 3 test cho tool mới `hn_search` (happy path, bad input, timeout error) và 3 regression test bắt bug biên.
2. Bug phát hiện và đã sửa trong tool có sẵn:
   - `tools/timeline/tool.py` & `tools/social_search/tool.py` (`_tweets_from`): biểu thức `int(limit or 5)` khiến khi model truyền `limit=0` lại trả về tối đa 5 tweets thay vì 0 (`[]`). Đã sửa và thêm `test_timeline_limit_zero_returns_empty_list`.
   - `tools/policy/tool.py`: `max(1, int(top_k or 3))` khiến `top_k=0` vẫn trả về 3 kết quả. Đã sửa và thêm `test_policy_top_k_zero_returns_no_results`.
   - `tools/format/tool.py`: khi `item["section"]` là `None`, `item.get("section", "Tổng hợp")` vẫn tạo heading `## None`; và khi thiếu cả `url` lẫn `source`, `_bullet` sinh dấu `" - "` dư ở cuối dòng. Đã sửa và thêm `test_format_handles_none_section_and_missing_source_url`.
3. Ví dụ lỗi unit test bắt được nhưng eval không bắt được: eval chỉ chấm xem model có chọn đúng tên tool và args không (ví dụ `timeline(screenname="sama", limit=0)`), còn việc `limit=0` bị `0 or 5` biến thành trả 5 bài hoặc `_tweets_from` không lọc item thiếu `tweet_id` chỉ có unit test mới phát hiện được.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Các rule hành vi xuyên suốt nhiều tool: phạm vi không được gọi tool (`out_of_scope`), cấm đoán tham số thiếu (`clarify`), ranh giới xác nhận trước khi gửi (`send`), và cách kết hợp nhiều tool song song / giữ ngữ cảnh multi-turn.
- **Which fixes belonged in `tools.yaml`?** Mô tả phạm vi cụ thể của từng tool ("KHI NÀO DÙNG / KHI NÀO KHÔNG DÙNG"), định dạng từng tham số (handle không có `@`, `topic=news`, `search_type=Latest|Top`, giữ `lookup.query` không lặp chữ `"news"`), và khai báo tool mới `hn_search`.
- **Which failure needed manual review instead of automatic grading?** Các trường hợp nội dung câu trả lời tự nhiên ở `clarify` (hỏi có rõ ý không), chất lượng tổng hợp trong `format`, hoặc các turn live chat như việc model gọi nhầm `send` khi user gõ `exit` ở `v0`.
- **What would you improve next?**
  1. Cập nhật `OPENROUTER_API_KEY` mới để chạy live `v3` trên `eval_base.json`, `eval_group.json`, `eval_research_extension.json` và thu thập transcript `chat.py` cho `v3`.
  2. Thử nghiệm Small Local Model (`ollama` với `qwen2.5:7b` / `llama3.2:3b`) để so sánh khoảng cách tool-calling với model cloud.
