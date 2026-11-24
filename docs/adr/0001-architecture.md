# ADR-0001 Architecture: modular monolith, PostgreSQL, native Android client

Status: accepted (Phase 0) · Date: 2026-11-24

## Context
MASTER_AUDIT §5 asks for a modern modular monolith (FastAPI + PostgreSQL + Kotlin/Compose), no
microservices, no dependency on any archive or third-party service for core operation.

## Decision
- **Server:** one FastAPI process (`server/app`), routers per domain (auth, communities, posts,
  comments, votes, users, health). SQLAlchemy 2.1 + psycopg 3, synchronous endpoints in the
  threadpool. Schema owned by Alembic migrations (`server/migrations`), hand-written SQL so
  constraints are explicit.
- **Database:** PostgreSQL 18.7 (19.0 was released days before this decision; 18 chosen for maturity).
  Two roles: `app_migrator` (owns schema, runs migrations) and `app_runtime` (DML only). Tests use
  the same split and assert the runtime role cannot run DDL.
- **Client:** `android/core` is a pure Kotlin/JVM library (models + OkHttp client), so the code the
  app ships is tested against a real server from the JVM. `android/app` is the Compose UI.
- **No Redis, no queue, no search engine, no object storage** in Phase 1. Each is added only when a
  phase needs it and a measurement justifies it.
- **Dev/pilot deployment:** Docker Compose (`infra/docker-compose.yml`): `db`, one-shot `migrate`, `api`.

## Versions (latest stable checked on 2026-11-24)
| Component | Version | Component | Version |
|---|---|---|---|
| Python | 3.13.18 | FastAPI | 0.165.0 |
| SQLAlchemy | 2.1.9 | Alembic | 1.20.1 |
| psycopg | 3.3.9 | argon2-cffi | 25.1.0 |
| pydantic | 2.14.4 | uvicorn | 0.54.0 |
| PostgreSQL | 18.7 | Gradle | 9.9.2 |
| AGP | 9.5.2 (built-in Kotlin) | Kotlin | 2.4.21 |
| Compose BOM | 2026.11.01 | OkHttp | 5.5.1 |
| kotlinx.serialization | 1.13.0 | Navigation Compose | 2.10.2 |
| compileSdk | 37.2 (required by Compose 1.13) | targetSdk / minSdk | 36 / 26 |

## Deviations from SYSTEM_ARCHITECTURE.md (recorded, not silent)
1. `android/feature/*` modules are not split out yet; screens live in `android/app/ui/<feature>`.
   Splitting adds build complexity with no benefit at this size; revisit when build times or
   ownership boundaries justify it.
2. `profiles` is folded into `users` (`display_name`, `bio`). One-to-one table adds joins for no gain.
   A later migration can split it without API changes.
3. Community routes use the slug (`/v1/communities/{slug}/membership`) rather than the UUID, because
   slugs are the stable, human-facing permalink. Posts/comments/users-by-id still use UUIDs.
4. `worker/` does not exist yet: Phase 1 has no background jobs. It arrives with Phase 3 imports.

## Consequences
Single deployable, one database, transactions for votes/memberships. Horizontal scale is a later
concern; the in-process rate limiter is explicitly single-process (see THREAT_MODEL.md).
