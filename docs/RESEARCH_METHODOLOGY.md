# Research Methodology (v0.1)

## 1. Epistemic states

Every stored statement has exactly one state, and the states never blur:

| State | Meaning | Required support | Can be shown as fact? |
|---|---|---|---|
| observation | Something retrieved or measured | RetrievalRecord (time, URI, hash) | Yes, as "source X says / measurement shows" |
| sourced claim | A statement attributed to a source | Citation with verbatim quote, VERIFIED by a live check | Yes, attributed |
| analysis | Synthesis, comparison or inference by Abyss or its authors | Reasoning recorded; citations optional | No. Shown as analysis |
| unverified | Commonly stated, not checked | None | No. Shown as unverified |
| hypothesis | Testable claim with alternatives and falsifiers | `Hypothesis` contract | No |
| verified finding | Hypothesis or claim that survived its test | `Finding` rules: evidence, method, ≥ 2 independent sources (real world) | Yes, with evidence |
| retracted | Previously asserted, now withdrawn | Reason retained | Shown as retracted |

## 2. Seven kinds of "unknown" (directive s2)

When Abyss can't place something, it must say *which* unknown applies (R24/T24):

| Code | Meaning | Typical evidence | What it does **not** imply |
|---|---|---|---|
| `unknown_to_user` | Documented and findable, just new to the owner | Owner rating "not already known" (B05) | Obscurity |
| `absent_from_mainstream_index` | Not found in the baseline indexes (Common Crawl, Wikidata, conventional search) | Recorded negative lookups with dates | Non-existence or hiddenness |
| `absent_from_corpus` | Not in Abyss's frozen initial corpus | Corpus manifest check | Novelty to the world |
| `documented_but_obscure` | Primary documentation exists, little secondary coverage | Primary source plus low mention counts | Low value |
| `undocumented_observed` | Observed in data (e.g. BGP/RIS, OONI), no documentation found | Observations plus failed documentation search | A new network. Ordinary causes come first |
| `hypothetical_unsupported` | Proposed with no supporting evidence | None | Anything |
| `unobservable_with_available_data` | No available data could show it either way | Data-coverage analysis | Existence or absence |

## 3. Source evaluation

Each source records `reliability` (primary, authoritative_secondary, secondary, community, unknown) with notes.
Rules:
- Prefer primary sources (specs, RFCs, project's own docs) for what a system *is*. Prefer independent sources for
  claims a project makes about *itself* (performance, adoption, security).
- Participant retrospectives (e.g. ISOC history) are authoritative but not contemporaneous. Corroborate dates with
  period documents.
- Self-descriptions are primary for intent and secondary for effectiveness.
- Promotional pages (e.g. some landing pages) are flagged in `reliability_notes`.
- Contradictions are recorded, not resolved by deleting one side.

## 4. Citation verification

`python -m abyss verify-citations` retrieves each cited source live, extracts text (HTML, plain text, PDF),
normalises typography and whitespace, and checks that each quote occurs. Outcomes: VERIFIED, QUOTE_NOT_FOUND,
SOURCE_BLOCKED, SOURCE_RATE_LIMITED, SOURCE_FAILED, SOURCE_UNEXTRACTABLE. Only VERIFIED is support.
Limits of the method:
- It shows that the quote was in the document at retrieval time. It doesn't show that the facet's paraphrase is
  faithful (human review is needed) or that the source is right.
- `whitespace_insensitive` matches (1 of 160 in the Phase 0 run) tolerate HTML/PDF extraction artefacts. They're
  recorded so they can be audited.
- Pages change. A later QUOTE_NOT_FOUND may mean the page changed, so Phase 1 adds archived copies (D-009).
- The negative control (`tests/live`) checks that fabricated and off-by-one claims are rejected.

## 5. Hypothesis lifecycle

1. **State** the claim, the observations it rests on, and at least one ordinary alternative (measurement error,
   outdated classification, incomplete data, ordinary version change).
2. **Pre-specify** the falsification conditions and the test before running it.
3. **Test** by retrieving new evidence or running a controlled experiment. Record everything, including failures.
4. **Update** the status: supported (needs supporting evidence), refuted (needs contradicting evidence),
   inconclusive, retracted. Old states stay in history.
5. **Escalate** only with stronger evidence. "New network" claims need independent observations from at least two
   unrelated data sources *and* the failure of every listed ordinary alternative. A classifier's `unknown`
   output is never enough on its own (MASTER_AUDIT s12).

## 6. Benchmark protocol

Definitions are pre-registered in `data/benchmarks/definitions.yaml` (B01–B06) before data collection.
- **Splits.** Group splits by lineage (forks, organisation, upstream), with frozen manifests and hashes. Whole
  families are withheld for open-set tests. Validation-unknown and test-unknown use different families.
- **Leakage.** Near-duplicate removal across splits, a name-blind feature variant, and no tuning on test data. The
  test split is evaluated once per frozen model version.
- **Baselines.** Majority, keyword rules, TF-IDF + logistic regression, k-NN, and conventional-search baselines for B05.
- **Statistics.** Per-class counts and imbalance, precision/recall, macro F1, a 95% bootstrap interval (2000
  resamples), paired tests for comparisons (Wilcoxon signed-rank across needs), and compute cost.
- **Reporting.** Failures and negative results are reported. Targets are "proposed", not achieved, until a
  result artifact exists.
- **Synthetic data** tests mechanisms only. It is never reported as real discovery.

## 7. Human evaluation (B05)

The owner writes need statements before development. Evaluation needs are hashed and hidden from development.
Results from Abyss and the baseline are pooled, deduplicated, shuffled and stripped of origin, then rated 0–3
with "already known" and "would try" flags. Inter-rater agreement is reported if a second rater takes part.

## 8. Reproducibility

Every run records the commit, dirty flag, environment, input hashes and outputs (see the citation report format).
Evidence artifacts live in `evidence/<phase>/`. Large datasets live outside git, with manifests and checksums.
