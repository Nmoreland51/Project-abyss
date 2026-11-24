# Project Abyss — Testing and Scientific Validation

## Test matrix
| ID | Test | Required evidence |
|---|---|---|
| T01 | Public/authorized source ingestion | Real fixture or accessible source, provenance and content hash |
| T02 | Persistence and migrations | Restart with identical stored findings; migration and restore test |
| T03 | Known architecture classification | Independent test data, confusion matrix, macro F1 |
| T04 | Unknown family recognition | Entire architecture families withheld; recall and false unknown rate |
| T05 | Calibration and ambiguity | Calibration plot or error table; valid abstention |
| T06 | False positives | Ordinary architecture changes, corrupted inputs and incomplete observations |
| T07 | Hypothesis falsification | Contradictory evidence changes status and is retained |
| T08 | Provenance and hallucination | Every verified claim backed by retrievable evidence; zero invented sources |
| T09 | Hidden-value discovery | Blind human relevance labels and baseline comparison |
| T10 | Autonomous endurance | Timestamped 24- and 72-hour job logs, budgets and actual outputs |
| T11 | Recovery | Kill process, interrupt source/model/database; restore checkpoint |
| T12 | Untrusted content | Embedded instructions cannot change scope or cause tool execution |
| T13 | Resource controls | Enforced memory/time/storage budgets and graceful stop |
| T14 | Scope and authorization | Out-of-scope sources rejected and clearly reported |
| T15 | UI/API integrity | Live status agrees with backend; mock/simulation labeled |
| T16 | Regression | Full test suite, pinned environment and commit identifier |

## Benchmark protocol
Freeze train/validation/test splits, holding entire architecture families out for unknown recognition. Deduplicate related samples across splits. Fit thresholds only on validation. Compare against majority, simple feature classifier and nearest-neighbor baselines. Record class counts, imbalance, precision/recall, macro F1, uncertainty, confidence intervals, compute and known limitations. Use synthetic environments to test recognition mechanisms, not to claim real discovery.

## Proposed targets (not achieved results)
- Known-family macro F1 ≥ 0.90.
- Withheld-family unknown recall ≥ 0.80.
- False unknown rate among known observations ≤ 0.05.
- Verified reports with evidence references: 100%.
- Fabricated citations in evaluation: 0.
- Recovery: no loss of committed evidence after interruption.
- Usefulness: statistically or practically meaningful improvement over frozen baseline; define metric before testing.
- Endurance: 24-hour and 72-hour bounded runs without unrecovered critical errors.

## Result template
Test ID / commit / dataset version / environment / expected result / actual result / metrics / evidence path / PASS-FAIL-BLOCKED / limitations / follow-up.

## Release decision
All critical tests must pass. Document noncritical exceptions explicitly. Never replace failed live tests with mocks and call the real capability validated. Mark unavailable source tests as blocked, not passed.
