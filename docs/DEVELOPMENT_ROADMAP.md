# Development Roadmap (v0.2, dependency-based)

Supersedes `starter_pack/DEVELOPMENT_ROADMAP.md` (kept unmodified). Phases and exit gates are unchanged in
intent. This version adds dependencies, owner decisions and the Phase 1 work plan. **Effort figures are
unbenchmarked estimates.** Phase 1 records actual effort per work package so later estimates can be calibrated
(GAP G-20).

## 1. Phases, dependencies and gates

| Phase | Scope | Depends on | Owner decisions needed | Exit gate (evidence required) |
|---|---|---|---|---|
| 0: Scientific foundation | Taxonomy, sources, methodology, contracts, benchmark pre-registration, gap audit | — | Review and approve | Taxonomy citations live-verified (done: 160/161); **owner review of design and facet wording**; D-017 approved |
| 1: Foundation | Storage, migrations, adapters, evidence store, dedup, initial KG, CLI, frozen corpus | 0 | D-009, D-015, D-017 | Real sources ingested, queried, **restored after kill/restart** (T01, T02, T11 partial); T12/T14/T18 pass; **frozen corpus manifest** committed |
| 2: Recognition | Signature extraction, labelled dataset, baselines, B01 | 1 | D-003, D-004 | B01 result with confusion matrix, CI and error analysis; T03, T17, T19 |
| 3: Unknown recognition | Open-set, calibration, anomaly lab, hypotheses | 2 | D-007 | B02–B04 measured; no unsupported identities (wrong-identity rate reported); T04–T07, T24 |
| 4: Hidden value | Strategies S1–S8, rubric, ranking, feed | 1 (corpus), 3 (hypothesis records) | D-008, D-012; owner writes needs | **MVP**: verified useful tool absent from the frozen corpus; B05 with blind ratings |
| 5: Autonomy | Persistent queue, scheduling, budgets, recovery, dashboard | 1, 4 | D-006, D-013 | 24 h bounded run with timestamped logs; failure-recovery demonstration; T10, T11, T13, T15 |
| 6: Improvement | Versioned retrieval, ranking and model iterations | 2–5 | — | Frozen-set improvement, ablation, rollback (T20) |
| 7: Release audit | Full regression, security, reliability, docs | all | D-010 | All critical defects resolved; 72 h run; reproducible release; FINAL_SYSTEM_AUDIT |

Critical path: **0 → 1 → 4 (MVP)**. Phases 2 and 3 can run in parallel with early Phase 4 work, because the
hidden-value engine doesn't need the classifier. This follows the starter pack's advice to prove the product
objective before investing in complex novelty models.

## 2. Phase 0 completion record

| Deliverable | Status |
|---|---|
| Versioned machine-readable taxonomy (18 entries × 12 facets, 161 citations) | Done: `data/taxonomy/network_taxonomy.yaml` |
| Live citation verification | Done: 160 VERIFIED, 1 SOURCE_UNEXTRACTABLE, 0 QUOTE_NOT_FOUND (`evidence/phase0/citation_report.json`) |
| Source registry (58 references, 36 candidate ingestion sources) with reachability probe | Done |
| Data contracts v0.1.0 with evidence rules | Done, unit-tested |
| Research methodology, signature and discovery specifications | Done (design) |
| Benchmarks B01–B06 pre-registered | Done |
| Gap audit, scope disclosure, decision log, traceability (R00–R24, T01–T24) | Done |
| Owner review of the design | **Pending.** This is the Phase 0 exit gate |

## 3. Proposed Phase 1 plan (awaiting approval, D-017)

Goal: real sources are ingested, indexed, queried and restored after restart. The initial corpus is frozen as
the baseline for Phase 4.

| WP | Work package | Deliverables | Tests | Estimate (unbenchmarked) |
|---|---|---|---|---|
| 1.1 | Storage | SQLite schema v1 (sources, retrievals, documents, observations, entities, relations with validity intervals, claims, findings, jobs, checkpoints, audit events); migration runner with forward migration and backup/restore | T02 migrate, restore, restart-identical | 1–2 sessions |
| 1.2 | Evidence store | Content-addressed raw store outside git (retention per D-009); retrieval records persisted; atomic writes | T02, T11 (kill during write leaves no partial record) | 1 session |
| 1.3 | Adapter framework | Adapter interface (scope check, pacing, budget, retry/backoff, terms gate); terms read and recorded for each enabled source | T01 live, T13 caps, T14 out-of-scope rejected | 1 session |
| 1.4 | First adapters | 5 sources reachable here: `rfc_index_xml`, `arxiv_api`, `software_heritage_api`, `pypi_json`, `openalex_api`. GitHub, Wikidata and native protocols are tested on the owner's machine | T01 live per adapter, failure injection | 2 sessions |
| 1.5 | Normalisation and dedup | Canonical documents; near-duplicate detection; entity resolution with alias history (Freenet/Hyphanet case) | T18 | 1 session |
| 1.6 | Untrusted-content suite | Corpus of adversarial documents (embedded instructions, scope-change requests, oversized and malformed files, zip/PDF bombs) | T12, T06 partial | 1 session |
| 1.7 | Knowledge graph v0 | Load taxonomy and ingested entities; NetworkX projection; queries | T02, T07 retention of contradictions | 1 session |
| 1.8 | CLI and corpus freeze | `abyss ingest / query / status / freeze-corpus`; corpus manifest with hashes | End-to-end: ingest, kill, restart, query identical | 1 session |
| 1.9 | Reproducibility | Lock file, container recipe, CI workflow | T16 | 0.5 session |

Exit evidence: an `evidence/phase1/` run log showing ingestion, an interruption, a restore and identical query
results; the frozen corpus manifest; live adapter results with BLOCKED sources listed as BLOCKED.

## 4. Explicit non-claims (unchanged from the starter pack)

No phase demonstrates the existence of an entirely unobservable network. A simulated discovery isn't a real-world
discovery. Unknown model output doesn't establish a new protocol or criminal activity. A milestone doesn't pass
when only its UI or a mock works.
