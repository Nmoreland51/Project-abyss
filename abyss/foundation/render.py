"""Render human-readable documents from the machine-readable sources of truth.

Generated files carry a banner and are checked for drift by tests/unit/test_generated_docs.py,
so the YAML/CSV and the Markdown can't silently diverge.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Optional

from ..core.contracts import SourceKind
from .registry import REPO_ROOT, Registry
from .taxonomy import FACETS, LoadedTaxonomy, basis_counts

DOCS = REPO_ROOT / "docs"
TRACE_CSV = DOCS / "REQUIREMENTS_TRACEABILITY.csv"

FACET_TITLES = {
    "origin": "1. Origin",
    "purpose": "2. Why it was developed",
    "public_disclosure": "3. How it became publicly known",
    "architecture": "4. Architecture",
    "protocols": "5. Communication protocols",
    "resource_identification": "6. Resource identification",
    "discovery": "7. Information discovery",
    "documentation": "8. Public technical documentation",
    "infrastructure_relationship": "9. Relationship to existing infrastructure",
    "distinguishing_characteristics": "10. Distinguishing characteristics",
    "limitations": "11. Observable limitations",
    "comparison": "12. Similarities and differences",
}

_MARK = {
    "VERIFIED": "✔ verified",
    "QUOTE_NOT_FOUND": "✘ quote not found",
    "SOURCE_BLOCKED": "⛔ blocked",
    "SOURCE_RATE_LIMITED": "⛔ rate-limited",
    "SOURCE_FAILED": "✘ fetch failed",
    "SOURCE_UNEXTRACTABLE": "⚠ text unextractable",
    None: "not yet checked",
}


def _banner(source: str) -> str:
    return (
        f"<!-- GENERATED FILE: do not edit by hand. Source: {source}. "
        "Regenerate with `python -m abyss render-docs`. -->\n"
    )


def _md(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def _citation_index(report: Optional[dict]) -> dict[tuple[str, str, str, str], str]:
    idx: dict[tuple[str, str, str, str], str] = {}
    if report:
        for c in report["citations"]:
            idx[(c["entry"], c["facet"], c["ref"], c["quote"])] = c["outcome"]
    return idx


def render_taxonomy(loaded: LoadedTaxonomy, registry: Registry, report: Optional[dict]) -> str:
    tax = loaded.taxonomy
    idx = _citation_index(report)
    sources = registry.sources
    out: list[str] = [_banner("data/taxonomy/network_taxonomy.yaml + evidence/phase0/citation_report.json")]
    out.append(f"# Network Taxonomy (v{tax.taxonomy_version})\n")
    out.append(f"{tax.description.strip()}\n")
    out.append(f"- Schema version: `{tax.schema_version}`; taxonomy released: {tax.released.isoformat()}")
    out.append(f"- Taxonomy file SHA-256: `{loaded.sha256}`")
    if report:
        s = report["summary"]
        rep_tax = report["inputs"]["taxonomy"]["sha256"]
        stale = "" if rep_tax == loaded.sha256 else " **(STALE: the report was produced from a different taxonomy file; re-run verify-citations)**"
        out.append(
            f"- Citation check: run {report['started_at'][:19]}Z: {s['citations_by_outcome'].get('VERIFIED', 0)}"
            f" of {s['citations_total']} citations verified against live retrievals{stale}"
        )
        out.append(f"  - outcomes: " + ", ".join(f"{k}={v}" for k, v in s["citations_by_outcome"].items()))
    else:
        out.append("- Citation check: **not run**. No citation in this file has been verified.")
    out.append(
        "\n**How to read this.** Each facet is labelled with its epistemic basis: **sourced** (stated by the cited "
        "source; each citation carries a verbatim quote that is machine-checked against the live document), "
        "**analysis** (synthesis or comparison by the Abyss authors; not a sourced fact), or **unverified** "
        "(commonly stated but not yet checked against a retrieved source). A ✔ means only that the quoted text was present in the "
        "retrieved document at check time.\n"
    )
    out.append("## Summary\n")
    out.append("| id | name | kind | lifecycle | layers | topology | sourced / analysis / unverified | citations ✔ / total |")
    out.append("|---|---|---|---|---|---|---|---|")
    for e in tax.entries:
        bc = basis_counts(e)
        cites = [(f, c) for f in FACETS for c in e.facets[f].citations]
        ok = sum(1 for f, c in cites if idx.get((e.id, f, c.ref, c.quote)) == "VERIFIED")
        out.append(
            f"| `{e.id}` | {_md(e.name)} | {e.kind} | {e.lifecycle} | {', '.join(e.layers)} | {', '.join(e.topology)} "
            f"| {bc['sourced']} / {bc['analysis']} / {bc['unverified']} | {ok} / {len(cites)} |"
        )
    out.append("")
    for e in tax.entries:
        out.append(f"## {e.name} (`{e.id}`)\n")
        if e.aliases:
            out.append(f"- Aliases: {', '.join(e.aliases)}")
        out.append(f"- Kind: {e.kind}; lifecycle: {e.lifecycle}; last reviewed: {e.last_reviewed.isoformat()}")
        out.append(f"- Layers: {', '.join(e.layers)}")
        out.append(f"- Topology: {', '.join(e.topology)}")
        out.append(f"- Resource identification: {', '.join(e.resource_identification_types)}")
        out.append(f"- Discovery: {', '.join(e.discovery_types)}")
        if e.patterns:
            out.append(f"- Architectural patterns: {', '.join(e.patterns)}")
        if e.examples:
            out.append(f"- Examples: {', '.join(e.examples)}")
        if e.related:
            out.append(f"- Related entries: {', '.join(f'`{r}`' for r in e.related)}")
        out.append("")
        for f in FACETS:
            facet = e.facets[f]
            out.append(f"**{FACET_TITLES[f]}** _({facet.basis.value})_. {facet.text.strip()}")
            for c in facet.citations:
                src = sources.get(c.ref)
                title = src.title if src else "UNREGISTERED SOURCE"
                status = _MARK.get(idx.get((e.id, f, c.ref, c.quote)), "not yet checked")
                loc = f", {c.locator}" if c.locator else ""
                out.append(f"  - [{status}] `{c.ref}` ({_md(title)}{loc}): \"{_md(c.quote)}\"")
            out.append("")
        if e.open_questions:
            out.append("_Open questions:_")
            for q in e.open_questions:
                out.append(f"- {q}")
            out.append("")
    out.append("## Controlled vocabulary\n")
    v = tax.vocabulary
    for name, vocab in (("Layers", v.layers), ("Topology", v.topology), ("Resource identification", v.resource_identification),
                        ("Discovery", v.discovery), ("Architectural patterns", v.patterns)):
        out.append(f"### {name}\n")
        out.append("| term | definition |")
        out.append("|---|---|")
        for k, d in vocab.items():
            out.append(f"| `{k}` | {_md(d)} |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def render_registry(registry: Registry, citation_report: Optional[dict], probe_report: Optional[dict]) -> str:
    cite_outcome: dict[str, str] = {}
    if citation_report:
        for r in citation_report["retrievals"]:
            cite_outcome[r["source_id"]] = f"{r['outcome']} (HTTP {r['http_status']})" if r["http_status"] else r["outcome"]
    probe: dict[str, str] = {}
    if probe_report:
        for row in probe_report["results"]:
            r = row["retrieval"]
            if r is None:
                probe[row["source_id"]] = f"scope-rejected: {row['scope_reason']}"
            else:
                probe[row["source_id"]] = f"{r['outcome']}" + (f" (HTTP {r['http_status']})" if r["http_status"] else "") + (
                    f": {r['error'][:80]}" if r.get("error") else "")
    out: list[str] = [_banner("data/registry/*.yaml + evidence/phase0/*.json")]
    out.append("# Data Source Registry\n")
    out.append(
        "Machine-readable source of truth: `data/registry/references.yaml` (documents cited as evidence) and "
        "`data/registry/ingestion_sources.yaml` (APIs, feeds and datasets Phase 1+ adapters may use). Every record states "
        "its access basis, what is known about its licence or terms, and whether those terms were actually read "
        "(`terms verified`). **Reachability results are from the environment the probe ran in** (a cloud container "
        "with a policy-enforcing egress proxy), not from the owner's machine.\n"
    )
    for p, h, rf in registry.files:
        out.append(f"- `{p.relative_to(REPO_ROOT)}`: version {rf.registry_version}, {len(rf.sources)} sources, SHA-256 `{h[:16]}…`")
    if citation_report:
        out.append(f"- Citation retrievals from run {citation_report['started_at'][:19]}Z")
    if probe_report:
        out.append(f"- Reachability probe run {probe_report['started_at'][:19]}Z: " +
                   ", ".join(f"{k}={v}" for k, v in probe_report["summary"]["by_outcome"].items()))
    out.append("")
    srcs = registry.sources
    refs = [s for s in srcs.values() if s.kind is SourceKind.REFERENCE_DOCUMENT]
    ing = [s for s in srcs.values() if s.kind is not SourceKind.REFERENCE_DOCUMENT]
    out.append(f"## Reference documents ({len(refs)})\n")
    out.append("| id | title | publisher | published | reliability | access | last retrieval |")
    out.append("|---|---|---|---|---|---|---|")
    for s in sorted(refs, key=lambda s: s.id):
        out.append(
            f"| `{s.id}` | [{_md(s.title)}]({s.uri}) | {_md(s.publisher)} | {s.published or 'n/a'} | {s.reliability.value} "
            f"| {s.access_basis.value} | {cite_outcome.get(s.id, 'not retrieved')} |"
        )
    out.append("")
    out.append(f"## Candidate ingestion sources ({len(ing)})\n")
    out.append("None of these has been ingested yet. Phase 1 adapters will be built only for sources the owner approves, "
               "after their terms are read and recorded.\n")
    out.append("| id | title | kind | access basis | terms verified | reachability here |")
    out.append("|---|---|---|---|---|---|")
    for s in sorted(ing, key=lambda s: s.id):
        out.append(
            f"| `{s.id}` | [{_md(s.title)}]({s.uri}) | {s.kind.value} | {s.access_basis.value} | "
            f"{'yes' if s.terms_verified else 'no'} | {_md(probe.get(s.id, 'not probed'))} |"
        )
    out.append("")
    by_kind = defaultdict(list)
    for s in sorted(ing, key=lambda s: s.id):
        by_kind[s.kind.value].append(s)
    out.append("### Details\n")
    for s in sorted(ing, key=lambda s: s.id):
        out.append(f"#### `{s.id}`: {s.title}\n")
        out.append(f"- URI: {s.uri}" + (f" (probe: {s.probe_uri})" if s.probe_uri else ""))
        out.append(f"- Publisher: {s.publisher}; reliability: {s.reliability.value}. {s.reliability_notes}".rstrip())
        out.append(f"- Access basis: {s.access_basis.value}; licence/terms: {s.license_or_terms}"
                   + (f" (terms: {s.terms_uri})" if s.terms_uri else "") + f"; terms verified: {'yes' if s.terms_verified else 'no'}")
        if s.rate_limit_notes:
            out.append(f"- Rate limits / etiquette: {s.rate_limit_notes}")
        if s.coverage:
            out.append(f"- Coverage: {s.coverage}")
        if s.limitations:
            out.append(f"- Limitations: {s.limitations}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def load_traceability(path: Path = TRACE_CSV) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def render_traceability(rows: list[dict]) -> str:
    out = [_banner("docs/REQUIREMENTS_TRACEABILITY.csv")]
    out.append("# Requirements Traceability\n")
    out.append(
        "Source of truth: `docs/REQUIREMENTS_TRACEABILITY.csv`. Status vocabulary: `not_implemented`, `partial`, "
        "`implemented_unverified`, `simulated_only`, `verified`, `blocked` (see `abyss.core.contracts.ImplementationStatus`). "
        "`verified` requires an evidence artifact path; it is never assigned because something compiles or a mock passes.\n"
    )
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
    out.append("Status counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) + "\n")
    out.append("| id | requirement | phase | tests | status | implementation | evidence | notes |")
    out.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append(
            f"| {r['requirement_id']} | {_md(r['requirement'])} | {r['phase']} | {_md(r['test_ids'])} | **{r['status']}** "
            f"| {_md(r['implementation'])} | {_md(r['evidence'])} | {_md(r['notes'])} |"
        )
    return "\n".join(out).rstrip() + "\n"
