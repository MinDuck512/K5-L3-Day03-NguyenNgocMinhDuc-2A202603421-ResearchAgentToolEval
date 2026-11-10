# BÁO CÁO CÁ NHÂN — DƯƠNG TUẤN HÙNG

- **Họ và tên:** Dương Tuấn Hùng
- **MSSV:** 2A202603416
- **Dự án:** Research Desk — Trợ lý AI tìm kiếm và tổng hợp thông tin (Day 03 Lab v2)
- **Nhánh phụ trách:** `feature/DuongTuanHung-2A202603416`

---

## 1. Công việc em đã làm

- **Thiết lập môi trường & Cấu hình Provider:** Cài đặt môi trường ảo `.venv`, cấu hình kết nối API OpenRouter (`openai/gpt-4o-mini`) giúp agent chạy ổn định, tốc độ cao và vượt qua lỗi giới hạn quota 429 của nhà cung cấp ban đầu.
- **Tối ưu Prompt & Khai báo Tool (Routing & Safety Guardrail):**
  - Chỉnh sửa `artifacts/system_prompt.md`: Xóa bỏ các chỉ dẫn xấu gây đoán mò và ép hành động 1 bước; bổ sung các quy tắc định tuyến phân biệt rõ giữa tìm kiếm cá nhân (`timeline`), chủ đề mạng xã hội (`social_search`), tin tức web (`lookup`) và đọc liên kết (`fetch`).
  - Thiết lập ranh giới an toàn (Guardrail): Bắt buộc Agent phải dừng lại gọi `clarify(response_type="yes_no")` để xin xác nhận từ người dùng trước khi gửi tin nhắn qua Telegram (`send`), cấm gửi tự tiện.
  - Tinh chỉnh `artifacts/tools.yaml`: Làm rõ mô tả khi nào dùng/không dùng, quy chuẩn tham số `timeframe="day"` cho tin tức hôm nay và `screenname` không chứa ký tự `@`.
- **Phát triển Tool mới (`calculator`):**
  - Tự lập trình công cụ `calculator` (nằm trong thư mục `tools/calculator/`) sử dụng Python AST để thực hiện tính toán số học, tỷ lệ tăng trưởng doanh thu, căn bậc hai an toàn cho dữ liệu nghiên cứu.
  - Bổ sung cơ chế phòng thủ: Tự động bắt lỗi chia cho 0 (`ZeroDivisionError`) và ngăn chặn mã độc injection mà không làm sập chương trình.
  - Đăng ký công cụ vào `tools/__init__.py` và khai báo schema trong `artifacts/tools.yaml`.
- **Viết Unit Test & Đảm bảo chất lượng Code:**
  - Viết 3 unit tests cho tool mới trong `tests/test_tools_todo.py` (happy path, xử lý input xấu/rỗng, và bắt lỗi trả về error dict).
  - Giữ toàn bộ test suite `pytest` luôn xanh, đạt chuẩn hợp đồng với `test_tool_contract.py`.
- **Xây dựng Test Cases nhóm & Đánh giá năng lực:**
  - Thiết kế và đóng góp 10 kịch bản kiểm thử vào `data/eval_group.json` (5 ca đơn lượt single-turn và 5 ca đa lượt multi-turn), bao quát các trường hợp tính toán số liệu, chuyển hướng tool, và tình huống ngoài phạm vi.
- **Xây dựng Giao diện Demo & Poster trình chiếu:**
  - Cài đặt thư viện Streamlit và hoàn thiện file giao diện Web Chat `app.py` trực quan, hiển thị chi tiết quá trình gọi tool, tham số và kết quả JSON.
  - Thiết kế trang poster HTML (`artifacts/poster.html`) giao diện tối hiện đại phục vụ trình chiếu trong buổi Team Showdown.

---

## 2. Kết quả đạt được

- **Chất lượng Tool & Unit Tests:** Bộ kiểm thử `pytest` đạt **70/70 test xanh (0 failed)**, đáp ứng toàn bộ hợp đồng khai báo công cụ.
- **Tiến trình tối ưu hóa Agent:**
  - **Phiên bản Baseline v0:** Đạt **70%** (14/20 ca) với lỗi chính là tự tiện gọi tool khi làm thơ/viết code và tự bịa link/tài khoản.
  - **Phiên bản v1 (Tối ưu Prompt):** Độ chính xác định tuyến công cụ (`tool_routing_accuracy`) tăng vọt lên **95%**; giải quyết triệt để các ca lỗi out-of-scope.
  - **Phiên bản v2 (Tối ưu Schema & Multi-turn):** Đạt điểm tuyệt đối **20/20 PASS (100% Case Accuracy)** trên bộ kiểm thử chuẩn `eval_base.json`.
- **Đánh giá Bộ test nhóm (`eval_group.json`):** Đạt **90%** (9/10 ca PASS), kích hoạt thành công tool `calculator` và nhận diện chuẩn xác ý định người dùng qua nhiều lượt hội thoại.
- **Sản phẩm bàn giao:** Giao diện Streamlit hoạt động hoàn chỉnh tại `http://localhost:8501`, sẵn sàng kết nối Cloudflare Tunnel để demo công khai.

---

## 3. Khó khăn gặp phải & Cách giải quyết

- **Khó khăn 1 — Giới hạn hạn mức API (Rate Limit 429):** Khi chạy các vòng kiểm thử ban đầu với Gemini Free Tier, hệ thống nhanh chóng bị cạn quota requests/ngày.
  - *Giải pháp:* Đã linh hoạt chuyển đổi provider sang OpenRouter (`openai/gpt-4o-mini`) giúp việc đánh giá diễn ra liên tục, không bị ngắt quãng.
- **Khó khăn 2 — Lỗi 403 Forbidden từ RapidAPI Twitter:** Khi test gọi tweet qua `timeline`, RapidAPI chặn kết nối với thông báo chưa đăng ký.
  - *Giải pháp:* Xác định nguyên nhân do tài khoản chưa kích hoạt gói miễn phí trên sàn RapidAPI, đã cấu hình đăng ký gói Basic ($0) của `twitter-api45` để lấy dữ liệu thực tế thành công.
- **Khó khăn 3 — Model bị ảo giác tham số (Hallucination):** Khi thiếu URL hoặc tên tài khoản, model có xu hướng tự điền thông tin giả định.
  - *Giải pháp:* Thiết lập ràng buộc chặt chẽ trong `system_prompt.md`, ép buộc model phải gọi `clarify` để hỏi lại thay vì tự phỏng đoán.

---

## 4. Bài học rút ra

1. **Evidence-Driven Development:** Mọi quyết định sửa đổi prompt hay schema phải dựa trên phân tích run log JSON thực tế (`failures`, `observed_mismatch`) thay vì cảm tính.
2. **Vai trò phối hợp giữa Prompt và Schema:** Prompt định hướng luồng suy nghĩ và nguyên tắc an toàn, nhưng mô tả schema chi tiết trong `tools.yaml` mới là yếu tố quyết định độ chính xác của tham số (đặc biệt là các trường enum như `response_type`, `timeframe`).
3. **Nguyên tắc an toàn (Guardrail):** Các công cụ có tác động ngoại vi (gửi tin, xuất bản) luôn cần cơ chế xác nhận 2 bước từ con người để tránh rủi ro phát tán thông tin sai lệch hoặc spam.

---
*Xem thêm chi tiết bằng chứng thực nghiệm trong [báo cáo tổng hợp của nhóm](group_report.md).*

