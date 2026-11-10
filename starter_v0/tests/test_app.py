"""UI smoke test, no provider or HTTP call required."""
from pathlib import Path


def test_ui_loads_and_audits_sources_without_network():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=15).run()
    assert not app.exception
    assert len(app.tabs) == 3
    app.button[0].click().run()
    assert not app.exception
    assert [(item.label, item.value) for item in app.metric] == [
        ('Nguồn duy nhất', '1'), ('Tên miền', '1'), ('Vấn đề', '2')]
