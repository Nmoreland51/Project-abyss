"""Opaque keyset cursors. Cursors are untrusted client input: decoded strictly and validated."""

import base64
import json
import uuid
from datetime import datetime

from .errors import invalid


def encode(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode(cursor: str | None, expected_kind: str) -> dict | None:
    if not cursor:
        return None
    try:
        if len(cursor) > 512:
            raise ValueError("too long")
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if not isinstance(data, dict) or data.get("k") != expected_kind:
            raise ValueError("wrong kind")
        uuid.UUID(str(data["id"]))
        if "at" in data:
            datetime.fromisoformat(data["at"])
        return data
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise invalid("Invalid or expired cursor", "cursor") from exc
