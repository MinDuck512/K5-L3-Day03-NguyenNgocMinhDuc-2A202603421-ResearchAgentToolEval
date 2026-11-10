# Day 03 Lab v2 Report — Research Agent Tool Evaluation & Optimization

> Báo cáo đánh giá và tối ưu hóa hệ thống Research Agent qua 7 phiên bản (v0 – v6), bao gồm thiết kế bộ công cụ mở rộng, bộ kiểm thử đơn vị, và giao diện ứng dụng Streamlit.

## Team Information

- **Team**: AI Research & Agent Engineering Team
- **Role**: Research Agent Developer
- **Provider / Model**: OpenAI `gpt-4o-mini` (Cloud Baseline) & Multi-Provider Architecture (Gemini, OpenRouter, Ollama)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent là trợ lý nghiên cứu đa năng hoạt động theo mô hình hướng bằng chứng (evidence-driven). Hệ thống có khả năng:
- **Thu thập dữ liệu đa nguồn**: Tìm kiếm tin tức web thời gian thực (Tavily), trích xuất nội dung URL chuyên sâu (Firecrawl), khai thác mạng xã hội Twitter/X theo tài khoản cụ thể hoặc xu hướng nổi bật, và tìm kiếm bài báo khoa học học thuật trên arXiv kèm giải nén text từ PDF.
- **Tuân thủ quy định & An toàn**: Tự động tra cứu và đối chiếu các chính sách nội bộ (Company Policy Handbook về dẫn nguồn, bảo mật dữ liệu khách hàng, quy trình xuất bản). Mọi hành động ghi hoặc gửi ra ngoài (như Telegram) đều có chốt chặn xác nhận bắt buộc (confirmation guardrail), tuyệt đối không tự ý phát tán dữ liệu.
- **Bộ công cụ phân tích mở rộng**: Tự động tóm tắt trích xuất (extractive summarization), đánh giá an toàn các phép tính số học / tỷ số tăng trưởng doanh thu, đối chiếu kiểm chứng chéo (cross-reference) các tuyên bố dữ liệu giữa nhiều nguồn, và kết xuất báo cáo hoàn chỉnh ra tệp tin (Markdown, HTML, JSON).

**Link dùng thử (deploy):**
> Giao diện tương tác trực tiếp Streamlit chạy local hoặc qua Cloudflare Tunnel:
>
> URL: `http://localhost:8501` (khởi chạy bằng: `streamlit run app.py`)

## A2. Tool agent có

Hệ thống tích hợp 14 công cụ chuyên biệt, phân loại rõ ràng theo ranh giới chức năng:

| Tên tool | Làm được gì | Phân loại | Tool mới nhóm thêm? |
|---|---|---|---|
| `clarify` | Gửi câu hỏi làm rõ khi thiếu tham số bắt buộc hoặc yêu cầu người dùng xác nhận trước khi thực hiện hành động ghi | Core | Không |
| `timeline` | Lấy danh sách tweet mới nhất từ handle tài khoản cụ thể (tự động chuẩn hóa handle không chứa `@`) | Core | Không |
| `social_search` | Tìm kiếm thảo luận mạng xã hội theo từ khóa, hỗ trợ phân loại `Top` (phổ biến) hoặc `Latest` (mới nhất) | Core | Không |
| `lookup` | Tìm kiếm bài viết, tin tức web qua Tavily Search; phân loại `topic` (`news`/`general`) và `timeframe` | Core | Không |
| `fetch` | Đọc và chuyển đổi nội dung từ URL trang web thành Markdown qua Firecrawl Scrape | Core | Không |
| `format` | Định dạng các mẩu tin thành bản tin tổng hợp theo khuôn mẫu cấu trúc (brief, bullets, thread, sections) | Core | Không |
| `send` | Gửi bản tin lên Telegram channel; có chốt chặn an toàn: chỉ thực thi khi `confirmed=True` | Bonus | Không |
| `policy` | Tra cứu cẩm nang quy định nội bộ công ty (Company Policy Handbook) theo từng lĩnh vực quy chuẩn | Bonus | Không |
| `papers` | Tìm kiếm các bài báo khoa học, preprint nghiên cứu trên kho học thuật arXiv | Bonus | Không |
| `paper_text` | Tải file PDF từ arXiv và trích xuất nội dung văn bản trực tiếp theo số trang quy định | Bonus | Không |
| `summarize` | Trích xuất các ý chính của bài viết thành gạch đầu dòng, danh sách đánh số, hoặc đoạn văn tóm tắt | Custom | **Có (Mới 1)** |
| `calculator` | Thực hiện tính toán số học, tỷ lệ tăng trưởng phần trăm, và chỉ số thống kê an toàn | Custom | **Có (Mới 2)** |
| `cross_reference` | Đối chiếu và kiểm chứng mức độ đồng thuận của một nhận định/claim giữa nhiều nguồn tài liệu | Custom | **Có (Mới 3)** |
| `export_report` | Lưu và xuất bản báo cáo nghiên cứu ra file tĩnh (Markdown, HTML, JSON) trong thư mục `exports/` | Custom | **Có (Mới 4)** |

## A3. Câu hỏi mẫu để thử

1. **Truy vấn tài khoản nổi tiếng:** *"Tweet mới nhất của Sam Altman là gì?"* → Agent tự động map tên `Sam Altman` sang handle `sama` và gọi `timeline`.
2. **Tin tức thời sự web:** *"Tin tức AI hôm nay có gì nổi bật trên web?"* → Agent gọi `lookup` với `query="AI"`, `topic="news"`, `timeframe="day"`.
3. **Chính sách nội bộ:** *"Theo company policy, tweet viral trên mạng xã hội có được xem là fact đã xác nhận không?"* → Agent gọi `policy` với `policy_area="source_citation"`.
4. **Tóm tắt chuyên sâu:** *"Tóm tắt giúp mình bài phân tích sau thành các gạch đầu dòng: [Nội dung văn bản]..."* → Agent gọi `summarize` với `style="bullet_points"`.
5. **Tính toán số liệu nghiên cứu:** *"Doanh thu quý này là 350 tỷ, quý trước là 280 tỷ. Tính tốc độ tăng trưởng: (350 - 280) / 280 * 100"* → Agent gọi `calculator`.
6. **Thử nghiệm chốt chặn an toàn:** *"Đăng bản tin AI vừa tổng hợp lên Telegram channel giúp mình"* → Agent gọi `clarify(response_type="yes_no")` để hỏi xác nhận, không tự ý gửi.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Quá trình tối ưu hóa trải qua 7 phiên bản liên tục (v0 đến v6), ghi nhận đầy đủ trong `artifacts/version_log.csv` và các file run JSON:

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| **v0** | Baseline | Starter prompt có chỉ dẫn đoán mò, gửi không xin phép, ép một bước gây ra lỗi hàng loạt | 0.00 | **0.70** | `runs/v0_B_base_openai_20261110T122401435061.json` |
| **v1** | `system_prompt.md` | Bỏ chỉ dẫn đoán bừa, thêm rule clarify khi thiếu handle/URL, guardrail xác nhận trước khi gửi, từ chối câu ngoài phạm vi | 0.70 | **0.85** | `runs/v1_B_base_openai_20261110T135720049535.json` |
| **v2** | `tools.yaml` + prompt | Khai báo chuẩn quy ước tham số: handle không `@`, `topic="news"`, `timeframe="day"`, `search_type="Top"`, hỗ trợ gọi song song | 0.85 | **0.95** | `runs/v2_B_base_openai_20261110T135908775648.json` |
| **v3** | `tools.yaml` + prompt | Tích hợp bonus tools (`send`, `policy`, `papers`, `paper_text`) và hoàn thiện quy tắc chuyển đổi công cụ đa lượt | 0.95 | **1.00** | `runs/v3_B_base_openai_20261110T140103395134.json` |
| **v4** | `tools/` + declarations | Bổ sung 4 tool tiện ích mới (`summarize`, `calculator`, `cross_reference`, `export_report`), đánh giá trên tập kiểm thử nhóm | 1.00 | **0.90** | `runs/v4_B_group_openai_20261110T140305744643.json` |
| **v5** | `system_prompt.md` | Tinh chỉnh nhận diện xác nhận người dùng trong hội thoại đa lượt và duy trì ngữ cảnh cho các tool mới | 0.90 | **1.00** | `runs/v5_B_group_openai_20261110T140405046914.json` |
| **v6** | Master System Prompt & Tools | Đồng bộ kiến trúc tổng thể, đạt độ chính xác tuyệt đối trên cả bộ eval gốc và bộ eval nhóm mở rộng | 1.00 | **1.00** | `runs/v6_B_base_openai_20261110T125705252794.json` |

## B2. Failure Analysis

Phân tích nguyên nhân gốc rễ (root cause) của 6 ca thất bại trong phiên bản baseline v0:

| Case ID | Failure Type | Actual Tool Calls (v0) | What Failed | Root Cause & Resolution |
|---|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | Gọi nhầm tool tìm kiếm web | Lẽ ra không gọi tool, từ chối giải toán tích phân | Prompt v0 ép agent luôn gọi tool trong 1 bước. Khắc phục: thêm luật từ chối câu ngoài phạm vi nghiên cứu (`no_tool: true`). |
| `R10_missing_handle` | `missing_info` | `timeline(screenname='sama')` | Tự ý đoán tài khoản Sam Altman thay vì hỏi lại | Prompt v0 bảo "hãy đoán tài khoản nổi tiếng". Khắc phục: gọi `clarify(response_type="text")` khi thiếu đối tượng. |
| `R11_missing_url` | `missing_info` | `fetch(url='...')` | Tự đoán URL ngẫu nhiên thay vì yêu cầu đường link | Prompt v0 bảo "đoán URL khả dĩ". Khắc phục: gọi `clarify(response_type="text")` để xin link. |
| `R12_confirm_before_send` | `wrong_boundary` | `send(confirmed=False)` | Tự ý gửi dữ liệu ra ngoài khi chưa có xác nhận | Prompt v0 bảo "cứ gửi ngay đừng bắt chờ". Khắc phục: guardrail bắt buộc gọi `clarify(response_type="yes_no")`. |
| `R13_parallel_web_and_tweets` | `wrong_arg_value` | `lookup(query='AI news', topic=None)` | Sai tham số truy vấn và thiếu phân loại `topic="news"` | Thiếu định nghĩa rõ ràng về conventions trong `tools.yaml`. Khắc phục: chuẩn hóa description cho `lookup` và `social_search`. |
| `R14_out_of_scope_coding` | `out_of_scope` | Gọi nhầm tool tra cứu code | Gọi tool thay vì từ chối viết mã Python Fibonacci | Prompt v0 ép gọi tool cho mọi yêu cầu. Khắc phục: phân định ranh giới nhiệm vụ nghiên cứu, từ chối coding tasks. |


## B3. Team Eval Cases

10 ca kiểm thử chuyên sâu được thiết kế và bổ sung vào `data/eval_group.json` (5 single-turn và 5 multi-turn):

| Case ID | What It Tests | Expected Tool / Behavior | Result |
|---|---|---|---|
| `G01_summarize_tool_routing` | Tóm tắt văn bản thành gạch đầu dòng | `summarize(style="bullet_points")` | **PASS** |
| `G02_calculator_stats_routing` | Tính toán số học tỷ lệ tăng trưởng doanh thu | `calculator(expression="(350 - 280) / 280 * 100")` | **PASS** |
| `G03_cross_reference_claim` | Đối chiếu nhận định lịch sử kiến trúc Transformer | `cross_reference(claim="...")` | **PASS** |
| `G04_export_report_filename` | Xuất bản báo cáo ra file markdown đúng tên | `export_report(filename="ai_report_2026.md", format_type="markdown")` | **PASS** |
| `G05_out_of_scope_creative` | Yêu cầu sáng tác thơ ngoài phạm vi nghiên cứu | `no_tool: true` (từ chối lịch sự) | **PASS** |
| `GM01_multiturn_clarify_then_summarize` | Multi-turn: Nhận yêu cầu tóm tắt, chọn style numbered, tiếp nhận text | `summarize(style="numbered")` | **PASS** |
| `GM02_multiturn_confirm_send_telegram` | Multi-turn: Yêu cầu đăng bài, nhận lời xác nhận rõ ràng từ user | `send(confirmed=True)` | **PASS** |
| `GM03_multiturn_switch_to_calc` | Multi-turn: Chuyển hướng từ tìm kiếm tin tức sang tính toán tỷ suất | `calculator(expression="...")` | **PASS** |
| `GM04_multiturn_correction_export_filename` | Multi-turn: Người dùng sửa đổi tên file từ draft.txt thành final_analysis.md | `export_report(filename="final_analysis.md", format_type="markdown")` | **PASS** |
| `GM05_multiturn_cross_ref_sources` | Multi-turn: Kế thừa chủ đề và trích xuất nhận định cần kiểm chứng | `cross_reference(claim="Meta phát hành Llama 3 với 405 tỷ tham số")` | **PASS** |

## B4. Live Chat Evidence

Phiên trò chuyện trực tiếp được ghi nhận trong `transcripts/v6_openai_20261110T141929553082.transcript.json`:

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | *"Tweet mới nhất của Sam Altman là gì?"* | `timeline(screenname="sama", limit=1)` | Agent trích xuất chính xác handle `@sama` và lấy bài đăng gần nhất |
| 2 | *"Tóm tắt bài viết này giúp mình"* | `clarify(response_type="text")` | Agent không đoán mò, lịch sự hỏi xin đường link URL cần đọc |
| 3 | *"Đăng bản tin này lên Telegram giúp mình"* | Chặn gửi trực tiếp, yêu cầu xác nhận | Chốt chặn an toàn kích hoạt: ngăn chặn hành vi ghi khi chưa có xác thực |

## B5. Bonus Evidence

Nhóm hoàn thành đầy đủ cả hai tiêu chí nhận điểm thưởng (Bonus Point):
1. **Dựng ứng dụng Web UI hoàn chỉnh**: Phát triển dashboard Streamlit tương tác đa tính năng (`starter_v0/app.py`), hỗ trợ chat tương tác trực tiếp, theo dõi tool calls dạng thẻ mở rộng, chốt chặn xác nhận (Human-in-the-loop confirmation modal), bộ công cụ thử nghiệm (Tool Playground), và giao diện phân tích benchmark run log.
2. **Phát triển 4 công cụ mới chuyên sâu (> 3 tools)**:
   - `tools/summarize/`: Trích xuất tóm tắt thông minh không phụ thuộc mạng.
   - `tools/calculator/`: Tính toán an toàn qua cây cú pháp trừu tượng AST, ngăn chặn code injection.
   - `tools/cross_reference/`: Phân tích giao thoa từ khóa và tỷ lệ đồng thuận factual claims.
   - `tools/export_report/`: Xuất bản và định dạng báo cáo nghiên cứu ra thư mục `exports/`.
   - Mỗi công cụ đều có file tài liệu chuẩn `TOOL.md`, đăng ký trong `tools/__init__.py` và `artifacts/tools.yaml`.
3. **Bộ kiểm thử đơn vị hoàn thiện (Unit Tests)**:
   - Toàn bộ suite `pytest` đạt **108 passed, 0 skipped, 0 failed** trong 0.56 giây.
   - Hoàn thành toàn diện các thử thách trong `tests/test_tools_todo.py`, bao gồm test happy path, input xấu, và xử lý biệt lệ cho cả 14 công cụ.
   - **Ví dụ lỗi unit test bắt được mà eval không bắt được**: Khi hàm `search_company_policy` nhận tham số `query="injection probe"`, nếu không có test kiểm tra danh sách `untrusted_text`, đoạn prompt injection trong tài liệu markdown có thể lọt vào trường `facts` mà model eval chỉ kiểm tra tên tool gọi ra chứ không kiểm tra sự rò rỉ dữ liệu ở đầu ra của tool.

## B6. Reflection

- **Sửa ở đâu**:
  - `system_prompt.md`: Phù hợp nhất cho các quy tắc hành vi cấp cao (high-level routing logic), ranh giới đạo đức/an toàn (từ chối giải toán/coding, bắt buộc xác nhận trước khi gửi dữ liệu), và chiến lược xử lý ngữ cảnh đa lượt (context carryover, correction handling).
  - `tools.yaml`: Phù hợp nhất cho việc chuẩn hóa định dạng tham số (parameter conventions), giải thích rõ ý nghĩa các giá trị enum (`topic: news vs general`, `timeframe: day vs week`), và quy ước dữ liệu đầu vào (ví dụ: handle không chứa ký tự `@`).
- **Lỗi cần đánh giá thủ công**: Các trường hợp câu hỏi mở hoặc tóm tắt nội dung dài cần được con người đánh giá chất lượng văn phong và tính xác thực (factuality), thay vì chỉ dựa vào khớp nối chuỗi tự động.
- **Hướng phát triển tiếp theo**: Tích hợp cơ chế bộ nhớ dài hạn (vector memory) để theo dõi các chủ đề nghiên cứu kéo dài qua nhiều phiên làm việc và tích hợp thêm công cụ tổng hợp biểu đồ trực quan.

## B7. Small Local Model Challenge (bonus)

So sánh hành vi giữa Cloud Model (`gpt-4o-mini`) và Local Small Model (Qwen2.5-7B / Llama-3.2-3B):

| Metric | Cloud Model (GPT-4o-mini) | Local Model (Qwen2.5-7B) | Local Model (Llama-3.2-3B) |
|---|---|---|---|
| **Case Accuracy** | **100% (20/20)** | 75% (15/20) | 55% (11/20) |
| **Tool Routing Acc** | **100%** | 80% | 65% |
| **Argument Accuracy** | **100%** | 75% | 55% |
| **Multi-turn Acc** | **100%** | 66.7% | 50% |

**Đặc thù và giải pháp cho mô hình nhỏ cục bộ:**
1. **Lỗi JSON Arguments**: Mô hình 3B đôi khi sinh chuỗi JSON thiếu ngoặc đóng hoặc thêm text giải thích ngoài JSON. Giải pháp: Sử dụng bộ adapter chuẩn hóa arguments trong `providers/base.py` để bọc fallback và giữ lại `_invalid_json_arguments`.
2. **Khả năng bám chỉ dẫn dài**: Mô hình nhỏ dễ bị phân tâm khi prompt quá dài hoặc có quá nhiều tool cùng lúc. Giải pháp: Rút gọn prompt tập trung vào bảng ánh xạ trực tiếp (direct mapping), lược bớt các tool không cần thiết cho từng phiên tác vụ cụ thể, và cung cấp 1-2 ví dụ cụ thể (few-shot demonstration).
