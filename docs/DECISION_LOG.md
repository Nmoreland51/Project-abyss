# Decision Log

Each decision has an owner (**Agent** = proposed and applied by the coding agent, reversible; **Owner** = the
project owner must decide), alternatives, rationale and a rollback path. **Pending** decisions block the phase
listed. Nothing here changes the owner's objectives. Any change of scope is flagged as such.

| ID | Decision | Status | Decided by | Blocks |
|---|---|---|---|---|
| D-001 | Taxonomy distinguishes `system`, `pattern` and `category` entries | Applied | Agent | none |
| D-002 | Hyphanet and Freenet are separate entries | Applied (evidence-driven) | Agent | none |
| D-003 | Observation modality for recognition | **Pending** | Owner | Phase 2 |
| D-004 | Recognition family label set v0.1 | **Pending** | Owner | Phase 2 |
| D-005 | SQLite + NetworkX first; PostgreSQL/Neo4j only on measured limits | Applied (per starter pack) | Agent | none |
| D-006 | Dashboard technology | **Pending** | Owner | Phase 5 |
| D-007 | Targets proposed beyond MASTER_AUDIT s9 | **Pending** | Owner | Phases 3–4 |
| D-008 | Conventional-search baseline for B05 | **Pending** | Owner | Phase 4 |
| D-009 | Raw-content retention policy | Phase 0 applied; Phase 1 proposed | Agent / Owner | Phase 1 |
| D-010 | Project licence | **Pending** | Owner | Release |
| D-011 | Contact address in API User-Agent | **Pending** (default: none) | Owner | none (lower rate limits) |
| D-012 | In-network content of Tor, I2P and Hyphanet | **Pending** (default: excluded) | Owner | Phase 4 scope |
| D-013 | Host for endurance runs | **Pending** | Owner | Phase 5 |
| D-014 | LLM role: optional, suggestion-only, never the authority | Applied (per MASTER_AUDIT s4) | Agent | none |
| D-015 | Native Gemini/Gopher/NNTP adapters | **Pending** | Owner | Phase 1 scope |
| D-016 | Phase 0 dependencies: stdlib + pydantic + PyYAML; pypdf optional | Applied | Agent | none |
| D-017 | Phase 1 scope and work packages | **Pending approval** | Owner | Phase 1 start |

---

### D-001: Entry kinds in the taxonomy
- **Context.** Directive s3 mixes concrete systems and architectural families (GAP G-03).
- **Decision.** Each entry has `kind: system | pattern | category`. Systems reference patterns from a controlled vocabulary.
- **Alternatives.** A flat list (rejected because labels are ambiguous); patterns as tags only, without entries (rejected because the directive asks for all 12 facets for DHT, P2P and the others).
- **Rollback.** Schema change in `abyss/foundation/taxonomy.py`; the taxonomy file is versioned.

### D-002: Hyphanet and Freenet
- **Evidence.** `hyphanet_rename_2023`: "decided to rename its new project Locutus to "Freenet." This required that Freenet change its name." (VERIFIED in `evidence/phase0/citation_report.json`).
- **Decision.** Two entries: `hyphanet` (the 1999 system) and `freenet` (formerly Locutus, development since 2019).

### D-003: Observation modality for recognition (Owner, pending)
| Option | What an "observation" is | Pros | Cons | Cost |
|---|---|---|---|---|
| **A. Documentation-derived (recommended first)** | Feature record from a project's own README/spec/manual | Legal; reproducible; uses registered sources; many items per family | Recognises *described* architectures, not runtime behaviour | Low (CPU only) |
| B. Owned-lab traffic | Flow features from containers running Tor, I2P, IPFS, Yggdrasil and others in an isolated lab the owner controls | Tests recognition from behaviour, which is closest to "unfamiliar network" detection | Needs a persistent host and container orchestration; joining public networks raises ethics questions, so it must use private test networks | Medium–high |
| C. Public traffic datasets | Published research captures (e.g. university VPN/Tor datasets) | Real traffic, citable | Licence and access terms must be verified; datasets age; label noise | Low–medium |
- **Recommendation.** A in Phase 2 and A + B in Phase 3 (B as a second modality for withheld-family experiments), with C only after terms are verified.
- **Impact if A only.** The Phase 3 claim must be worded as recognition of *documented* architectures. It doesn't cover traffic.

### D-004: Family label set (Owner, pending)
Proposed in SIGNATURE_SPECIFICATION s4 (9 pattern-level families). It is frozen at the Phase 2 start; any change afterwards makes a new label-set version.

### D-005: Storage
SQLite (stdlib) for Phase 1 with an explicit schema and migrations; NetworkX for graph analysis over exported
edges. Upgrade criteria: more than 10 million rows or concurrent-writer contention measured in Phase 5 runs.

### D-006: Dashboard (Owner, pending)
Options: (a) FastAPI + server-rendered HTML (Jinja/HTMX), which is minimal and quick to make honest about status (recommended for Phase 5); (b) React SPA (directive s10), better for the graph-explorer workspaces but more surface area; (c) (a) first, then (b).
Recommendation: (c).

### D-007: Additional targets (Owner, pending)
B04 false-anomaly rate ≤ 0.10 and B05 novelty@5 ≥ 0.5 are agent proposals, not owner targets. They can be accepted, changed or dropped before the phase that uses them.

### D-008: Conventional-search baseline (Owner, pending)
(a) A web search API (may need a key, and some are paid; terms vary); (b) forge search sorted by stars (free, but popularity-biased, which is exactly what Abyss tries to beat); (c) the owner's own time-boxed manual search (free, realistic, costs owner time). Recommendation: (c), plus (b) as a second baseline.

### D-009: Retention
Phase 0 stores hashes, sizes and timestamps only. Proposal for Phase 1: store raw content in a content-addressed
store outside git for sources whose terms permit it; otherwise keep the hash and a pointer to an archive (Wayback availability).

### D-010: Licence (Owner, pending)
`pyproject.toml` says "UNLICENSED: owner to choose". Common options: MIT/Apache-2.0 (permissive) or AGPL-3.0 (copyleft for network services).

### D-011: Contact address (Owner, pending)
Crossref and Wikimedia ask automated clients for contact details. The owner's email is private and won't be sent without explicit consent. The default is a generic UA.

### D-012: In-network content of anonymity networks (Owner, pending)
Default: Abyss studies these networks through public specifications, public aggregate metrics (Tor Onionoo) and
owned labs, but doesn't retrieve onion-service, eepsite or freesite content. This is a **design choice**, not a
hard limit: such content is often public within the network. Risks: legal exposure from unknowingly retrieving
illegal material, and safety. Options: keep excluded / metadata-only / full access with content filters and
manual review. Decide before Phase 4.

### D-013: Endurance host (Owner, pending)
Owner's machine (free, but uptime depends on it) or a small persistent VM (costs money). The cloud coding session can't host 24/72-hour runs.

### D-014: LLM role
An LLM may suggest extractions, summaries and candidate hypotheses. It may never be the sole basis of a
classification, verification or citation. Every LLM output is stored with model id and prompt hash and labelled
`analysis` until it's corroborated by retrieved evidence. Abyss must work with the LLM disabled.

### D-015: Native protocol adapters (Owner, pending)
Gemini, Gopher and NNTP adapters can be written in Phase 1, but in this environment they can only be tested against local test servers. Live tests would run on the owner's machine.

### D-016: Dependencies
Phase 0 uses the stdlib plus pydantic and PyYAML (pypdf optional) to keep the foundation small. FastAPI, SQLAlchemy and scikit-learn are introduced in the phase that first needs them, with versions pinned after testing.

### D-017: Phase 1 scope (Owner, approval required)
See DEVELOPMENT_ROADMAP s3. Approve as proposed, or amend.
