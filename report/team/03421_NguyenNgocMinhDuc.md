# BÁO CÁO CÁ NHÂN — NGUYỄN NGỌC MINH ĐỨC

- **MSSV:** 2A202603421
- **Dự án:** Research Desk — Trợ lý AI tìm kiếm và tổng hợp thông tin

## 1. Công việc em đã làm

- Cài đặt môi trường Python và cấu hình API để chạy dự án.
- Chỉnh sửa hướng dẫn cho AI để chọn đúng công cụ, hỏi lại khi thiếu thông tin và xin xác nhận trước khi gửi Telegram.
- Viết công cụ `source_audit` để tìm link thiếu, loại link trùng và đếm số tên miền. Công cụ chỉ kiểm tra link, không xác minh nội dung.
- Sửa lỗi xử lý dữ liệu đầu vào và bổ sung các bài kiểm thử tự động.
- Viết 10 tình huống thử AI, gồm 5 tình huống một lượt và 5 tình huống nhiều lượt hội thoại.
- Xây dựng giao diện Streamlit; lưu kết quả chạy và tổng hợp báo cáo.

## 2. Kết quả đạt được

- Bộ kiểm thử code: **148 bài đạt, không có bài lỗi hoặc bị bỏ qua**.
- Phiên bản ban đầu v0: đạt **12/20** tình huống.
- Phiên bản v1: đạt **13/20** tình huống, tăng từ **60% lên 65%** trong lần chạy đã ghi nhận.
- Phiên bản v2: đạt **7/10** tình huống đã chạy; còn 10 tình huống chưa đo nên chưa thể kết luận tốt hơn v1.

## 3. Khó khăn và việc còn thiếu

API bị giới hạn lượt gọi nên em chưa chạy đủ v2. Các bản v3–v6 đã chuẩn bị nhưng chưa có kết quả thực tế; bộ 10 tình huống của nhóm cũng chưa chạy. Ngoài ra, còn thiếu 3 lượt chat thành công được lưu lại và link giao diện công khai.

Em cần chạy tiếp các phần còn thiếu và cập nhật báo cáo theo kết quả thực tế.

## 4. Bài học rút ra

Em học được cách viết hướng dẫn rõ ràng cho AI, đọc log để tìm lỗi và kiểm tra công cụ trước khi sử dụng. Code chạy đúng chưa có nghĩa AI luôn chọn đúng công cụ, vì vậy cần kiểm tra cả hai. Khi báo cáo, em cần phân biệt rõ phần đã hoàn thành và phần chưa có kết quả.

Xem bằng chứng chi tiết trong [báo cáo nhóm](group_report.md).
