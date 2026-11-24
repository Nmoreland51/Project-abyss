"""Command line: `python -m abyss <command>`.

    validate          offline: schema + cross-reference validation of taxonomy, registry, benchmarks, scope
    verify-citations  LIVE: retrieve every cited source and check every quote; writes evidence/phase0/citation_report.json
    probe-sources     LIVE: reachability probe of candidate ingestion sources; writes evidence/phase0/source_probe_report.json
    render-docs       regenerate docs/NETWORK_TAXONOMY.md, docs/DATA_SOURCE_REGISTRY.md, docs/REQUIREMENTS_TRACEABILITY.md
"""

from __future__ import annotations

import argparse
import json
import sys

from .core.contracts import ImplementationStatus
from .core.scope import ScopePolicy
from .foundation import benchmarks, citations, probe, render
from .foundation.registry import REPO_ROOT, load_registry
from .foundation.taxonomy import cross_validate, load_taxonomy

SCOPE_PATH = REPO_ROOT / "config" / "scope.yaml"


def cmd_validate(_args) -> int:
    loaded = load_taxonomy()
    registry = load_registry()
    errors = cross_validate(loaded.taxonomy, registry)
    bf = benchmarks.load_benchmarks()
    policy = ScopePolicy.from_yaml(SCOPE_PATH)
    rows = render.load_traceability()
    valid_status = {s.value for s in ImplementationStatus}
    for r in rows:
        if r["status"] not in valid_status:
            errors.append(f"traceability {r['requirement_id']}: invalid status {r['status']!r}")
        if r["status"] == "verified" and not r["evidence"].strip():
            errors.append(f"traceability {r['requirement_id']}: 'verified' without an evidence path")
    n_cites = sum(1 for _ in loaded.taxonomy.iter_citations())
    print(f"taxonomy v{loaded.taxonomy.taxonomy_version}: {len(loaded.taxonomy.entries)} entries, {n_cites} citations")
    print(f"registry: {len(registry.sources)} sources in {len(registry.files)} files")
    print(f"benchmarks v{bf.definitions_version}: {len(bf.benchmarks)} pre-registered definitions")
    print(f"scope policy: {sorted(b.value for b in policy.allowed_access_bases)}")
    print(f"traceability: {len(rows)} requirements")
    if errors:
        print(f"\n{len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("OK: offline validation passed (this does NOT verify citations; run verify-citations)")
    return 0


def cmd_verify_citations(args) -> int:
    loaded = load_taxonomy()
    registry = load_registry()
    errors = cross_validate(loaded.taxonomy, registry)
    if errors:
        print("refusing to verify: cross-validation errors:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    report = citations.verify_citations(loaded, registry)
    path = citations.write_report(report, args.out) if args.out else citations.write_report(report)
    print(json.dumps(report["summary"], indent=2))
    print(f"report: {path}")
    not_verified = [c for c in report["citations"] if c["outcome"] != "VERIFIED"]
    for c in not_verified:
        print(f"  {c['outcome']:<22} {c['entry']}.{c['facet']} <- {c['ref']}: {c['quote'][:70]!r}")
    # Exit status: 0 only if every citation verified; 3 if any quote is missing (a content defect);
    # 4 if only source-availability problems remain (environment, reported as BLOCKED/FAILED).
    if any(c["outcome"] == "QUOTE_NOT_FOUND" for c in not_verified):
        return 3
    return 4 if not_verified else 0


def cmd_probe(args) -> int:
    registry = load_registry()
    policy = ScopePolicy.from_yaml(SCOPE_PATH)
    report = probe.probe_sources(registry, policy)
    path = probe.write_probe_report(report)
    print(json.dumps(report["summary"], indent=2))
    for row in report["results"]:
        r = row["retrieval"]
        print(f"  {row['source_id']:<28} " + (f"{r['outcome']:<13} HTTP {r['http_status']}" if r else f"SCOPE: {row['scope_reason']}"))
    print(f"report: {path}")
    return 0


def cmd_render(_args) -> int:
    loaded = load_taxonomy()
    registry = load_registry()
    crep = citations.load_report()
    prep = probe.PROBE_REPORT_PATH.exists() and json.loads(probe.PROBE_REPORT_PATH.read_text(encoding="utf-8")) or None
    targets = {
        render.DOCS / "NETWORK_TAXONOMY.md": render.render_taxonomy(loaded, registry, crep),
        render.DOCS / "DATA_SOURCE_REGISTRY.md": render.render_registry(registry, crep, prep),
        render.DOCS / "REQUIREMENTS_TRACEABILITY.md": render.render_traceability(render.load_traceability()),
    }
    for path, text in targets.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="abyss", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    v = sub.add_parser("verify-citations")
    v.add_argument("--out", type=lambda s: __import__("pathlib").Path(s), default=None)
    v.set_defaults(fn=cmd_verify_citations)
    sub.add_parser("probe-sources").set_defaults(fn=cmd_probe)
    sub.add_parser("render-docs").set_defaults(fn=cmd_render)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
