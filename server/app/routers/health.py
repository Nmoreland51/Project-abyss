from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .. import API_VERSION
from ..db import get_engine

router = APIRouter(tags=["health"])

# Must equal the Alembic head revision (asserted by tests/test_health.py).
EXPECTED_SCHEMA_REVISION = "0001"


@router.get("/health/live")
def live() -> dict:
    return {"status": "ok", "api_version": API_VERSION}


@router.get("/health/ready")
def ready() -> JSONResponse:
    checks: dict[str, str] = {}
    ok = True
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
            revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            if revision == EXPECTED_SCHEMA_REVISION:
                checks["schema"] = "ok"
            else:
                checks["schema"] = f"mismatch: have {revision}, need {EXPECTED_SCHEMA_REVISION}"
                ok = False
    except Exception as exc:  # readiness must report, not raise
        checks.setdefault("database", f"error: {type(exc).__name__}")
        ok = False
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ok" if ok else "unavailable", "checks": checks, "api_version": API_VERSION},
    )
