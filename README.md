# Project Abyss

An evidence-driven research system for discovering overlooked, practically useful tools and information
ecosystems, using public and authorised sources only. **Current phase: 0 (scientific foundation).** This is
not yet a working discovery system. See `docs/IMPLEMENTATION_STATUS.md` for exactly what exists.

## What Phase 0 contains

| Item | Where |
|---|---|
| Versioned, machine-readable network taxonomy (18 entries × 12 facets; 222 quotes checked live) | `data/taxonomy/network_taxonomy.yaml` → `docs/NETWORK_TAXONOMY.md` |
| Source registry: 58 cited references + 36 candidate ingestion sources, with reachability probe | `data/registry/` → `docs/DATA_SOURCE_REGISTRY.md` |
| Typed data contracts that enforce the rules of evidence | `abyss/core/contracts.py` |
| Owner-controlled scope policy and hard limits | `config/scope.yaml`, `abyss/core/scope.py`, `docs/SCOPE_AND_RESTRICTIONS.md` |
| Live citation verifier and evidence reports | `abyss/foundation/citations.py`, `evidence/phase0/` |
| Pre-registered benchmarks B01–B06 | `data/benchmarks/definitions.yaml`, `docs/BENCHMARK_RESULTS.md` |
| Architecture, methodology, signature and discovery specifications | `docs/` |
| Gap audit, decision log, roadmap, traceability (R00–R24, T01–T24) | `docs/` |
| Original starter pack and owner directive, unmodified (checksummed) | `docs/starter_pack/` |

## Quick start

```bash
python -m pip install -e '.[dev]'           # Python ≥ 3.11; or use a Python that already has pydantic, PyYAML, pytest
python -m abyss validate                    # offline validation
python -m pytest                            # unit tests (live tests show as SKIPPED, which isn't a pass)
ABYSS_LIVE=1 python -m pytest tests/live    # live tests: real retrievals
python -m abyss verify-citations            # re-check every taxonomy quote against live sources
python -m abyss probe-sources               # reachability of candidate ingestion sources from *your* network
python -m abyss render-docs                 # regenerate generated docs after editing data files
```

## Rules this repository follows

- Planned, implemented, simulated and verified are always distinguished.
- No fabricated sources: every sourced statement has a quote that's checked against the live document.
- Unknown is a valid answer and is never promoted to "new network" without the hypothesis process.
- Scope limits are disclosed and sorted into hard limits, security controls, environment limits and owner choices.

Start reading at `docs/DEVELOPMENT_ROADMAP.md` (status and next steps) and `docs/DECISION_LOG.md` (decisions waiting for the owner).
