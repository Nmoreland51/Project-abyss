# Project Abyss — Master Audit and Implementation Directive

**Status:** Pre-development design audit; no existing codebase has been inspected.  
**Mission:** Discover overlooked digital knowledge, obscure software, experimental technologies and useful information ecosystems through evidence-based autonomous research.

## 1. Research hypothesis and boundaries
The Web is an application-layer information system, not the entirety of the Internet. Independent overlays, federated systems and private networks can exist on shared infrastructure. Abyss will investigate observable, documented or legitimately shared evidence of alternative systems. It must distinguish unknown to the user, absent from search indexes, absent from the local knowledge base, undocumented in the research corpus, and genuinely unobservable. It must not confuse novelty with criminality or assume an unexplained observation proves a hidden network. Private resources require permission; completely unobservable systems cannot be remotely discovered. No authentication bypass, unauthorized interception, or indiscriminate collection of private data. Controlled experiments use owned or explicitly authorized environments. Scope restrictions and their rationale must be documented, visible and not silently added.

## 2. Foundational scientific audit
Build a versioned taxonomy of ARPANET, WWW, Tor, I2P, Hyphanet, Freenet, GNUnet, IPFS, ZeroNet, Gopher, Gemini, Usenet, DHTs, peer-to-peer, mesh, federated and private intranet architectures. For each record: origin, creation purpose, public disclosure history, topology, protocol family, resource identification, discovery model, design documentation, infrastructure relationships, distinguishing characteristics, limitations, evidence quality and verification date. Separate physical infrastructure, transport, overlay, application and information ecosystem. Use public specifications and research literature; learn experimental recognition in laboratory data rather than targeting private services.

## 3. Capability audit
| Capability | Required behavior | Proof of completion |
|---|---|---|
| Historical research | Trace network origins and public disclosure | Primary-source-backed taxonomy |
| Architecture intelligence | Compare known design families | Independent classification benchmark |
| Signature library | Version documented architectural characteristics with provenance and ambiguity | Reproducible feature extraction on research/lab data |
| Open-set recognition | Reject unfamiliar observations without inventing identities | Family-held-out benchmark |
| Anomaly analysis | Consider ordinary explanations and measurement errors | False-positive evaluation and ablations |
| Hypothesis engine | State claim, evidence, alternatives, falsifier and verification plan | Reproducible experiment reports |
| Source adapters | Ingest accessible repositories, archives, research and authorized collections | Real integration tests |
| Hidden-value engine | Match discovered tools to practical needs | Blinded usefulness comparison with baseline |
| Evidence engine | Preserve sources, dates, hashes and uncertainty | All verified claims traceable |
| Knowledge graph | Track entities, relationships, contradictions and versions | Restart, deduplication and query tests |
| Autonomous orchestration | Manage objectives, queues, budgets, retries and checkpoints | Unattended bounded research runs |
| Continuous improvement | Benchmark and version retrieval/model changes | Frozen-set evaluation and rollback test |
| Dashboard | Show actual activity, findings and failures | End-to-end integration and status accuracy |

## 4. Architecture
Implement a local-first Python research core, FastAPI service, SQLite initially (PostgreSQL/Neo4j when justified), NetworkX, scikit-learn, optional PyTorch and Ollama, and a lightweight dashboard. Every ingestion adapter must record source authorization/scope, provenance, time and content type. Normalize observations; deduplicate; classify; detect anomalies; generate hypotheses; independently corroborate; publish only appropriately labeled findings. The LLM must not be the sole authority on experimental classification or verification. See SYSTEM_ARCHITECTURE.md.

## 5. Research and data integrity
Use a source registry with license, access conditions, acquisition dates, coverage and limitations. Store immutable raw inputs where retention is permitted, normalized observations, model versions and evidence references. Separate observations, inferred relationships, hypotheses, verified findings and retracted claims. Treat ingested text as untrusted data, not executable instructions. Evaluate against stale sources, duplicated records, contradictory evidence, poisoned documents and unknown families. Do not fabricate citations or claim successful experiments without logs and artifacts.

## 6. User-value research
Prioritize AI agents, productivity, business automation, education, software development, financial research, robotics and experimental computing. For each tool, assess problem solved, documented functionality, availability, license, cost, maintenance, dependencies, evidence and practical alternatives. Rank usefulness rather than mystery or popularity. Identify when a lead requires membership or permission without trying to obtain restricted contents. The deliverable is actionable, evidence-backed knowledge, not merely a count of anomalies.

## 7. Interface and operations
Provide mission control, research queue, taxonomy, architecture explorer, signature library, anomaly and hypothesis labs, discovery feed, evidence inspector, knowledge graph, benchmark reports, diagnostics and configuration. Expose real status: planned, queued, running, failed, blocked, complete. Clearly label synthetic demonstrations. Provide budgets, stop controls, audit events and recovery checkpoints. Use a minimal functional interface first; expand only after backend validation.

## 8. Roadmap and gates
Phase 0: research methodology, taxonomy, scope and design. Phase 1: ingestion, evidence and persistence. Phase 2: known architecture recognition. Phase 3: open-set and anomaly laboratory. Phase 4: practical knowledge discovery. Phase 5: autonomous orchestration. Phase 6: benchmark-driven improvement. Phase 7: independent system validation. Each gate requires code, real evidence where applicable, reproducible tests, traceability and a documented decision. See DEVELOPMENT_ROADMAP.md.

## 9. Proposed acceptance targets
Independent known-family macro F1 ≥ 0.90; withheld-family unknown recall ≥ 0.80; known-family false unknown rate ≤ 0.05; 100% verified reports traceable; zero fabricated citations in evaluation; successful restart/recovery; bounded 24- and 72-hour runs; measurable usefulness improvement over frozen baseline. These are proposed targets, not achieved results. Record uncertainty, dataset composition, confidence intervals, failures, resource cost and scope. Do not tune thresholds on the final test set.

## 10. Final audit deliverables
Maintain architecture, taxonomy, research methodology, signature specification, source registry, discovery specification, roadmap, traceability matrix, testing strategy, benchmark results, known limitations, implementation status, security audit and final system audit. Each requirement maps to code and tests or an explicit unresolved limitation. Do not label a feature production-ready merely because it compiles or passes mocks.

## 11. Development conduct
Use coordinated phases rather than endless isolated fixes. Audit current state before changes; implement related changes together; run full regression tests; disclose architectural tradeoffs and scope changes; report failures accurately. Avoid unnecessary infrastructure complexity and paid dependencies. Preserve the user's goal: discovering valuable knowledge beyond conventional retrieval. Never substitute speculative discovery claims for scientific evidence.

## 12. Definition of success
Abyss discovers independently verifiable, useful information absent from its initial corpus, accurately handles unknown observations in controlled benchmarks, and demonstrates durable autonomous research. A claim of a new network requires stronger independent evidence than a classification anomaly. The system must be capable of disproving its own hypotheses.
