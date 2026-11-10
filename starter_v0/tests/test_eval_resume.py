import json
import sys
import run_eval
from providers.base import ModelResponse, ToolCall


def test_resume_retries_provider_errors_without_replaying_measured_cases(monkeypatch, tmp_path):
    cases = [{'id': str(i), 'phase': 'B', 'query': f'Missing URL {i}', 'failure_type': 'missing_info',
              'expect': {'tool_calls': [{'name': 'clarify', 'args': {}}]}} for i in range(2)]
    dataset = tmp_path / 'cases.json'
    dataset.write_text(json.dumps({'cases': cases}), encoding='utf-8')
    argv = ['run_eval.py', '--provider', 'openrouter', '--model', 'fake', '--version', 'v6',
            '--eval-cases', str(dataset), '--runs-dir', str(tmp_path / 'runs')]
    calls = []

    class FailingProvider:
        def complete(self, messages, *args, **kwargs):
            calls.append(messages)
            if len(calls) == 2:
                raise RuntimeError('provider unavailable')
            return ModelResponse(tool_calls=[ToolCall('clarify', {'question': 'URL?'})])

    monkeypatch.setattr(run_eval, 'make_provider', lambda name: FailingProvider())
    monkeypatch.setattr(sys, 'argv', argv)
    run_eval.main()
    original = next((tmp_path / 'runs').glob('*.json'))
    assert json.loads(original.read_text(encoding='utf-8'))['summary']['measured_cases'] == 1
    calls.clear()
    monkeypatch.setattr(sys, 'argv', [*argv, '--resume', str(original)])
    run_eval.main()
    assert len(calls) == 1
    files = [p for p in (tmp_path / 'runs').glob('*.json') if p != original]
    resumed = json.loads(files[0].read_text(encoding='utf-8'))
    assert resumed['summary']['passed_cases'] == resumed['summary']['total_cases'] == 2
    assert resumed['resumed_from'] == str(original)
    assert resumed['execution']['send_enabled'] is False
