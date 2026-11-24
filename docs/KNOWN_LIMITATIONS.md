# Known Limitations (Phase 0)

## Capability
1. **No research engine exists yet.** Phase 0 delivers the foundation: taxonomy, registry, contracts, citation
   verifier, specifications and benchmark definitions. Nothing has been discovered. No classifier, ingestion
   pipeline, knowledge graph, orchestrator or UI exists.
2. **The taxonomy is a literature baseline, not research output.** It documents known systems from public sources.
3. **14 of 216 facets are `unverified` and 83 are `analysis`.** Only `sourced` facets with VERIFIED citations count as evidence.
4. **Quote verification isn't fact verification.** It proves the quote is in the source at retrieval time, not
   that the source is correct or that the surrounding paraphrase is faithful.
5. **One citation can't be machine-checked** (Kademlia PDF: no extractable text).
6. **The Freenet (formerly Locutus) entry is thin.** Its technical documentation hasn't been registered.

## Data and access
7. **No source terms have been read** (`terms_verified: false` for all 94). Reading them is a Phase 1 gate before any adapter.
8. **Reachability is environment-specific.** Results come from a cloud container behind an egress proxy: GitHub
   API/HTML blocked, Wikipedia and Semantic Scholar rate-limited, Wikidata and Codeberg intermittent, native Gemini/Gopher/NNTP ports closed
   (SCOPE_AND_RESTRICTIONS s3).
9. **Raw content isn't retained** in Phase 0 (hash only). Pages that change later can't be re-checked against the original bytes.
10. **Contract v0 supports only http(s) URIs.**

## Method
11. **The family label set and observation modality aren't decided** (D-003, D-004). Feasibility of the 0.90
    macro-F1 target depends on a census not yet done.
12. **Effort estimates are unbenchmarked.**
13. **Single-author review.** No independent audit has been performed yet.

## Operations
14. **Endurance runs can't happen in this cloud session** (ephemeral container). They need a persistent host (D-013).
15. **No lock file or container image yet.** Versions are recorded, not pinned (R23).
