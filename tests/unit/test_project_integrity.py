"""Project-level integrity: owner requirements preserved, docs in sync, benchmarks pre-registered (T16 support)."""

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest

from abyss.core.contracts import ImplementationStatus
from abyss.foundation import citations, probe, render
from abyss.foundation.benchmarks import BenchmarkFile, load_benchmarks
from abyss.foundation.registry import REPO_ROOT, load_registry
from abyss.foundation.taxonomy import load_taxonomy

DOCS = REPO_ROOT / "docs"
STARTER = DOCS / "starter_pack"


def test_starter_pack_is_preserved_unmodified():
    """The owner's original design package is the baseline; it must not be edited in place."""
    lines = (STARTER / "SHA256SUMS").read_text().split("\n")
    entries = [l.split(None, 1) for l in lines if l.strip()]
    assert len(entries) >= 7
    for digest, name in entries:
        assert hashlib.sha256((STARTER / name.strip()).read_bytes()).hexdigest() == digest, name


def test_owner_directive_preserved():
    assert (STARTER / "OWNER_DIRECTIVE_2026-11-24.md").exists()


def _trace_rows():
    with render.TRACE_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_no_original_requirement_silently_dropped():
    with (STARTER / "REQUIREMENTS_TRACEABILITY.csv").open(newline="", encoding="utf-8") as fh:
        original = {r["requirement_id"]: r["requirement"] for r in csv.DictReader(fh)}
    current = {r["requirement_id"]: r["requirement"] for r in _trace_rows()}
    for rid, text in original.items():
        assert rid in current, f"{rid} dropped"
        assert current[rid] == text, f"{rid} wording changed; record changes in DECISION_LOG and keep the original text"


def test_traceability_statuses_and_evidence():
    valid = {s.value for s in ImplementationStatus}
    for r in _trace_rows():
        assert r["status"] in valid, r["requirement_id"]
        if r["status"] == "verified":
            paths = [p.strip() for p in r["evidence"].split(";") if p.strip()]
            assert paths, f"{r['requirement_id']} verified without evidence"
            for p in paths:
                assert (REPO_ROOT / p).exists(), f"{r['requirement_id']}: evidence path {p} missing"


def test_every_referenced_test_id_is_defined_in_testing_strategy():
    defined = set(re.findall(r"^\| (T\d{2}) \|", (DOCS / "TESTING_STRATEGY.md").read_text(encoding="utf-8"), re.M))
    for r in _trace_rows():
        for tid in re.findall(r"T\d{2}", r["test_ids"]):
            if "-" in r["test_ids"]:  # ranges like T01-T22 are allowed for release validation
                continue
            assert tid in defined, f"{r['requirement_id']} references undefined {tid}"


def test_benchmarks_pre_registered():
    bf: BenchmarkFile = load_benchmarks()
    assert bf.benchmarks and all(b.status == "defined_not_run" for b in bf.benchmarks), "Phase 0 has run no benchmark"
    results = (DOCS / "BENCHMARK_RESULTS.md").read_text(encoding="utf-8")
    for b in bf.benchmarks:
        assert b.id in results, f"{b.id} missing from BENCHMARK_RESULTS.md"


@pytest.mark.parametrize("name", ["NETWORK_TAXONOMY.md", "DATA_SOURCE_REGISTRY.md", "REQUIREMENTS_TRACEABILITY.md"])
def test_generated_docs_are_in_sync(name):
    loaded, registry = load_taxonomy(), load_registry()
    crep = citations.load_report()
    prep = json.loads(probe.PROBE_REPORT_PATH.read_text()) if probe.PROBE_REPORT_PATH.exists() else None
    expected = {
        "NETWORK_TAXONOMY.md": lambda: render.render_taxonomy(loaded, registry, crep),
        "DATA_SOURCE_REGISTRY.md": lambda: render.render_registry(registry, crep, prep),
        "REQUIREMENTS_TRACEABILITY.md": lambda: render.render_traceability(render.load_traceability()),
    }[name]()
    assert (DOCS / name).read_text(encoding="utf-8") == expected, f"{name} is stale: run `python -m abyss render-docs`"


def test_committed_citation_report_matches_current_taxonomy():
    rep = citations.load_report()
    assert rep is not None, "no citation report committed"
    assert rep["inputs"]["taxonomy"]["sha256"] == load_taxonomy().sha256, "taxonomy changed since last live check"
    assert not any(c["outcome"] == "QUOTE_NOT_FOUND" for c in rep["citations"]), "a committed citation is unsupported"


@pytest.mark.parametrize("doc", [
    "MASTER_ARCHITECTURE.md", "NETWORK_TAXONOMY.md", "RESEARCH_METHODOLOGY.md", "SIGNATURE_SPECIFICATION.md",
    "DISCOVERY_ENGINE_SPECIFICATION.md", "DATA_SOURCE_REGISTRY.md", "DEVELOPMENT_ROADMAP.md", "REQUIREMENTS_TRACEABILITY.md",
    "TESTING_STRATEGY.md", "BENCHMARK_RESULTS.md", "KNOWN_LIMITATIONS.md", "IMPLEMENTATION_STATUS.md",
    "SECURITY_AUDIT.md", "FINAL_SYSTEM_AUDIT.md", "GAP_AUDIT.md", "DECISION_LOG.md", "SCOPE_AND_RESTRICTIONS.md",
])
def test_required_deliverable_documents_exist(doc):
    assert (DOCS / doc).stat().st_size > 200, doc
