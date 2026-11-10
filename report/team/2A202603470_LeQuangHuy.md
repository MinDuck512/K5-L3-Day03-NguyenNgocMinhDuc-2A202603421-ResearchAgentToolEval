# Báo cáo cá nhân - Lê Quang Huy (MSSV: 2A202603470)

## 1. Công việc đã thực hiện
- Đã chạy và đánh giá các phiên bản agent từ `v1` đến `v7` trên các tập test (`eval_group.json`, `eval_research_extension.json`).
- Đã cấu hình các API key cần thiết (`TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`) trong `.env` và xác thực qua preflight test.
- Sử dụng công cụ Antigravity để hỗ trợ theo dõi, tối ưu hóa quá trình chạy eval và đối chiếu prompt hash giữa các version.

## 2. Thấu hiểu các Version & Failure Analysis
- **Phiên bản v7:** Đạt kết quả cải thiện rõ rệt so với các phiên bản trước nhờ việc tinh chỉnh prompt và tối ưu cách agent gọi tool.
- **Các trường hợp thất bại (Failure Cases):** Phát hiện một số lỗi liên quan đến quá tải tài nguyên / timeout từ phía API provider (`RESOURCE_EXHAUSTED` / `429`). Hướng cải thiện là thêm cơ chế retry/backoff tự động khi gọi API.

## 3. Tự kiểm chứng (Self-Verification)
- Đã chạy bộ test contract bằng `pytest` (108 passed).
- Chạy thử giao diện Streamlit UI để đảm bảo hệ thống tương tác bình thường.