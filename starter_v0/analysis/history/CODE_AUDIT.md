# Rà soát code và tiêu chí — 10/11/2026

Đã đọc README/TOOL-SETUP, prompt/schema và snapshot, agent/chat/eval/versioning/env,
toàn bộ provider, implementation/TOOL.md của các tool, company policy, test, sample
và các phân tích/run đã có. Bộ đề `eval_base.json` giữ nguyên.

## Lỗi đã sửa và kiểm tra

| Vị trí | Lỗi | Sửa / bằng chứng |
|---|---|---|
| send | Chuỗi `"false"` vẫn truthy | Chỉ `confirmed is True`; regression test |
| send | Trả sent dù Telegram ok=false | Kiểm tra acknowledgement; mock response |
| send | Markdown làm hỏng nội dung literal | Bỏ parse_mode; kiểm tra text 1–4096 ký tự |
| agent/chat/app | Boolean do model tự đặt có thể vượt xác nhận | Eval không gửi; chat/app tạo preview, `/confirm` hoặc nút xác nhận mới gọi send |
| lookup/timeline/social/policy/papers | `0 or default` âm thầm đổi giá trị, số âm slice sai | Bounded integer, nhận chuỗi số nguyên, từ chối boolean/float/0/âm/out-of-range |
| tool input | Handle, URL, enum hoặc item sai gây API lỗi/exception | Kiểm tra trước HTTP và trả error dict |
| fetch | success=false bị coi là nội dung rỗng thành công | Trả error; vẫn giữ metadata và giới hạn 4000 ký tự |
| paper_text | Regex nhận ID nằm trong URL của host khác | Full match ID/arxiv.org; test no-network |
| policy | top_k=0 trả kết quả mặc định | Trả ValueError; giữ query rỗng -> results=[] |
| format | Input sai kiểu hoặc template sai bị crash/fallback mơ hồ | Error dict; groups, bullets, thread, rỗng, thiếu URL đều có test |
| chat | Mất bằng chứng tool khi sang lượt sau | Gắn TOOL_EVIDENCE_JSON vào assistant history |
| chat | Quá số vòng tool thì bỏ kết quả đã thu | Lượt cuối tắt tools để trả lời từ evidence; test fake provider |
| eval | Chỉ lưu cuối run, không resume | Checkpoint mỗi case, resume chỉ lỗi provider và kiểm tra version/model/artifact/dataset |
| provider | SDK retry ngầm chồng retry của harness | max_retries=0 và timeout 60s; giữ fallback REST khi DLL bị chặn |
| Gemini | Dedup có thể che tool call trùng thật của model | Candidate parts là nguồn chính, convenience function_calls chỉ fallback |
| .env | Tên biến external path chỉ có DAY04 | Hỗ trợ DAY03_ENV_FILE và giữ tương thích DAY04_ENV_FILE |
| CLI | CP1252 không in được emoji/tiếng Việt | stdout UTF-8; debug tool JSON dùng ASCII |
| UI | PyArrow DLL bị Application Control chặn | Bảng Markdown; không thay đổi Windows policy |
| error | Request exception có thể chứa token trong URL | Che giá trị env KEY/TOKEN/SECRET trước khi trả error |

## Phần bổ sung

- Source audit: URL tracking/fragments, nguồn thiếu URL, duplicate_of và số tên miền;
  registry/schema/TOOL.md/tests/group cases đều có. Không tự tuyên bố kiểm chứng fact.
- UI Streamlit dùng cùng tool loop với CLI; offline audit giúp demo khi quota lỗi.
- Snapshot v2–v6, một giả thuyết/version. V2 tools chỉ khác newline, schema như v1.
- Eval nhóm 10 case (5+5), có 2 case cho tool mới.
- RUN_GUIDE, runner thu bằng chứng, report/checklist từ run thật và gói nộp không chứa .env.

## Chưa thể coi là đã hoàn tất

Run v2 lần đầu đo 10/20 rồi hết quota; chưa đo đúng case xác nhận gửi R12.
V3–v6, group/extension và ≥3 lượt chat cần provider còn hạn mức. Public URL,
Telegram live và 2 model local chưa có bằng chứng. Chi tiết cập nhật theo
`analysis/TODO_STATUS.md` và `artifacts/REPORT.md`; số test cuối lấy từ `pytest.xml`.

Đối chiếu API theo [Tavily](https://docs.tavily.com/documentation/api-reference/endpoint/search),
[Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest),
[OpenRouter](https://openrouter.ai/docs/api_reference/limits).
