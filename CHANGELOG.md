# Changelog

## 0.1.0 (2026-11-24): Phase 0 scientific foundation

Added
- Network taxonomy v0.1.0: 18 entries (12 systems, 5 patterns, 1 category), each with all 12 facets required by the
  owner directive s3. 161 citations, live-verified (160 VERIFIED, 1 SOURCE_UNEXTRACTABLE, 0 QUOTE_NOT_FOUND).
- Source registry v0.1.0: 58 reference documents and 36 candidate ingestion sources; reachability probe report.
- Data contracts v0.1.0 (`abyss/core/contracts.py`) enforcing evidence rules; scope policy with hard limits.
- Bounded retrieval, text extraction, quote verification, probe and doc-generation tooling (`abyss/foundation/`); CLI `python -m abyss`.
- Pre-registered benchmark definitions B01–B06.
- Documentation: master architecture, methodology, signature and discovery specifications, roadmap v0.2, testing
  strategy v0.2 (T01–T24), traceability (R00–R24), gap audit, scope disclosure, decision log, security audit,
  limitations, implementation status, final-audit checklist.
- Starter pack and owner directive preserved verbatim with SHA-256 checksums.

Changed (relative to starter pack; originals kept unmodified)
- Requirements R13–R24 and tests T17–T24 added. R01–R12 wording unchanged (enforced by test).

Migration notes
- First release; no migrations.
