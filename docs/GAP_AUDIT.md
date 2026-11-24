# Consolidated Gap Audit (Phase 0, 2026-11-24)

This audit covers three things: the baseline state, defects and gaps in the starter pack design, and the state
of each required capability. Gaps are listed once, with the requirement or test that now tracks them.

## 1. Baseline

| Item | Finding |
|---|---|
| Repository | `Nmoreland51/Project-abyss`, branch `claude/project-abyss-architecture-0q77n9`. **No commits** before this change; no files. |
| Baseline tests | None existed (0 tests). No baseline pass/fail status is possible. |
| Environment | Linux container, Python 3.13.18, pydantic 2.13.5, PyYAML 6.0.3, pytest 9.1.1, pypdf 6.17.0, poppler `pdftotext`; 4 CPU, 15 GiB RAM, no GPU. HTTPS egress through a policy proxy (see SCOPE_AND_RESTRICTIONS s3). |
| Inputs | Starter pack (7 files) and the owner directive, preserved verbatim with SHA-256 checksums in `docs/starter_pack/`. |

## 2. Starter pack and directive: defects, inconsistencies and gaps

| ID | Gap | Severity | Resolution / tracking |
|---|---|---|---|
| G-01 | The requirements matrix (R01–R12) omits directive subsystems 4.1 (historical research), 4.3 (signature library), 4.9 (evidence engine), 4.10 (knowledge graph) and 4.12 (continuous learning), as well as the 15 UI workspaces, leakage controls, duplicate handling and the rule that the LLM is never the authority | High | Added R13–R24. Original R01–R12 text is kept unchanged, and a test checks that |
| G-02 | The test matrix (T01–T16) has no IDs for contamination/leakage, duplicates, model failure or rollback, all of which directive s8 lists | High | Added T17–T20. New Phase 0 tests are T21–T23, and T24 is unknown-type labelling |
| G-03 | The required study list mixes concrete systems (Tor, IPFS) with patterns (DHT, P2P) and a residual category ("experimental protocols"). Used as one label set, it gives ambiguous classification targets | High | Taxonomy `kind: system / pattern / category`. The recognition label set is proposed separately (SIGNATURE_SPECIFICATION s4; D-004) |
| G-04 | "Hyphanet and Freenet" have been **two different systems** since the 2023 rename (verified: `hyphanet_rename_2023`). Sources from before 2023 say "Freenet" and mean Hyphanet | Medium | Two taxonomy entries. Entity-resolution test T18 must not merge them by name |
| G-05 | "Observations" for recognition are undefined: documentation features or network traffic? This drives feasibility, cost and legality | High | D-003 (owner decision). Recommendation: documentation-derived first, owned-lab traffic later |
| G-06 | Macro F1 ≥ 0.90 on **system-level** families can't be measured meaningfully: several systems have only 1–3 independent implementations (e.g. Hyphanet: one reference node) | High | Pattern-level families with minimum sample sizes (B01: at least 50 lineage-independent items per family) and a census before freezing. Proposed in SIGNATURE_SPECIFICATION s4 |
| G-07 | Phase 4's "absent from initial corpus" needs a **frozen corpus manifest**, but no phase produces one | High | Added to the Phase 1 exit gate (DEVELOPMENT_ROADMAP) |
| G-08 | The "conventional search baseline" is undefined, and the options may cost money (search APIs) | Medium | D-008, with options listed in B05 |
| G-09 | T09 needs blind human ratings, but the owner's time isn't in the roadmap | Medium | Owner dependency recorded in B05 and the roadmap |
| G-10 | 24 h and 72 h runs (T10, Phase 5/7 gates) can't run in an ephemeral cloud session | High | D-013 (owner machine or persistent VM) |
| G-11 | UI stack conflict: React (directive s10) compared with "lightweight dashboard" and "minimal functional interface first" (MASTER_AUDIT s4, s7) | Low | D-006. Recommendation: minimal server-rendered UI first, React when backend validated |
| G-12 | Storage: the directive suggests PostgreSQL/Neo4j, and the starter pack says SQLite first | Low | Consistent if gated on measured limits (D-005) |
| G-13 | Deliverable name: REQUIREMENTS_TRACEABILITY.md (directive) compared with .csv (starter pack) | Low | Both. The CSV is the source of truth, and the MD is generated and drift-tested |
| G-14 | Candidate datasets (CAIDA, RIPE RIS) are listed without verified terms, and some CAIDA datasets require a request | Medium | Registry `terms_verified: false` everywhere. Reading terms is a Phase 1 gate per adapter |
| G-15 | Tension between "discover previously undocumented infrastructure" and the hard limits | Medium | Reconciled. Undocumented-infrastructure questions are studied only through public measurement data (BGP/RIS, OONI, Tor Metrics) and owned labs, and labelled with the 7-category unknown vocabulary (RESEARCH_METHODOLOGY s2) |
| G-16 | Acceptance targets have no sample sizes, confidence-interval method or tie to a specific dataset | Medium | B01–B06 pre-registered with metric definitions, CI method and minimum sizes |
| G-17 | "Useful" is undefined for the hidden-value engine | High | DISCOVERY_ENGINE_SPECIFICATION s5 rubric plus B05 metrics (nDCG@5, novelty@5, verified-claim rate) |
| G-18 | Untrusted-content rule has no concrete adversarial cases | Medium | T12 suite specified for Phase 1 (SECURITY_AUDIT s3) |
| G-19 | Native Gemini/Gopher/NNTP can't be reached from this environment | Medium | Environment limit E5. Adapters must be tested on the owner's machine (D-015) |
| G-20 | Effort estimates aren't benchmarked (owner preference: "estimates need benchmarking") | Medium | Roadmap estimates are labelled unbenchmarked. Phase 1 records actual effort per work package for calibration |
| G-21 | The architecture doesn't say how the LLM may be used | Medium | MASTER_ARCHITECTURE s6: suggestion-only, never the final arbiter, with outputs labelled (R20/T19) |

## 3. Capability status (MASTER_AUDIT s3 list)

Status words: **implemented** (code exists and is tested), **partial**, **specified** (design only), **missing**.

| Capability | Status | What exists | What's missing | Validated? |
|---|---|---|---|---|
| Historical research | partial | Taxonomy origin/disclosure facets with 160 verified quotes | Engine to mine patterns across sources (R13) | Quotes are live-verified. The faithfulness of paraphrases hasn't been human-reviewed |
| Architecture intelligence | partial | 18-entry taxonomy with controlled vocabularies (layers, topology, identification, discovery, patterns) | Classifier (R03, B01) | Schema-tested only |
| Signature library | specified | `Signature` contract; SIGNATURE_SPECIFICATION | Library and extraction (R14) | No |
| Open-set recognition | specified | B02/B03 pre-registered | Everything (R04) | No |
| Anomaly analysis | specified | B04 pre-registered; ordinary-explanation-first rule | Everything (R05) | No |
| Hypothesis engine | partial | `Hypothesis` contract requires alternatives and falsifiers; REFUTED needs contradiction | Engine and persistence (R06) | Contract unit tests |
| Source adapters | partial | Registry of 36 candidate sources with probe results; bounded fetcher | Adapters, terms review (R01) | Reachability probed live: 29 ok, 4 rate-limited, 2 failed, 1 blocked |
| Hidden-value engine | specified | DISCOVERY_ENGINE_SPECIFICATION; B05 | Everything (R07) | No |
| Evidence engine | partial | `RetrievalRecord` with hash/time/outcome; citation verifier; `ClaimBasis`/`RecordScope` | Persistent evidence store (R16) | Live: 161 citations checked |
| Knowledge graph | missing | Taxonomy `related` edges (seed) | Store, history, contradiction tracking (R15) | No |
| Autonomous orchestration | specified | `Job`/`Budget` contracts | Queue, scheduler, recovery (R08) | No |
| Continuous improvement | specified | Pre-registration policy | Versioning, ablation, rollback (R17) | No |
| Dashboard | missing | `JobStatus` vocabulary | UI (R10, R21) | No |

## 4. Gaps in the Phase 0 work itself

| ID | Gap | Why it matters | Next step |
|---|---|---|---|
| P0-1 | 14 of 216 facets are `unverified` and 83 are `analysis` | Only sourced facets are evidence | Register more primary sources (each entry lists `open_questions`) |
| P0-2 | 1 of 161 citations (Kademlia PDF) is `SOURCE_UNEXTRACTABLE` | It can't be machine-verified. The DHT origin facet also cites Chord, which is verified | Find a text-extractable copy, or OCR in Phase 1 |
| P0-3 | A VERIFIED citation proves the quote is in the source, not that the facet's paraphrase is faithful | Paraphrase drift is a hallucination risk | Owner or independent review of facet text (Phase 0 exit gate) |
| P0-4 | No source's terms have been read (`terms_verified: false` for all 94) | Ingestion legality and retention | Phase 1 gate, per adapter |
| P0-5 | Freenet (new) entry is thin (4 unverified facets) | Its documentation wasn't registered | Register whitepaper and manual |
| P0-6 | Single-author design. No independent review yet | Directive and owner process require independent audit | Owner review; optional second-agent review |
| P0-7 | The rename account comes from one side only (Hyphanet) | Possible bias | Register Freenet's account |
| P0-8 | Live results depend on this environment's egress, so reachability isn't portable | Your machine may differ | Re-run `probe-sources` and `verify-citations` locally |
