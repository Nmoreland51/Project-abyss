"""Idempotency keys for non-naturally-idempotent writes (post/comment creation).

The key row is inserted inside the same transaction as the write. A concurrent duplicate blocks
on the primary key until the first transaction commits (then replays the stored response) or
rolls back (then proceeds as the owner). Replays with a different payload are rejected (409)."""

import hashlib
import json
import re
import uuid

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .errors import ApiError, invalid
from .models import IdempotencyKey

_KEY_RE = re.compile(r"^[A-Za-z0-9_.:\-]{8,128}$")


def _hash(endpoint: str, payload: dict) -> str:
    raw = json.dumps({"e": endpoint, "p": jsonable_encoder(payload)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def begin(db: Session, user_id: uuid.UUID, key: str | None, endpoint: str, payload: dict) -> JSONResponse | None:
    """Claim the key. Returns a replay response if this request was already completed."""
    if key is None:
        return None
    if not _KEY_RE.fullmatch(key):
        raise invalid("Idempotency-Key must be 8-128 characters of [A-Za-z0-9_.:-]", "Idempotency-Key")
    digest = _hash(endpoint, payload)
    claimed = db.execute(
        insert(IdempotencyKey)
        .values(user_id=user_id, key=key, endpoint=endpoint, request_hash=digest)
        .on_conflict_do_nothing()
        .returning(IdempotencyKey.key)
    ).scalar()
    if claimed is not None:
        return None
    row = db.scalar(select(IdempotencyKey).where(IdempotencyKey.user_id == user_id, IdempotencyKey.key == key))
    if row is None:  # pragma: no cover - row vanished (cleanup raced); treat as conflict
        raise ApiError(409, "idempotency_conflict", "Retry the request")
    if row.request_hash != digest or row.endpoint != endpoint:
        raise ApiError(409, "idempotency_key_reused", "Idempotency-Key was already used for a different request")
    if row.status_code is None:  # pragma: no cover - only visible if isolation level changes
        raise ApiError(409, "idempotency_in_progress", "The original request is still in progress")
    db.rollback()
    return JSONResponse(status_code=row.status_code, content=row.response, headers={"Idempotent-Replayed": "true"})


def finish(db: Session, user_id: uuid.UUID, key: str | None, status_code: int, body) -> None:
    if key is None:
        return
    db.execute(
        update(IdempotencyKey)
        .where(IdempotencyKey.user_id == user_id, IdempotencyKey.key == key)
        .values(status_code=status_code, response=jsonable_encoder(body))
    )
