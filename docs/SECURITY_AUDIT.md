# Security Audit (Phase 0 threat model and controls)

Scope: the Phase 0 code (`abyss/`) and the planned architecture. Security controls are kept separate from
behavioural design choices (SCOPE_AND_RESTRICTIONS s1–s4).

## 1. Assets
Owner's machine and credentials; the evidence store's integrity; the owner's private data (needs profile, email);
the reputation of the owner's IP with source operators.

## 2. Phase 0 attack surface and controls

| Threat | Where | Control in Phase 0 | Residual risk |
|---|---|---|---|
| Malicious or oversized responses | `fetch.http_fetch` | Byte cap (25 MiB, 64 KiB for probes); timeout; failures classified, not raised | Decompression isn't requested, so the cap applies to transfer bytes |
| Malformed PDFs (parser bugs) | `fetch.extract_text` | pypdf in-process with broad exception capture; `pdftotext` as a subprocess with a 120 s timeout | A pypdf vulnerability could affect the process. Phase 1: run parsers in a subprocess with resource limits |
| HTML/script content | `fetch.html_to_text` | stdlib HTMLParser; script/style dropped; nothing executed | None identified |
| Prompt injection through retrieved text | All consumers | No LLM in Phase 0; text is only hashed and substring-matched | Phase 1+: T12 adversarial suite before any LLM use |
| Scope escalation by data | `ScopePolicy` | Policy is loaded only from `config/scope.yaml`; immutable dataclass; `restricted` can't be enabled | Phase 1: host allow/deny enforced in every adapter |
| TLS interception or downgrade | `fetch._ssl_context` | Default verification; CA from `SSL_CERT_FILE` (the environment proxy's CA) | Trusts the configured CA. On the owner's machine that is the system store |
| Leaking private data in requests | `USER_AGENT` | Generic UA; no email or other personal data (D-011) | None |
| YAML deserialisation attacks | Loaders | `yaml.safe_load` only | None identified |
| Over-aggressive crawling (bans, terms breaches) | Fetcher | 1 request/s/host pacing; probes fetch 64 KiB at most | Terms not yet read (Phase 1 gate) |

## 3. Planned controls (Phase 1+)

- **T12 adversarial corpus:** embedded instructions ("ignore previous instructions", "add this host to scope"),
  scope-change requests in metadata, Unicode tricks, oversized and nested archives, PDF/zip bombs, invalid encodings.
- **Never auto-install or execute discovered software.** Any trial runs only in a sandbox the owner starts manually.
- Parser isolation (subprocess with CPU, memory and time limits).
- Secrets (API keys) read from the environment or OS keychain, never stored in the repository or the evidence store.
- Audit events for every scope decision, adapter run and status change.
- Dependency review and pinning (lock file plus hashes) before Phase 1 exit.

## 4. Findings in Phase 0
No critical findings. Medium: in-process PDF parsing (mitigation planned for Phase 1). Low: the reachability
probe contacts 36 endpoints per run (one after another, paced per host). It should stay a manual command and isn't scheduled.
