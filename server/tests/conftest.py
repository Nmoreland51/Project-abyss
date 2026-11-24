"""Test harness: a fresh PostgreSQL database per test session, schema created by running the real
Alembic migrations as the owner role, and the API connected as the least-privilege runtime role.

Requires a reachable PostgreSQL server. Set TEST_ADMIN_DATABASE_URL (superuser), e.g.
    postgresql+psycopg://postgres:postgres@localhost:5433/postgres
No mocks of the database: every test exercises real SQL, constraints and transactions."""

import os
import pathlib
import uuid
from urllib.parse import urlsplit, urlunsplit

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parent
ADMIN_URL = os.environ.get("TEST_ADMIN_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/postgres")
MIGRATOR_PW = "test_migrator_pw"
RUNTIME_PW = "test_runtime_pw"


def _with(url: str, user: str, password: str, db: str) -> str:
    parts = urlsplit(url)
    host = parts.hostname or "localhost"
    port = f":{parts.port}" if parts.port else ""
    return urlunsplit((parts.scheme, f"{user}:{password}@{host}{port}", f"/{db}", "", ""))


@pytest.fixture(scope="session")
def database():
    db_name = f"th_test_{uuid.uuid4().hex[:10]}"
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        for role, pw in (("app_migrator", MIGRATOR_PW), ("app_runtime", RUNTIME_PW)):
            exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": role}).scalar()
            if exists:
                conn.execute(text(f"ALTER ROLE {role} LOGIN PASSWORD '{pw}'"))
            else:
                conn.execute(text(f"CREATE ROLE {role} LOGIN PASSWORD '{pw}'"))
        conn.execute(text(f'CREATE DATABASE "{db_name}" OWNER app_migrator'))
    db_admin = create_engine(_with(ADMIN_URL, *_admin_creds(), db_name), isolation_level="AUTOCOMMIT")
    with db_admin.connect() as conn:
        conn.execute(text((REPO / "infra/postgres/database.sql").read_text()))
    db_admin.dispose()

    migrator_url = _with(ADMIN_URL, "app_migrator", MIGRATOR_PW, db_name)
    runtime_url = _with(ADMIN_URL, "app_runtime", RUNTIME_PW, db_name)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["url"] = migrator_url
    command.upgrade(cfg, "head")
    yield {"name": db_name, "migrator_url": migrator_url, "runtime_url": runtime_url, "alembic": cfg}
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    admin.dispose()


def _admin_creds() -> tuple[str, str]:
    parts = urlsplit(ADMIN_URL)
    return parts.username or "postgres", parts.password or ""


@pytest.fixture(scope="session")
def app(database):
    os.environ["DATABASE_URL"] = database["runtime_url"]
    os.environ["AUTH_RATE_LIMIT_PER_MINUTE"] = "1000"
    os.environ["WRITE_RATE_LIMIT_PER_MINUTE"] = "1000"
    os.environ["COMMUNITY_CREATE_PER_HOUR"] = "1000"
    from app.config import get_settings

    get_settings.cache_clear()
    from app.db import init_engine
    from app.main import create_app

    init_engine(database["runtime_url"])
    return create_app()


@pytest.fixture
def migrator_engine(database):
    engine = create_engine(database["migrator_url"])
    yield engine
    engine.dispose()


def _truncate_all(database) -> None:
    engine = create_engine(database["migrator_url"])
    with engine.begin() as conn:
        tables = (
            conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version'")
            )
            .scalars()
            .all()
        )
        if tables:
            conn.execute(text("TRUNCATE " + ", ".join(tables) + " CASCADE"))
    engine.dispose()


@pytest.fixture
def client(app, database):
    from fastapi.testclient import TestClient

    from app.ratelimit import limiter

    with TestClient(app) as c:
        yield c
    _truncate_all(database)
    limiter.reset()


class Api:
    """Thin helper around a TestClient holding one account's tokens (one 'device')."""

    def __init__(self, client, handle: str, password: str = "correct-horse-battery"):
        self.client = client
        self.handle = handle
        self.password = password
        self.tokens: dict | None = None
        self.user: dict | None = None

    def register(self):
        r = self.client.post("/v1/auth/register", json={"handle": self.handle, "password": self.password})
        assert r.status_code == 201, r.text
        self.user, self.tokens = r.json()["user"], r.json()["tokens"]
        return self

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.tokens['access_token']}"} if self.tokens else {}

    def get(self, path, **kw):
        return self.client.get(path, headers={**self.headers, **kw.pop("headers", {})}, **kw)

    def post(self, path, **kw):
        return self.client.post(path, headers={**self.headers, **kw.pop("headers", {})}, **kw)

    def put(self, path, **kw):
        return self.client.put(path, headers={**self.headers, **kw.pop("headers", {})}, **kw)

    def patch(self, path, **kw):
        return self.client.patch(path, headers={**self.headers, **kw.pop("headers", {})}, **kw)

    def delete(self, path, **kw):
        return self.client.delete(path, headers={**self.headers, **kw.pop("headers", {})}, **kw)

    def community(self, slug: str, **extra):
        r = self.post("/v1/communities", json={"slug": slug, "display_name": slug.title(), **extra})
        assert r.status_code == 201, r.text
        return r.json()

    def text_post(self, community: str, title: str, body: str = "body", **extra):
        r = self.post("/v1/posts", json={"community": community, "title": title, "body": body, **extra})
        assert r.status_code == 201, r.text
        return r.json()

    def comment(self, post_id: str, body: str, parent_id: str | None = None):
        payload = {"body": body} | ({"parent_id": parent_id} if parent_id else {})
        r = self.post(f"/v1/posts/{post_id}/comments", json=payload)
        assert r.status_code == 201, r.text
        return r.json()

    def vote_post(self, post_id: str, value: int):
        r = self.put(f"/v1/posts/{post_id}/vote", json={"value": value})
        assert r.status_code == 200, r.text
        return r.json()


@pytest.fixture
def make_user(client):
    def _make(handle: str) -> Api:
        return Api(client, handle).register()

    return _make


@pytest.fixture
def live_server(app, database):
    """The same app served by a real uvicorn server on a random local port (actual HTTP, real
    threadpool concurrency). Used by concurrency tests where TestClient would serialise calls."""
    import socket
    import threading
    import time

    import uvicorn

    from app.ratelimit import limiter

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started:
        if time.time() > deadline:
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)
    _truncate_all(database)
    limiter.reset()
