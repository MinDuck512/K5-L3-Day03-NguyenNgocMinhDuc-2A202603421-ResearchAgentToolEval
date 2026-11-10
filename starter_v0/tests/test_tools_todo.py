"""Completed lab challenge and regression tests. All HTTP is mocked."""
import importlib
import pytest
import requests
from conftest import FakeResponse
from tools import TOOL_FUNCTIONS as T


def test_clarify_choice_returns_options_and_awaits_user():
    result = T['clarify']('Nguon nao?', 'choice', ['Web', 'Twitter'])
    assert result['options'] == ['Web', 'Twitter']
    assert result['awaiting_user'] is True


@pytest.mark.parametrize('kwargs', [{'question': ''}, {'question': 'x', 'response_type': 'bad'}, {'question': 'x', 'response_type': 'choice', 'options': ['one']}])
def test_clarify_bad_input_returns_error(kwargs):
    assert T['clarify'](**kwargs)['error'] == 'ValueError'


def test_format_sections_groups_items_by_section():
    result = T['format']([{'title': s, 'section': s} for s in ['A', 'B', 'A']])
    assert result['markdown'].count('## A') == result['markdown'].count('## B') == 1


def test_format_thread_numbers_items():
    result = T['format']([{'title': 'First'}, {'title': 'Second'}], 'thread')
    assert result['markdown'].startswith('1/ First')
    assert '\n\n2/ Second' in result['markdown']


@pytest.mark.parametrize('items', [None, []])
def test_format_empty_items_does_not_crash(items):
    assert T['format'](items)['item_count'] == 0


@pytest.mark.parametrize('kwargs', [{'items': ['bad']}, {'items': {}, 'template': 'bullets'}, {'items': [], 'template': 'bad'}, {'items': [{'title': 1}]}])
def test_format_invalid_items_returns_error(kwargs):
    assert T['format'](**kwargs)['error'] == 'ValueError'


def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake-token')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'fake-chat')
    calls = fake_http(FakeResponse({'ok': True}))
    assert T['send']('literal *text*', True)['status'] == 'sent'
    assert len(calls) == 1
    assert calls[0]['method'] == 'POST'
    assert calls[0]['url'] == 'https://api.telegram.org/botfake-token/sendMessage'
    assert calls[0]['json'] == {'chat_id': 'fake-chat', 'text': 'literal *text*'}


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http):
    calls = fake_http(FakeResponse())
    assert T['send']('hello', True)['error'] == 'RuntimeError'
    assert calls == []


@pytest.mark.parametrize('confirmed', ['false', 'true', 1, None, False])
def test_send_non_boolean_confirmation_never_posts(confirmed, fake_http):
    calls = fake_http(FakeResponse())
    assert T['send']('hello', confirmed)['status'] == 'needs_confirmation'
    assert calls == []


def test_send_false_telegram_ack_is_error(monkeypatch, fake_http):
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake')
    monkeypatch.setenv('TELEGRAM_CHAT_ID', 'fake')
    fake_http(FakeResponse({'ok': False}))
    assert T['send']('hello', True)['error'] == 'RuntimeError'


def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http):
    monkeypatch.setenv('TAVILY_API_KEY', 'fake')
    calls = fake_http(FakeResponse({'results': []}))
    assert T['lookup']('AI', timeframe=None, max_results='3')['items'] == []
    assert 'time_range' not in calls[0]['json']
    assert calls[0]['json']['max_results'] == 3


def test_fetch_maps_firecrawl_response(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    calls = fake_http(FakeResponse({'data': {'markdown': 'body', 'metadata': {'title': 'T', 'sourceURL': 'https://example.com/a'}}}))
    result = T['fetch']('https://example.com/a')
    assert calls[0]['json'] == {'url': 'https://example.com/a', 'formats': ['markdown']}
    assert result['items'][0] == {'title': 'T', 'url': 'https://example.com/a', 'source': 'example.com', 'summary': 'body'}


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    fake_http(FakeResponse({'data': {'markdown': 'x' * 5000}}))
    assert len(T['fetch']('https://example.com')['items'][0]['summary']) == 4000


def test_fetch_upstream_unsuccessful_is_error(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    fake_http(FakeResponse({'success': False}))
    assert T['fetch']('https://example.com')['error'] == 'RuntimeError'


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http):
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake')
    calls = fake_http(FakeResponse({'timeline': [{'text': 'no id'}] + [{'tweet_id': str(i), 'screen_name': 'sama', 'text': f'post {i}'} for i in range(1, 7)]}))
    result = T['timeline']('@sama', '3')
    assert calls[0]['params'] == {'screenname': 'sama'}
    assert [i['url'] for i in result['items']] == [f'https://x.com/sama/status/{i}' for i in range(1, 4)]


@pytest.mark.parametrize('search_type', ['Latest', 'Top'])
def test_social_search_passes_search_type(search_type, monkeypatch, fake_http):
    monkeypatch.setenv('RAPIDAPI_KEY', 'fake')
    calls = fake_http(FakeResponse({'tweets': [{'id': '42', 'author': {'screen_name': 'a'}, 'text': 'text'}]}))
    result = T['social_search']('AI', search_type, 1)
    assert calls[0]['params'] == {'query': 'AI', 'search_type': search_type}
    assert result['items'][0]['url'] == 'https://x.com/a/status/42'


def test_policy_empty_query_returns_no_results():
    assert T['policy']('')['results'] == []


def test_policy_area_filter_only_returns_that_area():
    result = T['policy']('API key prompt', 'data_privacy')
    assert result['results']
    assert {r['policy_area'] for r in result['results']} == {'data_privacy'}


def test_policy_instruction_like_lines_go_to_untrusted_text():
    result = T['policy']('citation source', 'source_citation', 20)
    suspicious = [r for r in result['results'] if r['untrusted_text']]
    assert suspicious
    for record in suspicious:
        for line in record['untrusted_text']:
            assert line not in record['facts']


@pytest.mark.parametrize('name,args', [
    ('lookup', {'query': 'AI', 'max_results': 0}),
    ('lookup', {'query': 'AI', 'topic': 'bad'}),
    ('lookup', {'query': 'AI', 'timeframe': 'bad'}),
    ('timeline', {'screenname': 'sama', 'limit': 0}),
    ('timeline', {'screenname': 'Sam Altman'}),
    ('social_search', {'query': 'AI', 'limit': -1}),
    ('social_search', {'query': 'AI', 'search_type': 'top'}),
    ('fetch', {'url': 'file:///secret'}),
    ('policy', {'query': 'citation', 'top_k': 0}),
    ('policy', {'query': 'citation', 'policy_area': 'bad'}),
    ('papers', {'query': 'AI', 'max_results': 0}),
    ('papers', {'query': 'AI', 'sort_by': 'bad'}),
    ('paper_text', {'arxiv_url': 'https://evil.test/1706.03762'}),
    ('paper_text', {'arxiv_url': '1706.03762', 'max_pages': 0}),
])
def test_invalid_model_input_returns_error_before_network(name, args, fake_http):
    calls = fake_http(FakeResponse())
    assert T[name](**args)['error'] == 'ValueError'
    assert calls == []


def test_source_audit_deduplicates_tracking_links_and_reports_missing_url():
    result = T['source_audit']([
        {'title': 'A', 'url': 'https://WWW.example.com/a?utm_source=x&id=1#part'},
        {'title': 'B', 'url': 'https://example.com/a?id=1'},
        {'title': 'C'}, {'url': 'javascript:alert(1)'}, {'url': 'https://other.test/b'},
    ])
    assert result['unique_count'] == result['domain_count'] == 2
    assert result['items'][0]['url'] == 'https://example.com/a?id=1'
    assert result['issues'] == [
        {'index': 1, 'issue': 'duplicate_url', 'duplicate_of': 0},
        {'index': 2, 'issue': 'missing_or_invalid_url'},
        {'index': 3, 'issue': 'missing_or_invalid_url'},
    ]


@pytest.mark.parametrize('items', [None, {}, ['x'], [None], [{}] * 501])
def test_source_audit_bad_input_from_model(items):
    assert T['source_audit'](items)['error'] == 'ValueError'


def test_source_audit_failure_returns_error_dict(monkeypatch):
    module = importlib.import_module('tools.source_audit.tool')
    def fail(value):
        raise RuntimeError('parser unavailable')
    monkeypatch.setattr(module, 'http_url', fail)
    result = T['source_audit']([{'url': 'https://example.com'}])
    assert result['error'] == 'RuntimeError'
    assert result['message'] == 'parser unavailable'


def test_source_audit_does_not_merge_distinct_ports_or_paths():
    urls = ['https://x.test/a', 'https://x.test:444/a', 'https://x.test/A']
    assert T['source_audit']([{'url': u} for u in urls])['unique_count'] == 3


def test_paper_text_happy_path_and_character_limit(monkeypatch, tmp_path):
    module = importlib.import_module('tools.paper_text.tool')
    output = tmp_path / '1706.03762.pdf'
    monkeypatch.setattr(module, '_download_arxiv_pdf', lambda u: ('1706.03762', output, 'https://arxiv.org/pdf/1706.03762.pdf'))
    calls = []
    def extract(path, max_pages):
        calls.append(max_pages)
        return 'a' * 2000, 10
    monkeypatch.setattr(module, '_extract_pdf_text', extract)
    result = T['paper_text']('1706.03762', max_pages='2', max_chars='500')
    assert result['pages_read'] == 2
    assert result['chars_returned'] == 500
    assert calls == [2]
    assert output.with_suffix('.txt').read_text() == 'a' * 500


def test_papers_maps_atom_response(monkeypatch, fake_http):
    module = importlib.import_module('tools.papers.tool')
    monkeypatch.setattr(module, '_rate_limit_arxiv', lambda: None)
    xml = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/1706.03762</id><title>Attention</title><summary>Body</summary><author><name>A</name></author></entry></feed>'
    calls = fake_http(FakeResponse(text=xml))
    result = T['papers']('attention', 2)
    assert calls[0]['params']['max_results'] == 2
    assert result['items'][0]['arxiv_id'] == '1706.03762'
    assert result['items'][0]['authors'] == ['A']


def test_fetch_timeout_returns_error(monkeypatch, fake_http):
    monkeypatch.setenv('FIRECRAWL_API_KEY', 'fake')
    fake_http(requests.Timeout('timeout'))
    assert T['fetch']('https://example.com')['error'] == 'Timeout'


def test_tool_errors_redact_api_tokens(monkeypatch):
    from tools._shared import err
    monkeypatch.setenv('TELEGRAM_BOT_TOKEN', 'fake-secret-token')
    result = err('send', RuntimeError('https://api.telegram.org/botfake-secret-token/sendMessage'))
    assert 'fake-secret-token' not in result['message']
    assert '[REDACTED]' in result['message']


def test_source_audit_bad_port_is_an_issue_and_other_sources_survive():
    result = T['source_audit']([{'url': 'https://x.test:bad/a'}, {'url': 'https://x.test/a'}])
    assert result['unique_count'] == 1
    assert result['issues'][0]['issue'] == 'missing_or_invalid_url'
