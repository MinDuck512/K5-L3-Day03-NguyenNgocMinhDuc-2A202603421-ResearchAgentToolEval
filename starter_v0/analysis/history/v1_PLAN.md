# V1 — một giả thuyết, đã chạy đánh giá

## Giả thuyết

Chỉ dẫn starter yêu cầu đoán account/URL khi thiếu thông tin có thể làm agent bỏ qua clarify. Thay riêng đoạn này bằng quy tắc hỏi lại khi dữ kiện cần thiết chưa có trong hội thoại sẽ cải thiện các yêu cầu thiếu thông tin, đồng thời giữ dữ kiện đã được cung cấp ở lượt trước.

Đã kiểm chứng một lần trên cùng model OpenRouter: R10/R11 chuyển FAIL → PASS; case accuracy 0.60 → 0.65. Có ba case giảm điểm; xem analysis/v0_v1_comparison.md. Các log Gemini cũ không được dùng để so trực tiếp với OpenRouter.

## Thay đổi duy nhất

- File sửa: artifacts/system_prompt.md.
- Thay một đoạn: đoán account/URL → hỏi clarify(response_type="text") khi thiếu thông tin.
- tools.yaml, dữ liệu eval và cơ chế chấm giữ nguyên.
- Bản prompt/tools v0 được lưu tại artifacts/versions/v0/ để chạy lại baseline.
- Đã ghi v1 vào version_log từ run thực tế; có metric trước/sau và đường dẫn run JSON.

Artifact chuẩn bị: `v1+p997e21ee7b23+t8db0ba629f52`.

## Chạy đánh giá bằng OpenRouter — model miễn phí cố định

- Provider hiện tại: `openrouter`.
- Model cố định: `nvidia/nemotron-3.5-lightning:free`.
- Preflight model này đã PASS, trả structured tool call `timeline`.
- Hạn mức trước preflight model cố định: 1/50 request đã dùng, còn 49. Cần kiểm tra lại trước v1.
- `openrouter/free` đã dùng để kiểm tra kết nối ban đầu; không dùng router tự chọn model để so sánh v0–v3.
- Giữ lịch sử Gemini/OpenAI; các lỗi quota/credit cũ không được so như cùng một model.

### Baseline v0

Dùng snapshot gốc để tránh nhầm prompt hiện tại (đã chuẩn bị cho v1):

```powershell
.\.venv\Scripts\python.exe run_eval.py --provider openrouter --model nvidia/nemotron-3.5-lightning:free --version v0 --suite base --eval-cases data/eval_base.json --system-prompt artifacts/versions/v0/system_prompt.md --tools artifacts/versions/v0/tools.yaml --request-interval 4 --max-retries 1 --retry-delay 10 --max-retry-wait 30
```

### Đánh giá v1

Sau khi đọc baseline và kiểm tra còn đủ hạn mức, chạy prompt hiện tại với cùng model và cấu hình:

```powershell
.\.venv\Scripts\python.exe run_eval.py --provider openrouter --model nvidia/nemotron-3.5-lightning:free --version v1 --suite base --eval-cases data/eval_base.json --request-interval 4 --max-retries 1 --retry-delay 10 --max-retry-wait 30
```

Đọc metric tổng và lỗi từng case. Chỉ ghi kết quả v1 sau khi có run thật. Nếu không cải thiện, ghi nhận và đổi giả thuyết theo README; giữ nguyên eval_base và cơ chế chấm.

### Lịch sử thiết lập

- Gemini: đã gọi được API nhưng gặp quota ngày (20 request cho project/model trong log).
- OpenAI / gpt-4o-mini: preflight báo credit_balance_exhausted.
- OpenRouter: cả router miễn phí và model cố định nêu trên đã qua preflight.

## Kết quả đã đo

V0: `runs/v0_B_base_openrouter_20261110T124056248410.json` (12/20). V1: `runs/v1_B_base_openrouter_20261110T124451769886.json` (13/20). Cả hai đo đủ 20 case, 0 provider_error. Không cần chạy lặp lại hai lệnh trên nếu không có thay đổi hoặc lý do kiểm chứng mới. Quota sau v1 còn 10 request; giữ cho công việc cần thiết, chưa đủ cả suite v2.
