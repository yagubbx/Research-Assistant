"""Streamlit's actual app runner, with real offline pipeline integration."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_ui_offline_research_and_references(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_CACHE_DIR", str(tmp_path))
    app = AppTest.from_file(str(Path(__file__).parents[1] / "researcher/web_ui.py"), default_timeout=20).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "3"
    assert len(app.expander) == 3
    assert "synthetic" in app.info[0].value


def test_ui_live_missing_credentials_is_readable(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("LLM_API_KEY", "")
    app = AppTest.from_file(str(Path(__file__).parents[1] / "researcher/web_ui.py"), default_timeout=20).run()
    app.radio[0].set_value("Live research").run()
    app.text_area[0].set_value("What is photosynthesis?")
    app.button[0].click().run()
    assert not app.exception
    assert app.error


def test_ui_disables_empty_source_selection():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "researcher/web_ui.py"), default_timeout=20).run()
    app.multiselect[0].set_value([]).run()
    assert app.button[0].disabled
