"""T01 (in-process part): migrations apply cleanly, readiness reports schema state."""

from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.routers.health import EXPECTED_SCHEMA_REVISION


def test_expected_revision_is_alembic_head(database):
    head = ScriptDirectory.from_config(database["alembic"]).get_current_head()
    assert head == EXPECTED_SCHEMA_REVISION


def test_live_and_ready(client):
    assert client.get("/health/live").json()["status"] == "ok"
    r = client.get("/health/ready")
    assert r.status_code == 200, r.text
    assert r.json()["checks"] == {"database": "ok", "schema": "ok"}
    assert r.headers["x-request-id"]


def test_runtime_role_cannot_run_ddl(database):
    from sqlalchemy import create_engine
    from sqlalchemy.exc import ProgrammingError

    engine = create_engine(database["runtime_url"])
    try:
        with engine.begin() as conn:
            try:
                conn.execute(text("CREATE TABLE should_fail (id int)"))
                raise AssertionError("runtime role was able to create a table")
            except ProgrammingError as exc:
                assert "permission denied" in str(exc)
        with engine.begin() as conn:
            try:
                conn.execute(text("DROP TABLE users"))
                raise AssertionError("runtime role was able to drop a table")
            except ProgrammingError as exc:
                assert "must be owner" in str(exc) or "permission denied" in str(exc)
    finally:
        engine.dispose()


def test_downgrade_and_reupgrade_roundtrip(database):
    """Migration rollback path works on an empty schema (T22 precursor)."""
    command.downgrade(database["alembic"], "base")
    command.upgrade(database["alembic"], "head")


def test_error_envelope_shape(client):
    r = client.get("/v1/posts/not-a-uuid")
    assert r.status_code == 422
    body = r.json()["error"]
    assert body["code"] == "validation_error" and body["request_id"] and body["details"]
    r = client.get("/v1/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
