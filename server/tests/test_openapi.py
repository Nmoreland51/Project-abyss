"""The published contract (contracts/openapi.json) must match the code."""

import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "export_openapi.py"


def test_committed_openapi_matches_code():
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.OUT.read_text() == mod.render(), "run: python server/scripts/export_openapi.py"
