"""Live citation verification (T08 / T21): is every quoted passage actually in its cited source?

For each registered reference document cited by the taxonomy, this module:
1. retrieves the document live (bounded, polite, through the environment's proxy),
2. records a RetrievalRecord (time, HTTP status, bytes, sha256, outcome),
3. extracts text and checks every quotation that cites the document.

Per-citation outcomes:
    VERIFIED              quote found in the retrieved text
    QUOTE_NOT_FOUND       document retrieved, quote absent  -> the claim is unsupported
    SOURCE_BLOCKED        egress or origin policy refused access -> BLOCKED, not passed
    SOURCE_RATE_LIMITED   HTTP 429 -> BLOCKED, not passed
    SOURCE_FAILED         network/server failure -> not passed
    SOURCE_UNEXTRACTABLE  retrieved, but no readable text (e.g. font-encoded PDF) -> not passed

Only VERIFIED counts as support. A run's verification rate is reported as-is; it isn't rounded up.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .. import __version__
from ..core.contracts import CONTRACT_VERSION, RetrievalOutcome
from .fetch import Fetcher, extract_text, find_quote, http_fetch, normalize
from .registry import REPO_ROOT, Registry
from .taxonomy import LoadedTaxonomy

CITATION_REPORT_PATH = REPO_ROOT / "evidence" / "phase0" / "citation_report.json"

_SOURCE_TO_CITATION = {
    RetrievalOutcome.BLOCKED: "SOURCE_BLOCKED",
    RetrievalOutcome.RATE_LIMITED: "SOURCE_RATE_LIMITED",
    RetrievalOutcome.FETCH_FAILED: "SOURCE_FAILED",
    RetrievalOutcome.TEXT_UNEXTRACTABLE: "SOURCE_UNEXTRACTABLE",
}


def git_commit(repo: Path = REPO_ROOT) -> Optional[str]:
    try:
        out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_dirty(repo: Path = REPO_ROOT) -> Optional[bool]:
    try:
        out = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, timeout=10)
        return bool(out.stdout.strip()) if out.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def environment_info() -> dict:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "abyss_version": __version__,
        "contract_version": CONTRACT_VERSION,
        "git_commit": git_commit(),
        "git_worktree_dirty": git_dirty(),
    }


def verify_citations(loaded: LoadedTaxonomy, registry: Registry, fetcher: Fetcher = http_fetch) -> dict:
    started = datetime.now(timezone.utc)
    by_ref: dict[str, list[tuple[str, str, object]]] = defaultdict(list)
    for entry_id, facet, c in loaded.taxonomy.iter_citations():
        by_ref[c.ref].append((entry_id, facet, c))

    sources = registry.sources
    retrievals: list[dict] = []
    citations: list[dict] = []
    for ref in sorted(by_ref):
        src = sources[ref]
        result = fetcher(ref, src.uri)
        record = result.record
        norm_text = ""
        if record.outcome is RetrievalOutcome.OK:
            text, method = extract_text(result.body, record.content_type)
            if method == "none" or not text.strip():
                record = record.model_copy(update={"outcome": RetrievalOutcome.TEXT_UNEXTRACTABLE,
                                                   "extraction_method": method, "error": "no readable text extracted"})
            else:
                norm_text = normalize(text)
                record = record.model_copy(update={"extraction_method": method, "text_chars": len(norm_text)})
        retrievals.append(json.loads(record.model_dump_json()))
        for entry_id, facet, c in by_ref[ref]:
            if record.outcome is RetrievalOutcome.OK:
                mode = find_quote(norm_text, c.quote)
                outcome = "VERIFIED" if mode else "QUOTE_NOT_FOUND"
            else:
                mode, outcome = None, _SOURCE_TO_CITATION[record.outcome]
            citations.append(
                {"entry": entry_id, "facet": facet, "ref": ref, "quote": c.quote, "outcome": outcome, "match_mode": mode}
            )

    finished = datetime.now(timezone.utc)
    counts: dict[str, int] = defaultdict(int)
    for c in citations:
        counts[c["outcome"]] += 1
    src_counts: dict[str, int] = defaultdict(int)
    for r in retrievals:
        src_counts[r["outcome"]] += 1
    total = len(citations)
    return {
        "report_type": "citation_verification",
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "environment": environment_info(),
        "inputs": {
            "taxonomy": {"path": str(loaded.path.relative_to(REPO_ROOT)) if loaded.path.is_relative_to(REPO_ROOT) else str(loaded.path),
                         "sha256": loaded.sha256, "version": loaded.taxonomy.taxonomy_version},
            "registry": [{"path": str(p.relative_to(REPO_ROOT)) if p.is_relative_to(REPO_ROOT) else str(p),
                          "sha256": h, "version": rf.registry_version} for p, h, rf in registry.files],
        },
        "summary": {
            "citations_total": total,
            "citations_by_outcome": dict(sorted(counts.items())),
            "citations_verified_fraction": round(counts["VERIFIED"] / total, 4) if total else None,
            "sources_total": len(retrievals),
            "sources_by_outcome": dict(sorted(src_counts.items())),
        },
        "retrievals": retrievals,
        "citations": citations,
        "notes": [
            "Retrieved content is hashed but not stored in Phase 0 (licence/retention not yet reviewed per source).",
            "Reachability reflects the environment the run executed in; see environment and DATA_SOURCE_REGISTRY.md.",
            "A VERIFIED citation means the quoted text was present at retrieval time; it doesn't independently prove the quoted claim is true.",
        ],
    }


def write_report(report: dict, path: Path = CITATION_REPORT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def load_report(path: Path = CITATION_REPORT_PATH) -> Optional[dict]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
