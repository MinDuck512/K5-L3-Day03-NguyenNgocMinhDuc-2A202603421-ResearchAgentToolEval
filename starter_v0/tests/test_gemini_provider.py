import sys
from types import ModuleType, SimpleNamespace
from providers.gemini_provider import GeminiProvider


def install_sdk(monkeypatch, response):
    requests = []
    def generate_content(**kwargs):
        requests.append(kwargs)
        return response
    def fields(**kwargs):
        return kwargs
    google = ModuleType('google')
    genai = ModuleType('google.genai')
    genai.Client = lambda **kw: SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    genai.types = SimpleNamespace(Tool=fields, GenerateContentConfig=fields, ToolConfig=fields, FunctionCallingConfig=fields)
    google.genai = genai
    monkeypatch.setitem(sys.modules, 'google', google)
    monkeypatch.setitem(sys.modules, 'google.genai', genai)
    monkeypatch.setenv('GEMINI_API_KEY', 'fake')
    return requests


def test_gemini_preserves_repeated_calls_but_does_not_double_count_mirror(monkeypatch):
    call = SimpleNamespace(name='fetch', args={'url': 'https://example.com'})
    response = SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[
        SimpleNamespace(function_call=call, text=None), SimpleNamespace(function_call=call, text=None)]))],
        function_calls=[call, call])
    captured = install_sdk(monkeypatch, response)
    result = GeminiProvider().complete([{'role': 'user', 'content': 'x'}],
        [{'type': 'function', 'function': {'name': 'fetch'}}], tool_choice='required')
    assert len(result.tool_calls) == 2
    assert captured[0]['config']['tool_config']['function_calling_config']['mode'] == 'ANY'


def test_gemini_falls_back_to_function_calls_when_parts_are_absent(monkeypatch):
    response = SimpleNamespace(candidates=[], function_calls=[SimpleNamespace(name='clarify', args={'question': 'URL?'})])
    install_sdk(monkeypatch, response)
    result = GeminiProvider().complete([])
    assert result.tool_calls[0].name == 'clarify'
    assert result.tool_calls[0].args == {'question': 'URL?'}
