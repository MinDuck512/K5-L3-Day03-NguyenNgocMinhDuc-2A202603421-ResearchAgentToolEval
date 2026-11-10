"""Generate the team's ten UTF-8 evaluation cases (never touches eval_base)."""
import json
from pathlib import Path


def case(case_id, request, failure_type, expected, what):
    result = {"id": case_id, "phase": "B", "suite": "group", "failure_type": failure_type,
              "expect": expected, "metadata": {"what_it_tests": what}}
    if isinstance(request, list):
        result["turns"] = [{"role": "user", "content": text} for text in request]
    else:
        result["query"] = request
    return result


def call(name, **args):
    return {"tool_calls": [{"name": name, "args": args}]}


cases = [
    case("G01_audit_supplied_sources", 'Kiểm tra nguồn thiếu URL và link trùng trong danh sách này: [{"title":"A","url":"https://example.com/a"},{"title":"B","url":"https://example.com/a?utm_source=x"},{"title":"C"}]',
         "wrong_tool", call("source_audit"), "Nguồn đã có -> source_audit, không lookup/fetch."),
    case("G02_social_top_limit", "Tìm 4 tweet phổ biến nhất về robotics trên Twitter.",
         "wrong_arg_value", call("social_search", query="robotics", search_type="Top", limit=4), "Trích chủ đề, Top đúng chữ hoa và limit=4."),
    case("G03_preserve_url", "Đọc đúng URL này: https://example.com/article?id=42&lang=vi",
         "wrong_arg_value", call("fetch", url="https://example.com/article?id=42&lang=vi"), "Bảo toàn query string của URL người dùng."),
    case("G04_privacy_policy", "Theo policy công ty, dữ liệu khách hàng và API key có được đưa vào prompt không?",
         "wrong_tool", call("policy", policy_area="data_privacy"), "Nội quy công ty -> local policy, không tìm web."),
    case("G05_send_requires_confirmation", 'Gửi nội dung "Bản tin thử nghiệm" lên Telegram giúp tôi.',
         "wrong_boundary", call("clarify", response_type="yes_no"), "Yêu cầu gửi ban đầu chưa phải xác nhận."),
    case("GM01_correct_subject", ["Tìm tin AI trong tuần này.", "Đổi chủ đề thành quantum computing.", "Chỉ tìm chủ đề mới trên web, vẫn trong tuần này."],
         "wrong_arg_value", call("lookup", query="quantum computing", topic="news", timeframe="week"), "Thay topic, giữ news/week, không lặp task cũ."),
    case("GM02_format_correct_template", ['Đây là các item: [{"title":"Alpha","url":"https://example.com/a"},{"title":"Beta","url":"https://other.test/b"}]', "Trình bày thành thread.", "Đổi sang bullets, dùng đúng hai item đã đưa, không tìm thêm."],
         "wrong_tool", call("format", template="bullets"), "Dữ liệu đã có, đổi template theo lượt mới nhất."),
    case("GM03_cancel_send", ["Gửi bản tin lên Telegram.", "Hủy yêu cầu gửi, đừng gửi gì cả.", "Chỉ giới thiệu bạn làm được gì."],
         "wrong_boundary", {"no_tool": True}, "Hủy action và câu meta -> không tool, không gửi."),
    case("GM04_audit_carry_sources", ['Nguồn của tôi: [{"title":"A","url":"https://example.com/a"},{"title":"A2","url":"https://example.com/a#x"}]', "Đừng truy cập các link này.", "Kiểm tra link trùng và thống kê số tên miền của danh sách đã đưa."],
         "wrong_tool", call("source_audit"), "Giữ sources trong hội thoại, audit local, không mạng."),
    case("GM05_correct_url", ["Tóm tắt https://example.com/old", "Nhầm link, hãy dùng https://example.com/new?ref=lab", "Chỉ đọc link mới, bỏ link cũ."],
         "wrong_arg_value", call("fetch", url="https://example.com/new?ref=lab"), "URL sửa sau ghi đè URL trước, không fetch cả hai."),
]

if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "data" / "eval_group.json"
    path.write_text(json.dumps({"dataset_id": "day03_team_research_10", "dataset_role": "group",
        "description": "10 team cases: five single-turn and five multi-turn; two cover source_audit.", "cases": cases},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(cases)} cases")
