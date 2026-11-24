"""Write the OpenAPI contract to contracts/openapi.json (checked by tests/test_openapi.py)."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "openapi.json"


def render() -> str:
    return json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    OUT.write_text(render())
    print(f"wrote {OUT}")
