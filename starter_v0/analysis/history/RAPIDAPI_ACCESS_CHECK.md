# Kiểm tra quyền Twitter API

- Endpoint: `https://twitter-api45.p.rapidapi.com/timeline.php?screenname=sama`.
- HTTP status thực tế: **403**.
- Thông báo từ API: `You are not subscribed to this API.`
- Người dùng xác nhận đã đăng ký đúng API; cần đối chiếu subscription với tài khoản/team và App/Key đang được sử dụng.
- Không lưu API key hoặc headers xác thực vào báo cáo.

Bước xử lý: mở đúng trang API, chọn đúng tài khoản/team đã subscribe, kiểm tra trạng thái subscription, chọn App/Key tương ứng trong Endpoints, dùng Test Endpoint. Khi thành công mới sao chép key tương ứng vào cấu hình local và thử lại tool.

## Kiểm tra lại với cùng key đang lưu

- Endpoint `/timeline.php?screenname=sama` hiện trả **HTTP 200**.
- Response có các trường `timeline`, `next_cursor`, `prev_cursor`, `status`, `user`.
- Không cần thay key cho endpoint này. Kết quả mới không thay đổi bằng chứng HTTP 403 đã ghi trong run v0 cũ.
- Endpoint social search chưa được kiểm tra lại trong lần kiểm tra này.

## Bằng chứng từ baseline OpenRouter đầy đủ

Run `runs/v0_B_base_openrouter_20261110T124056248410.json` đã gọi cả timeline và social_search; không có error dict trong tool_results. Các lỗi HTTP 403 của run Gemini cũ được giữ làm lịch sử.
