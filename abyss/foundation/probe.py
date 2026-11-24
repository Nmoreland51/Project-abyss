"""Reachability probe for candidate ingestion sources (environment audit, feeds Phase 1 planning).

A probe answers exactly one question: can this environment reach this endpoint right now?
It doesn't verify licence terms, data quality or fitness for purpose. Bodies are capped at
64 KiB, so large datasets (e.g. package indexes) are sampled rather than downloaded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..core.contracts import SourceKind
from ..core.scope import ScopePolicy
from .citations import environment_info
from .fetch import http_fetch
from .registry import REPO_ROOT, Registry

PROBE_REPORT_PATH = REPO_ROOT / "evidence" / "phase0" / "source_probe_report.json"
PROBE_MAX_BYTES = 64 * 1024


def probe_sources(registry: Registry, policy: ScopePolicy) -> dict:
    started = datetime.now(timezone.utc)
    rows = []
    for sid, src in sorted(registry.sources.items()):
        if src.kind is SourceKind.REFERENCE_DOCUMENT:
            continue
        decision = policy.evaluate(src)
        if not decision.allowed:
            rows.append({"source_id": sid, "scope": "rejected", "scope_reason": decision.reason, "retrieval": None})
            continue
        uri = src.probe_uri or src.uri
        result = http_fetch(sid, uri, max_bytes=PROBE_MAX_BYTES, allow_truncation=True, timeout=30.0)
        rows.append({"source_id": sid, "scope": "in_scope", "scope_reason": decision.reason,
                     "retrieval": json.loads(result.record.model_dump_json())})
    counts: dict[str, int] = {}
    for r in rows:
        key = r["retrieval"]["outcome"] if r["retrieval"] else "scope_rejected"
        counts[key] = counts.get(key, 0) + 1
    return {
        "report_type": "source_reachability_probe",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "environment": environment_info(),
        "summary": {"probed": len(rows), "by_outcome": dict(sorted(counts.items()))},
        "results": rows,
        "notes": [
            "Reachability from this environment only; the owner's machine may differ (different egress policy).",
            "'ok' means an HTTP 2xx response was received; it doesn't mean the source's terms were reviewed.",
        ],
    }


def write_probe_report(report: dict, path: Path = PROBE_REPORT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
