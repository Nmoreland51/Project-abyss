# Scope and Restrictions Disclosure

Every limit that affects what Abyss does is listed here, sorted by **type**, so you can tell which limits are
fixed and which are choices you can change. Nothing in the code restricts behaviour without appearing in this
file. If you find a restriction that isn't listed, that's a defect (report it in GAP_AUDIT.md).

| Type | Meaning | Who can change it |
|---|---|---|
| **Hard limit** | Legal, ethical or security boundary. Enforced in code (`abyss/core/scope.py` `HARD_LIMITS`). | Not configurable. Changing one would change the project's legal and ethical basis. |
| **Security control** | Protects your machine and data (caps, TLS, no code execution). | You, with care, in code. Loosening one should be a recorded decision. |
| **Environment limit** | A property of *where the code ran* (this cloud container), not of the project. | Run on your own machine, or change the cloud environment's network settings. |
| **Design choice** | An optional default the agent proposed. Not required by law or security. | You. Each one links to a DECISION_LOG entry. |
| **Observability limit** | What no method can observe from available data. | Nobody. These follow from what data exists. |

## 1. Hard limits (not configurable)

| ID | Limit | Rationale |
|---|---|---|
| H1 | No authentication bypass, credential guessing or use of leaked credentials | Unauthorised access is illegal in most jurisdictions and outside the owner's stated goals (MASTER_AUDIT s1, directive s5) |
| H2 | No interception of traffic Abyss isn't a party to; packet capture only in owned or authorised labs | Same |
| H3 | No collection of private personal data without explicit permission | Privacy law; directive s5 |
| H4 | Restricted contents (membership-only, paywalled, private) are recorded as leads, never retrieved | Directive s5; MASTER_AUDIT s6 ("identify when a lead requires membership... without trying to obtain restricted contents") |
| H5 | Ingested text is data. It can't change scope or configuration or invoke tools | Prompt-injection and poisoning defence (MASTER_AUDIT s5) |

Code: `AccessBasis.RESTRICTED` sources can't be registered as ingestion endpoints (contract validator), and
`ScopePolicy.from_yaml` refuses a config that enables `restricted`. Tests: `tests/unit/test_scope.py`, `tests/unit/test_contracts.py`.

## 2. Security controls

| ID | Control | Current setting | Impact |
|---|---|---|---|
| C1 | TLS verification always on (proxy CA honoured via `SSL_CERT_FILE`) | on | none |
| C2 | Byte cap per retrieval | 25 MiB (citations), 64 KiB (probes) | Very large datasets need a dedicated, resumable downloader (Phase 1) |
| C3 | Per-host pacing | 1 request/s/host | Slower bulk collection; protects sources and avoids bans |
| C4 | Downloaded content is never executed or imported | always | none |
| C5 | PDF parsing with a pure-Python library (pypdf) or `pdftotext` subprocess with timeout | on | Malformed PDFs fail closed as `text_unextractable` |
| C6 | Fixed, identifying User-Agent without personal data | `ProjectAbyss-research/<version>` | Some APIs (Crossref, Wikimedia) prefer a contact address; see D-011 |

## 3. Environment limits observed in Phase 0 (cloud container, 2026-11-24)

These are facts about the **session environment**, measured by `evidence/phase0/source_probe_report.json`
and exploratory requests. They aren't project restrictions, and your own machine is likely to behave differently.

| ID | Observation | Impact | Alternative |
|---|---|---|---|
| E1 | GitHub API and HTML return 403 (session scoped to this repository); `raw.githubusercontent.com` works | Can't search GitHub or read repository metadata (stars, activity, licence) here | Run on your machine with a GitHub token; use Software Heritage, GitLab and Codeberg here |
| E2 | Wikipedia API returns 429; Wikidata returned 429 in exploration and 200 in the recorded probe (intermittent) | Unreliable mainstream-knowledge-base baseline here | Your machine; or an offline Wikidata dump |
| E3 | Semantic Scholar 429 without key; Codeberg 429 intermittently | Slower or blocked literature/forge queries | Free API key (you hold it); retries with backoff |
| E4 | SourceHut 502; Wayback CDX connection reset; Common Crawl intermittent | Archive and forge coverage gaps here | Retry; your machine |
| E5 | Outbound TCP 1965 (Gemini), 70 (Gopher) and 119 (NNTP) refused | Native Gemini/Gopher/Usenet adapters can't be live-tested here | Test on your machine; HTTPS mirrors where they exist (used for the Gemini spec) |
| E6 | Container is ephemeral (reclaimed after inactivity) | 24 h/72 h endurance runs (T10) can't be done here | Your machine or a persistent VM (D-013) |
| E7 | No GPU; Ollama not installed | Local-LLM features untested | Optional on your machine; the LLM is never an authority (D-014) |

## 4. Design choices (optional; you decide)

| ID | Default chosen | Why it was proposed | What it costs you | Decision |
|---|---|---|---|---|
| O1 | Content inside Tor onion services, I2P eepsites and Hyphanet freesites is **not ingested** in Phases 0–3 | Legal and safety risk of unknowingly retrieving illegal material; needs network clients; not needed to prove the MVP | Excludes some genuinely obscure, legitimate publications | D-012 (pending). Options: keep excluded / metadata-only from public indexes / full access with content filters |
| O2 | Retrieved content is hashed but not stored in Phase 0 | Licences not yet read per source | Re-retrieval is needed to re-check, and content may change | D-009: Phase 1 stores raw content where the licence permits |
| O3 | No contact email in User-Agent | Your email is private data; sending it needs your consent | Lower rate limits at some APIs | D-011 |
| O4 | Recognition starts from documentation-derived observations, not network traffic | Cheap, legal and reproducible, using registered sources | Doesn't yet test recognition from live behaviour | D-003 (pending; alternatives listed) |
| O5 | Minimal server-rendered dashboard before React | MASTER_AUDIT s7 says minimal UI first | Less polished UI early | D-006 (pending) |
| O6 | 1 request/s/host politeness | Courtesy and ban avoidance | Slower collection | Configurable in Phase 1 per source |
| O7 | Only `http(s)` URIs in contract v0 | Phase 0 had no native-protocol client | Gemini/Gopher/NNTP need a contract extension | Phase 1 if you approve native adapters (D-015) |

## 5. Observability limits (no configuration can change these)

- A system that produces no observable evidence in available data can't be discovered remotely. Abyss will label such
  questions `unobservable_with_available_data` (RESEARCH_METHODOLOGY s2) rather than speculate.
- Radio-only mesh networks with no Internet presence are observable only locally or through what their operators publish.
- Private intranets are invisible from outside by design. Their absence from public data isn't an anomaly.
- Absence from a search index is evidence of *obscurity to that index*, not of hiddenness or wrongdoing.

## 6. Agent-side policies (disclosure)

The coding agent works under its provider's usage policies. In Phase 0 none of them required narrowing or
changing any objective in the owner's directive. Everything listed above was chosen for the stated legal,
security or engineering reasons. If a future request conflicts with those policies, the agent will say so
explicitly in the phase report. It won't quietly reduce scope.
