"""Build the submission report and checklist strictly from saved evidence."""
from __future__ import annotations

import csv
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
from providers import make_provider

HYPOTHESES = {
    2: 'An explicit yes/no confirmation boundary prevents premature publishing.',
    3: 'Allowing all independent tool calls removes the forced single-tool bottleneck.',
    4: 'Explicit tool descriptions and argument conventions improve routing and argument precision.',
    5: 'An explicit task-state routing procedure resolves corrections and task boundaries.',
    6: 'A dedicated source_audit tool handles supplied-source checks without unnecessary retrieval.',
}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|',
                       *['| ' + ' | '.join(cell(x) for x in row) + ' |' for row in rows]])


def main():
    runs = [(path, read_json(path)) for path in sorted((ROOT / 'runs').glob('*.json'))]
    load_lab_env(ROOT)
    provider = os.getenv('LAB_PROVIDER', 'openrouter')
    model = os.getenv('LAB_MODEL') or make_provider(provider).default_model
    base = {}
    for number in range(7):
        version = f'v{number}'
        candidates = [(path, run) for path, run in runs if run['version'] == version and run['suite'] == 'base'
                      and run['provider'] == provider and run['model'] == model]
        if candidates:
            base[version] = max(candidates, key=lambda pair: (pair[1]['summary']['measured_cases'], pair[0].name))
    tests = {'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
    xml_path = ROOT / 'analysis' / 'pytest.xml'
    if xml_path.exists():
        for suite in ET.parse(xml_path).getroot().iter('testsuite'):
            for key in tests:
                tests[key] += int(suite.get(key, '0'))
    tests_ok = tests['tests'] > 0 and tests['failures'] == tests['errors'] == tests['skipped'] == 0
    version_rows = []
    for number in range(7):
        version = f'v{number}'
        hypothesis = {0: 'Baseline starter', 1: 'Clarify essential missing information instead of guessing.'}.get(number, HYPOTHESES.get(number))
        entry = base.get(version)
        if entry:
            path, run = entry
            s = run['summary']
            complete = s['measured_cases'] == 20
            status = 'Đã đo đủ' if complete else 'Chưa đủ: provider bị giới hạn'
            metrics = f"{s['passed_cases']}/{s['measured_cases']} đã đo; coverage {s['measured_cases']}/20"
            link = str(path.relative_to(ROOT)).replace('\\', '/')
            routing, argument, multi = [s.get(k, '—') for k in ['tool_routing_accuracy', 'argument_accuracy', 'multiturn_accuracy']]
        else:
            status, metrics, link, routing, argument, multi = 'Đã chuẩn bị; chưa đo', '—', '—', '—', '—', '—'
        version_rows.append([version, hypothesis, status, metrics, routing, argument, multi, link])

    log_path = ROOT / 'artifacts' / 'version_log.csv'
    with log_path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        logs = [row for row in reader if (ROOT / row['run_file']).is_file()]
    known_runs = {row['run_file'].replace('\\', '/') for row in logs}
    for path, run in runs:
        relative = str(path.relative_to(ROOT)).replace('\\', '/')
        if relative in known_runs:
            continue
        version = run['version']
        if version not in {f'v{i}' for i in range(2, 7)}:
            continue
        number = int(version[1:])
        summary = run['summary']
        prior = base.get(f'v{number-1}')
        before = prior[1]['summary']['case_accuracy'] if prior and prior[1]['summary']['measured_cases'] == 20 and run['suite'] == 'base' else ''
        logs.append({**{key: run.get(key, '') for key in ['version', 'artifact_version', 'prompt_hash', 'tools_hash']},
                     'author': 'workspace', 'changed_artifact': 'tools.yaml' if number in {4, 6} else 'system_prompt.md',
                     'reason': f"{run['provider']} / {run['model']}; suite={run['suite']}; measured {summary['measured_cases']}/{run.get('dataset_total_cases', summary['total_cases'])}; provider errors {summary['provider_error_cases']}. Accuracy denominator is measured cases only.",
                     'hypothesis': HYPOTHESES[number], 'metric_before': before, 'metric_after': summary['case_accuracy'], 'run_file': relative})
    with log_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(logs)

    failure_rows, tool_errors = [], []
    for version, (path, run) in base.items():
        for item in run['results']:
            result = item['result']
            if not result['passed']:
                failure_rows.append([version, item['id'], result.get('case_failure_type'), result.get('observed_mismatch'),
                    json.dumps(result.get('actual_tool_calls', []), ensure_ascii=False), '; '.join(result['failures'])])
            for event in item.get('tool_results', []):
                if isinstance(event.get('result'), dict) and event['result'].get('error'):
                    tool_errors.append([version, item['id'], event['tool'], event['result']['error']])
    with (ROOT / 'analysis' / 'all_failures.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['version', 'case_id', 'case_failure_type', 'observed_mismatch', 'actual_calls', 'failures'])
        writer.writerows(failure_rows)
    groups = [(p, r) for p, r in runs if r['version'] == 'v6' and r['suite'] == 'group'
              and r['provider'] == provider and r['model'] == model]
    group_results = {item['id']: item['result'] for item in groups[-1][1]['results']} if groups else {}
    group_cases = read_json(ROOT / 'data' / 'eval_group.json')['cases']
    group_rows = [[c['id'], 'multi' if 'turns' in c else 'single', c['metadata']['what_it_tests'],
                   ', '.join(t['name'] for t in c['expect'].get('tool_calls', [])) or 'no_tool',
                   ('PASS' if group_results[c['id']]['passed'] else 'FAIL') if c['id'] in group_results else 'Chưa đo'] for c in group_cases]
    live_rows, live_ok = [], False
    for path in sorted((ROOT / 'transcripts').glob('*.transcript.json')):
        transcript = read_json(path)
        turns = transcript.get('turns', [])
        successful = [turn for turn in turns if turn.get('status') not in {'provider_error', 'started'}]
        live_ok = live_ok or len(successful) >= 3
        for turn in turns:
            live_rows.append([str(path.relative_to(ROOT)).replace('\\', '/'), turn.get('turn_index', '—'),
                              turn['user'], ', '.join(e['tool'] for e in turn.get('tool_events', [])), turn.get('status', '—')])
    mandatory_evals = all(v in base and base[v][1]['summary']['measured_cases'] == 20 for v in ['v1', 'v2', 'v3'])
    all_six = all(v in base and base[v][1]['summary']['measured_cases'] == 20 for v in [f'v{i}' for i in range(1, 7)])
    tool_rows = [
        ['clarify', 'Hỏi bổ sung hoặc xin xác nhận; chờ người dùng.', 'Có sẵn'],
        ['timeline', 'Lấy bài X/Twitter do một tài khoản đăng.', 'Có sẵn'],
        ['social_search', 'Tìm bài X/Twitter theo chủ đề, Top/Latest.', 'Có sẵn'],
        ['lookup', 'Tìm thông tin/tin tức web qua Tavily.', 'Có sẵn'],
        ['fetch', 'Đọc một URL qua Firecrawl.', 'Có sẵn'],
        ['format', 'Trình bày các item đã có, giữ link nguồn.', 'Có sẵn'],
        ['send', 'Gửi Telegram sau thao tác xác nhận cụ thể.', 'Có sẵn; đã sửa guardrail'],
        ['policy', 'Tra handbook nội bộ giả lập có sẵn trong lab.', 'Có sẵn'],
        ['papers', 'Tìm paper arXiv theo chủ đề.', 'Có sẵn'],
        ['paper_text', 'Đọc PDF arXiv xác định, trích text tại máy.', 'Có sẵn'],
        ['source_audit', 'Kiểm tra link thiếu/trùng và số tên miền; không xác minh fact.', 'Mới tự viết'],
    ]
    v2_summary = base.get('v2', (None, {'summary': {}}))[1]['summary']
    v2_note = (f"V2 đang có {v2_summary.get('passed_cases', 0)}/{v2_summary.get('measured_cases', 0)} case đã đo, coverage {v2_summary.get('measured_cases', 0)}/20."
               if v2_summary else 'V2 chưa có run trên model đang chọn.')
    r12_measured = any(item['id'] == 'R12_confirm_before_send' and item['result'].get('failure_type') != 'provider_error'
                       for item in base.get('v2', (None, {'results': []}))[1]['results'])
    report = f'''# Day 03 — Research Desk: báo cáo theo bằng chứng

Ngày cập nhật: 10/11/2026 (Asia/Saigon). Người thực hiện: workspace NgNgocMinhDuc_93; chưa nhận danh sách nhóm.

## PHẦN A — Giới thiệu agent

### A1. Công dụng và link dùng thử

Research Desk tìm tin web, bài X/Twitter, paper arXiv và policy nội bộ; đọc URL rồi tổng hợp có nguồn. Agent hỏi lại khi thiếu dữ kiện và yêu cầu người dùng xem, xác nhận chính xác nội dung trước khi gửi Telegram.

- UI cục bộ: http://localhost:8501 (chỉ dùng trên máy đang chạy ứng dụng).
- Chạy UI: `python -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false`.
- Link public: chưa tạo; localhost chưa đáp ứng việc team khác truy cập từ máy khác.
- Tab **Kiểm tra nguồn** chạy offline. Chat cần provider/tool API còn quota; không dùng câu trả lời dựng sẵn khi API lỗi.
- Không thể xác nhận hoàn thành deadline lớp học 16:30 từ các file hiện có; thời điểm hiện tại không được dùng làm bằng chứng đã nộp đúng hạn.

### A2. Công cụ

{table(['Tool', 'Công dụng', 'Nguồn'], tool_rows)}

### A3. Câu hỏi mẫu

1. Tin AI hôm nay có gì nổi bật trên web và Twitter?
2. Lấy 3 tweet mới nhất của @karpathy.
3. Tóm tắt link: https://www.anthropic.com/research
4. Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?
5. Kiểm tra link trùng trong `[{{"url":"https://example.com/a"}},{{"url":"https://example.com/a#x"}}]`.

## PHẦN B — Chi tiết và bằng chứng

### B1. Các phiên bản v0–v6

Bảng chính chỉ so model `{provider}/{model}`. V4–v6 là các thí nghiệm cloud bổ sung theo yêu cầu; không thay thế bonus local v4-local/v5-local. Snapshot đã chuẩn bị không đồng nghĩa thí nghiệm đã hoàn thành.

{table(['Version', 'Giả thuyết', 'Trạng thái', 'PASS / coverage', 'Routing', 'Args', 'Multi', 'Run JSON'], version_rows)}

`artifacts/version_log.csv` ghi run thật; giả thuyết và trạng thái các bản chưa chạy nằm trong bảng trên. Hash prompt/tools nằm trong run JSON và version_log. V2 giữ nội dung schema giống v1 nhưng có đổi newline khi lưu snapshot, vì vậy tools_hash khác; không coi đây là cải tiến schema. Các bản từ v2 dùng code tool đã sửa; bộ đề base và hàm chấm không đổi. Giãn cách/retry khác các run cũ được lưu trong execution, nên không khẳng định mọi khác biệt điểm đều do prompt.

Lịch sử OpenRouter: v0 12/20; v1 13/20. {v2_note} Run thiếu coverage không chứng minh chất lượng trên cả suite. Thư mục runs giữ cả log lịch sử Gemini và lần retry để bảo toàn bằng chứng; chúng không được dùng để so sánh chất lượng với baseline OpenRouter đầy đủ.

### B2. Phân tích lỗi

CSV phân loại lỗi: `analysis/all_failures.csv`. Bảng từng case của mọi run: `analysis/all_runs.csv`. Đọc thêm actual_tool_calls và tool_results trong run JSON khi cần chi tiết.
Ghi chú thiết lập và phân tích trước đây được giữ tại `analysis/history/`; các kết luận cần cho bài nộp đã được tập trung trong báo cáo này.

- V1 có bốn case chuyển FAIL → PASS: R08, R10, R11, M02; ba case chuyển PASS → FAIL: R01, R09, M03. Hai case mục tiêu thiếu dữ kiện R10/R11 được sửa. Tổng tăng 5 điểm phần trăm từ một lần đo, chưa chứng minh độ ổn định.
- Chấm args dùng subset và chuỗi chính xác sau strip/lower. Query "AI news today" khác "AI" vẫn FAIL; giữ nguyên phép chấm, hướng dẫn tách query/topic/timeframe ở v4.
- V2 kiểm tra xác nhận gửi; R12 {'đã có kết quả trong run được chọn, xem CSV' if r12_measured else 'chưa được đo vì quota đã hết; chưa kiểm chứng giả thuyết chính'}.
- Routing PASS không chứng minh tool/API thực thi thành công. Các error dict được thống kê riêng bên dưới; source_audit chỉ kiểm tra cấu trúc URL, không xác minh sự thật hoặc tính độc lập nguồn.

{table(['Version', 'Case', 'Tool', 'Lỗi thực thi'], tool_errors) if tool_errors else 'Không có error dict tool trong các run được chọn.'}

### B3. Bộ eval nhóm

Đúng 10 case mới: 5 single-turn + 5 multi-turn; G01/GM04 kiểm tra route đến source_audit. Đã kiểm tra contract offline; chưa có run thì ghi Chưa đo.

{table(['ID', 'Loại', 'Nội dung kiểm tra', 'Kỳ vọng', 'Kết quả'], group_rows)}

### B4. Live chat

{table(['Transcript', 'Lượt', 'Yêu cầu', 'Tools', 'Trạng thái'], live_rows) if live_rows else 'Chưa có transcript live đạt yêu cầu. Không tính sample/mock làm bằng chứng thật.'}

Đủ ≥3 lượt thành công trong cùng transcript: **{'Có' if live_ok else 'Chưa'}**. Chạy `python chat.py --provider {provider} --model {model} --version v6` để ghi phiên live với provider/tool thật; nhập `/exit` khi kết thúc.

### B5. Code, UI và unit test

- Pytest: **{tests['tests']} tests; {tests['failures']} failed; {tests['errors']} errors; {tests['skipped']} skipped** (`analysis/pytest.xml`).
- Thay toàn bộ 17 stub skip bằng test thật; source_audit có happy path, input xấu, lỗi vận hành và regression URL; mọi HTTP trong unit test đều được mock.
- Bug bắt được bằng unit test: `confirmed="false"` trước đây là truthy nên có thể gửi; nay chỉ nhận boolean True và UI/CLI cần thao tác xác nhận riêng. Eval luôn vô hiệu hóa gửi thật.
- `limit=0`, `top_k=0`, `max_results=0` trước đây bị đổi sang mặc định; nay trả ValueError, số dạng chuỗi nguyên được chấp nhận. Enum sai, URL/handle sai và items sai kiểu được kiểm tra trước mạng.
- `send` chỉ báo sent khi Telegram trả ok=true; gửi text literal để tránh lỗi Markdown; token trong thông báo lỗi được che.
- `paper_text` kiểm tra URL arXiv đúng host và giới hạn trang/ký tự trước tải; test happy path đọc/ghi text là offline.
- Loop trả kết quả sau format, giữ bằng chứng qua các lượt và có giới hạn số vòng. Eval lưu checkpoint mỗi case, resume chỉ retry lỗi provider và từ chối nếu artifact/dataset khác.
- UI dùng cùng loop với CLI; tab offline được kiểm tra bằng Streamlit AppTest (`tests/test_app.py`). Bảng Markdown tránh DLL pyarrow bị Windows Application Control chặn. Không tắt hay thay đổi chính sách Windows. Kiểm tra trực quan qua Computer Use bị dừng vì công cụ không xác định được URL trình duyệt; không có ảnh xác nhận UI thật.
- UI localhost đã chạy. Telegram live chưa cấu hình bot/chat; không thực hiện gửi thật. Bonus hơn 3 tool mới chưa làm (hiện có 1 tool mới, đủ yêu cầu bắt buộc).

Các sửa chữa và giới hạn kiểm tra được tập trung trong mục này để tránh nhiều báo cáo trùng nhau.

### B6. Nhận xét và giới hạn

Prompt và tool description cần phân biệt tác giả/chủ đề, thời gian/query, thông tin thiếu và xác nhận hành động. Dữ liệu nhiều lượt cần áp dụng sửa đổi mới nhất thay vì lặp lại task cũ. Đây là giả thuyết thiết kế cho v3–v6 cho đến khi có đủ run để kết luận. Test offline chứng minh code hoạt động trên các tình huống đã kiểm tra; không thay thế đánh giá model/API.

Các lần chạy v2 đã gặp HTTP 429 do hạn mức provider; xem failures trong run JSON. Người dùng cho biết sẽ bổ sung hạn mức/provider trong .env. Chạy `python scripts/complete_lab.py` để đọc lại cấu hình và thu tiếp bằng chứng; nếu đổi model/provider nên thêm `--include-baselines` để có đối chứng cùng model (runner tự bổ sung nếu thiếu baseline). Sau đó chạy chat.py để có ≥3 lượt live và `python scripts/build_report.py` để cập nhật báo cáo.

### B7. Bonus Small Local Model

Ollama chưa có lệnh và localhost:11434 chưa có server/model ở lần kiểm tra. Chưa chạy hai model ≤8B, v4-local/v5-local hoặc kiểm tra ngược trên cloud; không ghi kết quả giả. Cần cài/chuẩn bị Ollama và hai model phù hợp nếu muốn hoàn thành bonus này. Không tải model nhiều GB khi chưa có lựa chọn của người dùng.

## Trạng thái bàn giao

- Prompt/schema và code v1–v6: đã chuẩn bị, có snapshot và giả thuyết.
- Eval bắt buộc v1–v3 đo đủ: **{'Đủ' if mandatory_evals else 'Chưa đủ'}**; v1–v6 đo đủ: **{'Đủ' if all_six else 'Chưa đủ'}**.
- Unit test 0 failed/0 skipped: **{'Đạt' if tests_ok else 'Chưa có xác nhận'}**.
- Còn phụ thuộc bên ngoài: quota/provider live; link public; Telegram live và local models nếu làm bonus.
- `.env`, thư mục `.venv` và cache không được đưa vào bài nộp. Giữ chúng tại máy nếu cần để chạy; nộp code, artifacts, data, tests, runs, transcripts và analysis.

## Tài liệu kỹ thuật đã đối chiếu

- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search): query/topic/time_range/max_results.
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest): kiểm tra UI offline.
- [OpenRouter limits](https://openrouter.ai/docs/api_reference/limits): kiểm tra quyền truy cập/hạn mức; lỗi provider thực tế nằm trong run JSON.
'''
    (ROOT / 'artifacts' / 'REPORT.md').write_text(report, encoding='utf-8')
    todo_rows = [
        ['Provider và preflight', 'Đã có lịch sử PASS; run v2 gặp quota', 'scripts/preflight_provider.py; runs/v2*.json'],
        ['Baseline và phân loại lỗi', 'Đạt', 'v0/v1 JSON; analysis/all_failures.csv'],
        ['Bỏ chỉ dẫn xấu, routing, descriptions/args', 'Đạt về artifact; chờ eval đầy đủ', 'artifacts/versions/v2–v6'],
        ['v1/v2/v3 một giả thuyết + metric thật', 'Đạt' if mandatory_evals else 'Chưa đủ', 'version_log.csv; không lấy 7/10 làm 7/20'],
        ['v4/v5/v6 theo yêu cầu bổ sung', 'Đủ bằng chứng' if all_six else 'Đã chuẩn bị; chưa đo đủ', 'artifacts/REPORT.md B1; artifacts/versions/'],
        ['Tool mới + TOOL.md + registry + schema', 'Đạt: source_audit', 'tools/source_audit; artifacts/tools.yaml'],
        ['≥3 tests/tool mới; tất cả TODO stubs', 'Đạt' if tests_ok else 'Chờ kiểm tra', 'tests/test_tools_todo.py; analysis/pytest.xml'],
        ['10 group case, 5 single + 5 multi', 'Đã viết; ' + ('có run' if groups else 'chưa đo live'), 'data/eval_group.json'],
        ['Pytest 0 failed, 0 skipped', 'Đạt' if tests_ok else 'Chưa xác nhận', str(tests)],
        ['UI Streamlit + link', 'Local đã chạy; public chưa tạo', 'http://localhost:8501; tests/test_app.py'],
        ['Chat live ≥3 lượt + transcript', 'Đạt' if live_ok else 'Chưa đủ bằng chứng', 'chat.py; transcripts/'],
        ['REPORT A/B', 'Đã điền trạng thái thật; số liệu còn chờ quota', 'artifacts/REPORT.md'],
        ['Bonus send confirmation', 'Code + mock tests đạt; Telegram live chưa cấu hình', 'tests/test_chat.py; tools/send'],
        ['Bonus hơn 3 tool mới', 'Chưa làm; không bắt buộc', 'Hiện có 1 tool mới'],
        ['Bonus 2 model local + tối ưu', 'Chưa có Ollama/server/model', 'REPORT B7'],
    ]
    todo = '# Đối chiếu TODO — 10/11/2026\n\nTrạng thái được dựng từ file thật; chưa đo không được đánh dấu hoàn thành.\n\n'
    todo += table(['Yêu cầu', 'Trạng thái', 'Bằng chứng'], todo_rows)
    todo += f'\n\nTiếp tục: `python scripts/complete_lab.py` → `python chat.py --provider {provider} --model {model} --version v6` (ít nhất 3 lượt) → `python scripts/parse_runs.py runs/ --output analysis/all_runs.csv` → `python scripts/build_report.py`.\n'
    (ROOT / 'analysis' / 'TODO_STATUS.md').write_text(todo, encoding='utf-8')
    print('Updated REPORT, TODO_STATUS, version_log and failure analysis from evidence.')


if __name__ == '__main__':
    main()
