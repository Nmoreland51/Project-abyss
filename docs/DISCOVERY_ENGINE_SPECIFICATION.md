# Discovery Engine Specification (v0.1, specified, not implemented)

The hidden-value engine finds tools and knowledge that solve the owner's real problems, are hard to find through
conventional search, and can be backed by retrievable evidence. Directive s4.8: "Do not prioritize obscurity
for its own sake."

## 1. Non-goals

- Not a search engine with an AI front end. Keyword search is one weak signal among several.
- No mystery for its own sake. Obscurity is measured and reported, never used as the ranking objective.
- No automatic installation or execution of discovered software (SECURITY_AUDIT s3).
- No retrieval of restricted contents (hard limit H4). Those are recorded as leads.

## 2. Inputs

**Needs profile** (owner-authored, versioned, hashed before evaluation). Each need has:
`id, problem statement, context (what's used today and why it falls short), constraints (cost ceiling, licence,
platform, privacy, offline), priority area (directive s4.8 list), success description`.
Ten or more needs are required for B05. Needs are the owner's data and are never inferred silently from other information.

**Seeds.** Taxonomy entries, curated lists (`awesome_lists_seed`), and tools the owner already knows (so they can
be excluded as "already known").

## 3. Candidate generation (beyond search)

Each strategy is an adapter-level plugin that logs yield, cost and later precision (input to R17).

| ID | Strategy | Mechanism | Registered sources | Why it finds overlooked things |
|---|---|---|---|---|
| S1 | Curated-list expansion | Parse lists and follow links to project pages | `awesome_lists_seed`, `github_raw` | Human curation reaches the niche tail |
| S2 | Dependency-graph traversal | Dependencies and reverse dependencies of tools known to be good | `pypi_json`, `npm_registry`, `crates_io_api`, `debian_sources_api` | Small libraries trusted by respected projects rarely rank in search |
| S3 | Citation and code links | Papers in the priority areas that link to code repositories | `arxiv_api`, `openalex_api`, `dblp_api`, `zenodo_api` | Research software is under-indexed |
| S4 | Off-GitHub forges | Search forges and archives outside the dominant one | `software_heritage_api`, `gitlab_api`, `codeberg_api`, `sourcehut_git` | Search engines favour one forge |
| S5 | Archive resurrection | Dead links in old lists and papers, then check archived availability and the current maintenance status | `wayback_availability`, `internet_archive_search` | Moved projects are lost to search |
| S6 | Standards pipeline | IETF drafts and RFCs, then their implementations | `ietf_datatracker_api`, `rfc_index_xml` | Implementations of new protocols are obscure early on |
| S7 | Community streams with delay | Show HN / Lobsters items re-checked after N weeks for maintenance | `hn_api`, `lobsters_json` | Separates durable tools from launch hype |
| S8 | Alternative ecosystems | Native app and package ecosystems | `fdroid_index`, `huggingface_api`, Gemini/Gopher (where reachable) | Separate ecosystems with separate discovery |

## 4. Verification of a candidate

- **Capabilities.** Each claimed capability is a `Citation` quoting the project's own documentation, VERIFIED
  live (`Tool.documented_capabilities`). Uncited capabilities aren't shown.
- **Maintenance.** Latest release or commit date from registry metadata, with the retrieval date. Unknown stays `unknown`.
- **Licence.** An SPDX id from metadata when available; otherwise `unknown`, never guessed.
- **Cost.** Stated price, or `free` only if documented, otherwise `unknown`.
- **Independent corroboration.** Needed before a finding is `verified`: at least 2 distinct sources
  (`Finding` rule). Examples are a package registry plus the project docs, or a paper plus the repository.

## 5. Usefulness rubric (per need × tool, each 0–3, rule-based with evidence)

| Criterion | 0 | 3 |
|---|---|---|
| Fit | Documented capability unrelated to the need | Documented capability directly addresses the stated problem and constraints |
| Evidence strength | No verified citation | Verified citations plus independent corroboration |
| Maintenance | Archived or unknown, with known breakage | Recent releases, active issue handling |
| Accessibility | Unclear install, unsupported platform | Documented install on the owner's platform |
| Licence and cost fit | Incompatible or unknown | Compatible and within budget |
| Risk | Security advisories, abandonware, unclear provenance | No known issues, reproducible builds or signed releases |
| Advantage over alternatives | Strictly worse than a known alternative | Documented advantage for this need |

v0 ranking is a transparent weighted sum with owner-adjustable weights, and the explanation shows every
criterion with its evidence. Learning-to-rank is only considered in Phase 6, trained on B05 development needs and
evaluated on frozen evaluation needs.

## 6. Obscurity signals (reported, not optimised)

Mapped to the unknown vocabulary (RESEARCH_METHODOLOGY s2): baseline-search rank, forge stars and download
percentiles, Wikidata presence, Common Crawl hits, and whether the item is in the frozen initial corpus. Each signal
records its lookup date and whether the lookup was BLOCKED (e.g. Wikipedia 429 in this environment). A blocked
lookup is not a negative result.

## 7. Output: discovery feed item

`tool, need, rubric scores with evidence, overall score, obscurity signals, unknown category, uncertainties,
alternatives considered, status (candidate / corroborated / verified / rejected), provenance trail`. Synthetic
or test items are visibly labelled.

## 8. Failure modes and defences

| Failure | Defence |
|---|---|
| Popularity bias re-enters through sources | Obscurity is reported separately; S2–S5 favour structure over popularity |
| Hallucinated capabilities | Quote-required capability claims; live verification; B06 |
| SEO spam, fake or typosquatted packages | Corroboration across sources; registry metadata checks; never auto-install |
| Stale documentation | Maintenance signals; archive dates; re-verification before display |
| Leakage into B05 | Frozen corpus manifest; hashed evaluation needs; blind rating |

## 9. Evaluation

B05 (pre-registered): nDCG@5, precision@5, novelty@5, verified-claim rate and paired difference against the
baseline the owner chooses (D-008). MVP gate (Phase 4): at least one independently verified, useful tool absent
from the initial corpus, with a ranking explanation, found by a job that survived an interruption.
