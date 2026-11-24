import json
import logging
import sys
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import API_VERSION
from .config import get_settings
from .errors import install_error_handlers
from .routers import auth, comments, communities, health, posts, users, votes

MAX_BODY_BYTES = 256 * 1024


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


access_log = logging.getLogger("app.access")


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_logging(settings.log_level)
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=API_VERSION,
        description=(
            "Independent live discussion platform API (v1). Not affiliated with Reddit. "
            "All routes enforce visibility and authorization server-side. Errors use a "
            "consistent envelope: {error: {code, message, request_id}}."
        ),
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id", "")
        if not (0 < len(rid) <= 64 and rid.replace("-", "").isalnum()):
            rid = uuid.uuid4().hex
        request.state.request_id = rid
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {"code": "payload_too_large", "message": "Request body too large", "request_id": rid}
                },
                headers={"X-Request-ID": rid},
            )
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
        # Path only (no query string, no headers): avoids logging tokens or search terms.
        access_log.info(
            "request",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
        return response

    install_error_handlers(app)
    for module in (health, auth, communities, posts, comments, votes, users):
        app.include_router(module.router)
    return app


app = create_app()
