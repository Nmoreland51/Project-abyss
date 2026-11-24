# Threadhall (working name) — live discussion platform + Android app

An independent, self-hosted, classic-style community app: accounts, communities, posts, threaded
replies, votes and karma on **your own server**, with a native Android client. Not affiliated with
Reddit; no dependency on any other service for core operation. Planning name in the specification:
"RetroReddit V2" (see `docs/spec/`). Public name is pending owner decision OD-01.

**Status:** Phase 0 complete; Phase 1 vertical slice implemented and verified against a real server
(JVM clients and the real app UI on Robolectric). **Not yet verified on physical Android devices.**
Details, evidence and limitations: [`docs/STATUS.md`](docs/STATUS.md).

## Quick start
```bash
cp infra/.env.example infra/.env      # set three passwords
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
curl http://localhost:8000/health/ready
```
Then install the pilot APK on a phone on the same Wi-Fi and enter `http://<server-LAN-IP>:8000`.
Full runbook: [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

## Layout
| Path | Contents |
|---|---|
| `server/` | FastAPI app (`app/`), Alembic migrations, pytest suite (real PostgreSQL), Dockerfile |
| `android/core` | Kotlin/JVM API client and models (tested against a live server) |
| `android/app` | Jetpack Compose app |
| `contracts/` | `openapi.json` (generated, checked by tests), `source_registry.json` (content rights) |
| `infra/` | Docker Compose stack, PostgreSQL role bootstrap |
| `tests/e2e/` | Two-account end-to-end script against any running server (stdlib Python) |
| `docs/` | Spec pack (`spec/`), ADRs, threat model, owner decisions, operations, status, evidence |

## Tests
```bash
# backend (needs a PostgreSQL superuser URL; tests create and drop their own database)
docker run -d --name th-testdb -e POSTGRES_PASSWORD=postgres -p 127.0.0.1:5433:5432 postgres:18.7-alpine
cd server && python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
# android (live tests run when LIVE_BASE_URL points at a running server)
cd android && LIVE_BASE_URL=http://localhost:8000 ./gradlew :core:test :app:testDebugUnitTest :app:assembleDebug
```
