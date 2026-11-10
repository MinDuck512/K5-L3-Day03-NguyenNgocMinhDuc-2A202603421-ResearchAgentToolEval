# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: NguyenNgocMinhDuc 
- Members: Nguyen Ngoc Minh Duc - Duong Tuan Hung - Le Hoang Quan - Le Quang Huy - Nguyen Tung
- Provider/model: OpenRouter (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent đa năng: hỗ trợ tìm kiếm tin tức thời sự trên web (`lookup`), theo dõi bài đăng của tài khoản nổi tiếng (`timeline`), tìm kiếm thảo luận trên mạng xã hội Twitter (`social_search`), đọc toàn văn link bài viết (`fetch`), tính toán số học & tỷ lệ thống kê tăng trưởng dữ liệu an toàn (`calculator`), đóng gói digest (`format`), và gửi tin báo cáo Telegram an toàn khi có xác nhận (`send`).

**Link dùng thử (deploy):**

- Chạy cục bộ: `streamlit run app.py` (truy cập tại `http://localhost:8501`)
- Expose công khai qua Cloudflare Tunnel:
  ```bash
  cloudflared tunnel --url http://localhost:8501
  ```
- URL Public: `https://research-agent-demo.trycloudflare.com` *(hoặc link tunnel đang chạy)*

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|:---:|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin quan trọng hoặc yêu cầu xác nhận trước khi gửi tin | Không |
| `timeline` | Lấy các bài đăng gần đây của một cá nhân/tài khoản cụ thể trên Twitter/X | Không |
| `social_search` | Tìm kiếm các bài đăng trên Twitter/X theo từ khóa (Latest / Top) | Không |
| `lookup` | Tra cứu thông tin, bài viết hoặc tin tức thời sự trên web (`topic="news"`, `timeframe="day"`) | Không |
| `fetch` | Đọc và trích xuất nội dung bài viết từ một đường link URL cụ thể | Không |
| `format` | Trình bày dữ liệu đã thu thập thành bản tin tóm tắt Markdown theo các template | Không |
| `send` | Gửi văn bản lên kênh Telegram (chỉ kích hoạt khi user đã xác nhận `confirmed=true`) | Không |
| `calculator` | Thực hiện tính toán số học, căn bậc hai, phần trăm tăng trưởng an toàn cho nghiên cứu | **CÓ (MỚI)** |
| `policy` | Tra cứu quy định nội bộ trong tài liệu công ty | Không |
| `papers` | Tìm kiếm các bài báo khoa học và công trình nghiên cứu trên arXiv | Không |
| `paper_text` | Tải và trích xuất nội dung văn bản chi tiết từ bài báo arXiv | Không |

## A3. Câu hỏi mẫu để thử

1. **Tin tức thời sự:** `"Tin tức AI hôm nay có gì nổi bật?"` *(Model sẽ tự gọi `lookup` với `topic="news"` và `timeframe="day"`)*
2. **Theo dõi tài khoản:** `"Tweet mới nhất của Sam Altman là gì?"` *(Model tự động map tên thành handle `sama` và gọi `timeline`)*
3. **Tính toán số liệu (Tool mới):** `"Doanh thu quý này đạt 150 tỷ, quý trước là 120 tỷ. Hãy tính tỷ lệ phần trăm tăng trưởng giúp mình."` *(Model tự gọi tool mới `calculator` với biểu thức `(150 - 120) / 120 * 100`)*
4. **Đọc URL:** `"Tóm tắt bài viết này giúp mình: https://openai.com/research/"` *(Model gọi `fetch` để đọc và tóm tắt)*
5. **Guardrail an toàn:** `"Gửi bài báo cáo này lên kênh Telegram giúp tôi"` *(Model sẽ dừng lại và gọi `clarify` xin xác nhận thay vì tự tiện gửi)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo lường điểm xuất phát ban đầu với starter prompt & tools.yaml | 0.0 | 0.70 (70%) | `runs/v0_B_base_openrouter_20261110T110718249079.json` |
| v1 | `system_prompt.md` | Bỏ các câu xúi đoán mò và ép 1 bước, thêm routing rules giúp tăng tool routing | 0.70 | 0.70 (Routing: 95%) | `runs/v1_B_base_openrouter_20261110T111033850799.json` |
| v2 | `tools.yaml`, `system_prompt.md` | Chuẩn hoá tham số tools (response_type, timeframe, confirmed) đạt độ chính xác tuyệt đối | 0.70 | **1.00 (100%)** | `runs/v2_B_base_openrouter_20261110T112822436960.json` |
| v3 | Tinh chỉnh & Group eval | Đánh giá toàn diện trên 10 test case mới của nhóm, tích hợp tool `calculator` | 0.70 | **0.90 (90%)** | `runs/v2_B_group_openrouter_20261110T112918992912.json` |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | `send` | User yêu cầu làm thơ nhưng model tự tiện gọi `send` | Cấm gọi tool cho câu ngoài phạm vi trong `system_prompt.md` |
| `R10_missing_handle` | `missing_info` | `timeline` | Thiếu tên tài khoản nhưng model tự bịa handle | Chỉ dẫn gọi `clarify` khi thiếu thông tin |
| `R11_missing_url` | `missing_info` | `fetch` | Thiếu URL nhưng model tự bịa link | Chỉ dẫn gọi `clarify(response_type="text")` |
| `R12_confirm_before_send` | `wrong_boundary` | `send` | Gửi tin khi chưa được xác nhận | Bắt buộc gọi `clarify(response_type="yes_no")` xin xác nhận |
| `R03_web_news_routing` | `wrong_arg_value` | `lookup(timeframe=None)` | Thiếu timeframe="day" cho tin hôm nay | Quy định rõ mô tả tham số `timeframe` trong `tools.yaml` |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|:---:|
| `G01_calculator_growth` | Tính % tăng trưởng bằng tool mới | `calculator` | **PASS** |
| `G02_calculator_eval` | Tính hàm toán học `sqrt` | `calculator` | **PASS** |
| `G03_social_search_top` | Tìm bài viết nổi bật trên Twitter | `social_search(search_type="Top")` | **PASS** |
| `G04_missing_url_article` | Thiếu URL đọc bài | `clarify(response_type="text")` | **PASS** |
| `G05_out_of_scope_creative` | Yêu cầu làm thơ ngoài phạm vi | `no_tool` | **PASS** |
| `G06_multiturn_clarify_then_calc` | Multi-turn: hỏi số liệu rồi tính trung bình cộng | `calculator` | **PASS** |
| `G07_multiturn_missing_handle_fill` | Multi-turn: bổ sung tên Yann LeCun -> ylecun | `timeline(screenname="ylecun")` | **PASS** |
| `G08_multiturn_confirm_then_send` | Multi-turn: xác nhận đồng ý -> gửi tin | `send(confirmed=true)` | **PASS** |
| `G09_multiturn_switch_tool_to_calc` | Multi-turn: chuyển hướng từ search sang tính toán | `calculator` | **PASS** |
| `G10_multiturn_refine_topic_news` | Multi-turn: thu hẹp chủ đề robotics tin hôm nay | `lookup(topic="news", timeframe="day")` | FAIL (arg) |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Doanh thu từ 150 lên 210 tăng bao nhiêu phần trăm?" | `calculator` | v2+pa397b7e95b20+t61a3bd1640c0 | Trả về 40.0% chính xác |
| 2 | "Đọc giúp mình nội dung link https://openai.com/research/" | `fetch` | v2+pa397b7e95b20+t61a3bd1640c0 | Trích xuất và tóm tắt bài viết |
| 3 | "Gửi tóm tắt này lên Telegram" | `clarify` | v2+pa397b7e95b20+t61a3bd1640c0 | Hỏi xác nhận người dùng trước khi gửi |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `calculator` | `tools/calculator/tool.py`, `tests/test_tools_todo.py` | Tính toán số học an toàn bằng Python AST | Chặn chia cho 0, chặn injection mã độc |
| UI Web tương tác | `app.py` | Giao diện Streamlit trực quan, hiển thị tool call & arguments | Expose public qua Cloudflare Tunnel |
| Guardrail xác nhận `send` | `artifacts/tools.yaml`, `runs/v2_...json` | Chặn gửi bài tự tiện, bắt buộc xin xác nhận trước | Bảo vệ tài nguyên mạng, chống spam |
| Tool unit tests (`tests/`) | `pytest` output | 70 passed, 0 failed | Đảm bảo hợp đồng tools và logic không lỗi runtime |

## B6. Reflection

1. **Evidence-Driven Loop:** Việc đọc run JSON và phân loại lỗi thực tế (thay vì phỏng đoán cảm tính) giúp xác định chính xác nguyên nhân vì sao model gọi sai tool hoặc truyền thiếu đối số.
2. **Tách biệt vai trò Prompt vs Tools Specification:** Prompt định hình luồng tư duy tổng thể (khi nào hỏi lại, khi nào không dùng tool), trong khi `tools.yaml` quyết định trực tiếp chất lượng tham số được trích xuất (enum, timeframe, default values).
3. **An toàn (Safety Boundary):** Các hành động có tác động ra ngoài (như gửi tin nhắn) bắt buộc phải có bước xác nhận rõ ràng từ con người để đảm bảo an toàn.
