# Chạy và hoàn thiện bằng chứng

Thư mục chạy lệnh: `starter_v0/`. Python đang dùng trong workspace này:
`D:\VinAI\Day03-Prompt-Engineering-Tool-Calling-Labs-student-main\.venv\Scripts\python.exe`.
Nếu dùng terminal mới, kích hoạt virtualenv ở thư mục ngoài hai cấp:

```powershell
& ..\..\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=analysis/pytest.xml
python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

UI: http://localhost:8501. **Kiểm tra nguồn** chạy local; chat cần API thật.

## Chạy tiếp v2–v6

Sau khi bổ sung hạn mức trong tài khoản provider hoặc cập nhật `.env`:

```powershell
python scripts/complete_lab.py
python scripts/demo_live.py
python scripts/parse_runs.py runs/ --output analysis/all_runs.csv
python scripts/build_report.py
python scripts/package_submission.py
```

Script đầu đọc lại `.env`, dùng snapshot cố định cho từng version, bỏ qua run đã đo đủ,
resume các case provider_error từ run phù hợp, lưu checkpoint sau từng case và dừng
khi provider lỗi. Điểm FAIL của model vẫn là kết quả đã đo; không gọi lại để chọn điểm đẹp.
Chỉ chạy các lệnh tiếp theo khi eval đã có đủ bằng chứng hoặc khi cần ghi rõ trạng thái đang dở.

Provider/model mặc định: OpenRouter / `nvidia/nemotron-3.5-lightning:free`.
Có thể khai báo `LAB_PROVIDER`, `LAB_MODEL`, `OPENROUTER_MODEL`, `GEMINI_MODEL` trong `.env`.
Nếu **đổi provider/model**, chạy lại cả baseline để đối chiếu công bằng:

```powershell
python scripts/complete_lab.py --provider openrouter --model TEN_MODEL --include-baselines
python scripts/demo_live.py --provider openrouter --model TEN_MODEL
```

Không đặt API key trong command, chat, report hoặc ảnh. `.env` không được đưa vào gói nộp.

## Demo nhiều lượt và Telegram

```powershell
python chat.py --provider openrouter --version v6
```

`chat.py` dùng artifact hiện tại (v6). Nếu chạy version khác, phải truyền đúng snapshot:

```powershell
python chat.py --provider openrouter --version v3 --system-prompt artifacts/versions/v3/system_prompt.md --tools artifacts/versions/v3/tools.yaml
```

Transcript thật được lưu tại `transcripts/*.transcript.json`. Demo tự động dùng đầu vào
soạn sẵn nhưng vẫn gọi provider và tool thật; không dùng mock hoặc câu trả lời mẫu.

Telegram cần `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`. UI luôn hiện bản xem trước
và nút xác nhận. CLI yêu cầu `/confirm` cho nội dung vừa xem; một request mới hủy
bản đang chờ xác nhận. Eval luôn vô hiệu hóa gửi để tránh tác dụng ngoài ý muốn.

## Link public và bonus local

Localhost chưa cho phép team khác truy cập từ máy khác. Khi cần chia sẻ, chạy UI,
sau đó dùng hướng dẫn Cloudflare Tunnel trong README, giữ tunnel chạy trong buổi demo,
và ghi URL thực vào REPORT A1. Không ghi một URL chưa được tạo/kiểm tra là link deploy.

Bonus local cần Ollama và ít nhất hai model hỗ trợ tool calling ≤8B, hai vòng
`v4-local`/`v5-local`, kiểm tra ngược trên cloud và log thật. V4–v6 cloud hiện tại
là thí nghiệm thêm, không được tính thay cho các model local. Xem nguyên đề Step 7.
