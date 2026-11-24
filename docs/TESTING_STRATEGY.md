# Testing and Scientific Validation Strategy (v0.2)

Supersedes `starter_pack/TESTING_STRATEGY.md` (kept unmodified). T01–T16 keep their original meaning. T17–T24
close gaps found in the Phase 0 audit (GAP_AUDIT.md, section 3): directive section 8 lists contamination,
leakage, duplicates and model failures, which had no test ID before.

## 1. Rules

1. **Status words are exact.** A test result is PASS, FAIL, BLOCKED (couldn't run: source unavailable,
   permission missing, environment limit) or SKIPPED (not attempted). Only PASS counts as passed. A skipped live
   test is reported as skipped, never as passed.
2. **Mocks prove logic, not capability.** A test using fakes (fake fetcher, fixtures, synthetic data) can show
   that the logic is correct. It can't show that a real-world capability works. Every requirement marked
   `verified` in the traceability matrix needs at least one live or real-data result with an evidence artifact.
3. **Synthetic stays labelled.** Synthetic and laboratory records carry `RecordScope.SYNTHETIC`/`LABORATORY`, and
   reports must show the label.
4. **Benchmarks are pre-registered** in `data/benchmarks/definitions.yaml` before data collection. Thresholds
   are fitted on validation data only.
5. **Every run records** the commit, environment, dataset version or manifest hash, command and output path.

## 2. Test tiers

| Tier | Location | Network | When it runs |
|---|---|---|---|
| unit | `tests/unit/` | none, or 127.0.0.1 only | every change: `python -m pytest` |
| live | `tests/live/` | real public sources | `ABYSS_LIVE=1 python -m pytest tests/live`; skipped (not passed) otherwise |
| integration / e2e | `tests/integration/` (Phase 1+) | local services, real sources where needed | every phase gate |
| benchmark | `benchmarks/` (Phase 2+) | frozen datasets | phase gates, per B-definition |
| endurance | scripted runs (Phase 5+) | real sources | 24 h / 72 h on a persistent host |
| human evaluation | protocol in B05 | n/a | Phase 4 gate, owner as blind rater |

## 3. Test matrix

| ID | Test | Required evidence | Phase | Phase 0 status |
|---|---|---|---|---|
| T01 | Public/authorized source ingestion | Real fixture or accessible source, provenance and content hash | 1 | partial: live retrieval with hashes in the citation checker; no ingestion adapter |
| T02 | Persistence and migrations | Restart with identical stored findings; migration and restore test | 1 | not implemented |
| T03 | Known architecture classification | Independent test data, confusion matrix, macro F1 (B01) | 2 | not implemented |
| T04 | Unknown family recognition | Entire families withheld; recall and false unknown rate (B02) | 3 | not implemented |
| T05 | Calibration and ambiguity | Calibration plot or error table; valid abstention (B03) | 3 | not implemented |
| T06 | False positives | Ordinary changes, corrupted and incomplete inputs (B04) | 3 | not implemented |
| T07 | Hypothesis falsification | Contradictory evidence changes status and is retained | 3 | contract-level only (REFUTED requires contradicting evidence) |
| T08 | Provenance and hallucination | Every verified claim backed by retrievable evidence; zero invented sources (B06) | 1 | partial: live citation verification of the taxonomy, plus a negative control |
| T09 | Hidden-value discovery | Blind human relevance labels and baseline comparison (B05) | 4 | not implemented |
| T10 | Autonomous endurance | Timestamped 24- and 72-hour job logs, budgets and actual outputs | 5 | not implemented |
| T11 | Recovery | Kill process; interrupt source/model/database; restore checkpoint | 1/5 | not implemented |
| T12 | Untrusted content | Embedded instructions can't change scope or cause tool execution | 1 | not implemented (design rule only) |
| T13 | Resource controls | Enforced memory/time/storage budgets and graceful stop | 5 | partial: byte cap and per-host pacing in fetcher |
| T14 | Scope and authorization | Out-of-scope sources rejected and clearly reported | 1 | partial: ScopePolicy unit tests |
| T15 | UI/API integrity | Live status agrees with backend; mock/simulation labelled | 5 | not implemented |
| T16 | Regression | Full test suite, pinned environment and commit identifier | all | partial: suite runs; lock file pending |
| T17 | Contamination and leakage | Near-duplicate and lineage checks across splits; name-blind variant; no test-set tuning | 2 | not implemented |
| T18 | Duplicate discoveries | Same entity from different sources/names resolved once; renamed entities (Freenet/Hyphanet) not merged by name | 1 | not implemented |
| T19 | Model failure and non-authority | LLM unavailable, timing out or hallucinating can't change a verification outcome | 2 | not implemented |
| T20 | Rollback | Revert a model or ranking version and reproduce its frozen-set metrics exactly | 6 | not implemented |
| T21 | Taxonomy and citation integrity | Schema, required subjects, 12 facets, citations resolve; live quote verification | 0 | **implemented** (unit + live) |
| T22 | Contract invariants | Evidence rules enforced by types | 0 | **implemented** (unit) |
| T23 | Owner-control integrity | Starter pack checksums, original requirements unchanged, generated docs in sync | 0 | **implemented** (unit) |
| T24 | Unknown-type labelling | Each unresolved item states which of the 7 unknown categories (RESEARCH_METHODOLOGY s2) applies, with justification | 3 | not implemented |

Coverage of directive section 8: unit (T21–T23), integration (T01, T02), end-to-end (T15, Phase 1 gate),
persistence (T02), source failures (T01, T08 outcomes), contradictory evidence (T07), duplicates (T18), unknown
classification (T04), false positives (T06), hallucination (T08, T19), contamination and leakage (T17),
malicious embedded instructions (T12), corrupted datasets (T06, T01), resource exhaustion (T13), interrupted
operations (T11), model and database failures (T11, T19), recovery (T11), long-duration operation (T10).

## 4. Result template

`Test ID / commit / dataset version / environment / expected / actual / metrics / evidence path / PASS-FAIL-BLOCKED-SKIPPED / limitations / follow-up`

## 5. Proposed targets (not achieved results)

Known-family macro F1 ≥ 0.90; withheld-family unknown recall ≥ 0.80; false unknown rate ≤ 0.05; 100% of verified
reports traceable; 0 fabricated citations; no loss of committed evidence after interruption; meaningful
usefulness improvement over the frozen baseline (B05 defines the metric); 24 h and 72 h bounded runs. Exact
definitions are in `data/benchmarks/definitions.yaml`.

## 6. Release decision

All critical tests must pass. Non-critical exceptions are documented explicitly. Failed live tests are never
replaced with mocks and called validated. Unavailable-source tests are BLOCKED, not passed.

## 7. How to run (Phase 0)

```bash
python -m pip install -e '.[dev]'          # or use the system Python if pydantic, PyYAML and pytest are present
python -m abyss validate                   # offline schema and cross-reference validation
python -m pytest                           # unit tier; live tests show as SKIPPED
ABYSS_LIVE=1 python -m pytest tests/live   # live tier: real retrievals (~1 minute)
python -m abyss verify-citations           # live: rewrites evidence/phase0/citation_report.json
python -m abyss probe-sources              # live: rewrites evidence/phase0/source_probe_report.json
python -m abyss render-docs                # regenerate generated docs after data changes
```
