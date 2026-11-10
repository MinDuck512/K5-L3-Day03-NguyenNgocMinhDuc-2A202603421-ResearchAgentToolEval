# Lần thử chạy lại v0 bị dừng

- Giữ nguyên prompt/tools của baseline, model yêu cầu gemini-3.5-flash.
- Đã chạy tới R09_no_tool_capability; stdout ghi `Provider HTTP 429; retry 1/3 in 14130.0s`.
- 14130 giây tương đương 3 giờ 55 phút 30 giây. Đã dừng tiến trình thay vì để chờ nhiều giờ.
- Tiến trình bị dừng trước khi ghi JSON tổng kết; không đưa lần này vào bảng metric và không tính là v1.
- Đã sửa retry để giới hạn thời gian chờ mặc định 60 giây. Khi server yêu cầu lâu hơn, ghi nhận lỗi thay vì thử lại sớm hoặc chờ vô hạn.
- Run v0 đầu tiên và toàn bộ bằng chứng của nó vẫn được giữ.
