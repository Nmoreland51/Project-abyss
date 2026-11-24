import os

import pytest

from abyss.foundation import fetch as fetch_mod


@pytest.fixture(autouse=True)
def _fast_pacer_for_local_tests(request, monkeypatch):
    """Unit tests only talk to 127.0.0.1, so per-host politeness delays are unnecessary there.
    Live tests keep the real pacing."""
    if "live" not in request.keywords:
        monkeypatch.setattr(fetch_mod._PACER, "interval", 0.0)


def pytest_collection_modifyitems(config, items):
    if os.environ.get("ABYSS_LIVE") == "1":
        return
    skip = pytest.mark.skip(reason="live network test: set ABYSS_LIVE=1 to run (a skip is NOT a pass)")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
