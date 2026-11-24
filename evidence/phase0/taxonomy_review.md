# Taxonomy wording review (v0.1.0 → v0.1.1), 2026-11-24

**What this is.** A fresh-context review of `data/taxonomy/network_taxonomy.yaml` v0.1.0 by a separate AI agent
session. It was given the file and the rules, not the author's conclusions. It checked whether each facet's
wording says more than its quotes support (paraphrase drift), something the automatic quote checker can't detect.

**What this is not.** It isn't a human review. The reviewer is the same kind of model as the author, so it's not
fully independent. Owner review remains the Phase 0 exit gate (DEVELOPMENT_ROADMAP).

## Findings (summary of the reviewer's report)

| Category | Count | Examples |
|---|---|---|
| 1. Sourced facet text beyond its quotes | 44 | `www.origin` names Berners-Lee with no quote naming him; `tor.protocols` described cells over TLS with only an onion-service quote; `usenet.public_disclosure` cited RFC 977's date without an rfc977 citation; `zeronet.resource_identification` claimed Bitcoin-style addresses with only a Namecoin quote |
| 2. Analysis facets stating checkable facts as settled | 10 | `federated.comparison` ("Email is the oldest widely deployed instance"); `freenet.distinguishing_characteristics` quoting "not privacy related" without a citation; `zeronet.discovery` asserting DHT use |
| 3. Factual errors | 1 | `gnunet.distinguishing_characteristics` called GNS "standardised-as-RFC", but RFC 9498 is Informational (Independent Submission) |
| 4. Inconsistencies | 5 | `mesh` claimed to be "the one family" with its own physical layer, though `arpanet` has one too; ZeroNet `lifecycle: operational` contradicted its "status unknown" limitation; I2P "fully distributed netDb" contradicted "floodfills are a concentration point" |

The reviewer also flagged minor drift in `freenet.infrastructure_relationship`, `ipfs.documentation` and
`mesh.purpose/architecture/protocols`. Those were fixed too.

## Disposition

All 60 findings were addressed in v0.1.1:
- **Quote added** where the retrieved source actually contained the supporting text (for example
  "Tim Berners-Lee, CERN"; "Under the hood, a channel is just a TLS connection over TCP, with a specified encoding for
  cells."; "February 1986 Network News Transfer Protocol"; "IPFS's take on Kademlia"). Citations rose from 161 to 222.
- **Wording cut** where no retrieved source supports it (for example "Solderpunk as maintainer", NDN and SCION
  architecture details, "dial-up", "internal DNS").
- **Basis downgraded** from analysis to `unverified` for 3 facets whose content is reported but unchecked
  (`mesh.resource_identification`, `experimental_protocols.protocols`, `experimental_protocols.resource_identification`).
- **Schema**: `lifecycle: unknown` added and used for ZeroNet.

Two points where the fix differs from the reviewer's suggestion:
- `zeronet.architecture`: the reviewer read the existing quotes as showing no peer verification. The README does say
  "the peers verify the `content.json` integrity (using the signature)", so that quote was added and the claim kept.
- `zeronet.discovery_types`: `dht_lookup` was removed as suggested. `tracker` was kept as a classification tag,
  because tags are analysis-level labels. The facet text claims only what the README quotes.

Verification of the fixes: `evidence/phase0/citation_report.json` (live run at the v0.1.1 commit).
