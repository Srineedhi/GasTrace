from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_starts_and_streams_without_exceptions():
    at = AppTest.from_file(APP, default_timeout=180).run()
    assert not at.exception
    for t in at.toggle:
        if t.key == "live_run":
            t.set_value(True)
    at.run()
    assert not at.exception
