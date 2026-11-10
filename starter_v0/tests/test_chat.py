from providers.base import ModelResponse, ToolCall
from agent import ResearchAgent
from chat import run_model_tool_loop


class SequenceProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, messages, tools=None, **kwargs):
        self.requests.append((messages, tools))
        return next(self.responses)


def run(provider, rounds=3):
    return run_model_tool_loop(provider=provider, messages=[{'role': 'user', 'content': 'test'}],
                               tools=[], model='fake', max_tool_rounds=rounds)


def test_clarify_stops_before_other_tools_execute(monkeypatch):
    provider = SequenceProvider([ModelResponse(tool_calls=[ToolCall('clarify', {'question': 'URL?'}), ToolCall('send', {'text': 'bad', 'confirmed': True})])])
    result = run(provider)
    assert result['status'] == 'waiting_for_user'
    assert len(result['tool_events']) == 1
    assert len(provider.requests) == 1


def test_generated_send_boolean_only_creates_a_preview(fake_http):
    from conftest import FakeResponse
    calls = fake_http(FakeResponse())
    result = run(SequenceProvider([ModelResponse(tool_calls=[ToolCall('send', {'text': 'Preview', 'confirmed': True})])]))
    assert result['status'] == 'waiting_for_confirmation'
    assert result['pending_action']['text'] == 'Preview'
    assert calls == []


def test_format_result_is_available_for_final_answer():
    provider = SequenceProvider([ModelResponse(tool_calls=[ToolCall('format', {'items': [{'title': 'A'}], 'template': 'bullets'})]), ModelResponse(text='- A')])
    result = run(provider)
    assert result['assistant_text'] == '- A'
    assert 'markdown' in provider.requests[1][0][-1]['content']


def test_round_budget_ends_with_tools_disabled():
    provider = SequenceProvider([ModelResponse(tool_calls=[ToolCall('format', {'items': []})]), ModelResponse(text='No items')])
    result = run(provider, rounds=1)
    assert result['status'] == 'max_tool_rounds'
    assert result['assistant_text'] == 'No items'
    assert provider.requests[-1][1] == []


def test_eval_does_not_send_even_if_model_invents_approval(fake_http):
    from conftest import FakeResponse
    calls = fake_http(FakeResponse())
    provider = SequenceProvider([ModelResponse(tool_calls=[ToolCall('send', {'text': 'bad', 'confirmed': True})])])
    result = ResearchAgent(provider, system_prompt='test').run([])
    assert result.tool_results[0]['result']['status'] == 'action_disabled'
    assert calls == []
