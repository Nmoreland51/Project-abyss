# Signature Specification (v0.1, specified, not implemented)

A **signature** is a documented architectural characteristic, such as "clients fetch a signed directory of
relays" or "resources are named by a hash of their content". Each one carries provenance, reliability, known
limitations and known overlaps. Signatures are the features the recognition engine reasons with. Directive
s4.3: "Do not assume that architectural similarity proves common ownership, purpose or content."

## 1. Record (contract `abyss.core.contracts.Signature`)

| Field | Meaning | Rule |
|---|---|---|
| `id`, `version` | Stable id plus semantic version | Any change of definition bumps the version, and old versions are kept |
| `family` | The architecture family it characterises | From the frozen label set (s4) |
| `feature` | Feature id from the vocabulary (s2) | Controlled |
| `definition` | Operational definition: what must be observed for the feature to be present | Must be decidable from an observation |
| `provenance` | Citations (quotes) establishing that the family has the trait | At least 1; must be VERIFIED by the citation checker |
| `reliability` | Reliability of the provenance | From the source registry |
| `limitations` | When the signature misleads (versions, optional modes) | Required |
| `overlaps_with` | Other families or technologies sharing the trait | Required to be considered; may be empty only with justification |
| `last_verified` | Date of the last VERIFIED check of its provenance | Set only by the checker |

## 2. Feature vocabulary v0.1

Derived from the taxonomy's controlled vocabulary so that recognition and taxonomy share one language:

- `layer.<term>` for the 7 layers; `topology.<term>` for 9 topologies; `resource_id.<term>` for 10 identification
  models; `discovery.<term>` for 12 discovery mechanisms; `pattern.<term>` for 21 architectural patterns (see
  `docs/NETWORK_TAXONOMY.md`, Controlled vocabulary).
- Documentary features (Phase 2): default transport/port statements, URI schemes, cryptographic primitives named,
  addressing-format descriptions, required infrastructure (trackers, directory authorities, gateways) and
  persistence model. Each needs a quote as provenance at extraction time.

Feature values are `present / absent / not_stated`. **`not_stated` is not `absent`.** Missing documentation is
an incomplete observation, and B04 tests that it isn't mistaken for novelty.

## 3. Overlap examples (illustrating the rule; to be verified as signatures in Phase 2)

| Feature | Taxonomy entries with it | Consequence |
|---|---|---|
| `resource_id.content_hash` | IPFS (CIDs), Hyphanet (CHKs), BitTorrent | Not discriminative alone |
| `pattern.distributed_hash_table` | IPFS, I2P netDb, GNUnet, BitTorrent DHT | A component signature, not a system identity |
| `pattern.self_certifying_names` | Tor onion services, I2P, GNUnet GNS, ZeroNet, Yggdrasil | Common in privacy designs, so it says nothing about content or ownership |
| `pattern.trust_on_first_use` | Gemini (spec recommends TOFU) | Shared with other TOFU-based tools outside this taxonomy (unverified here) |
| `pattern.federation` | Usenet, email, XMPP, Matrix, ActivityPub | Federation family is large and heterogeneous; sub-families may be needed |

## 4. Proposed recognition label set v0.1 (owner decision D-004)

Pattern-level families, chosen so that each has many independent implementations (GAP G-06). Counts are
**unmeasured**: a census in Phase 2 step 1 decides whether a family stays, merges or is withheld.

| Family | Typical members (from taxonomy) | Expected supply of independent projects |
|---|---|---|
| F01 `web_hypertext` | HTTP servers, clients, frameworks | Very high |
| F02 `gopher_menu` | Gopher servers and clients | Medium (unmeasured) |
| F03 `gemini_capsule` | Gemini servers and clients | Medium (unmeasured) |
| F04 `anonymity_overlay` | Tor, I2P and similar implementations and clients | Low–medium |
| F05 `anonymous_datastore` | Hyphanet-style stores | Low, likely merged with F04 or F06 |
| F06 `content_addressed_storage` | IPFS implementations and similar | Medium |
| F07 `p2p_file_swarming` | BitTorrent clients and libraries | High |
| F08 `federated_messaging` | Email, XMPP, Matrix, ActivityPub and NNTP servers | High |
| F09 `mesh_routing` | OLSR, Babel, batman-adv, LoRa mesh firmware, Reticulum | Medium |
| F10 `key_addressed_overlay_ip` | Yggdrasil and similar overlay IPv6 networks | Low–medium |
| F11 `private_tunnel_vpn` | WireGuard, IPsec and other VPN implementations | High |

Withheld-family candidates for B02 (Phase 3): families with distinctive but learnable signatures and enough
items, e.g. F03, F09, F10. The final choice is made after the census.

**Recognition outputs** (directive s4.4): `recognized` (one family, calibrated confidence above the operating
point), `partially_recognized` (some signatures match and others conflict or are not stated), `ambiguous` (two or
more families plausible), `out_of_distribution` (far from all families), `needs_evidence` (too few stated
features). None of these outputs creates a "new network" claim. That requires the hypothesis process
(RESEARCH_METHODOLOGY s5).

## 5. Extraction (Phase 2 plan)

1. Retrieve the project's documentation through registered adapters (provenance plus hash).
2. Segment it, then apply rule-based extractors per feature. Each positive value stores the supporting quote.
3. Optional LLM suggestions are stored as `analysis` and need a quote before they count (D-014).
4. A human spot-check of 10% of extractions, reporting per-feature agreement.
5. Freeze the dataset manifest; then run B01, T03 and T17.

## 6. Versioning

Signatures, the vocabulary and the label set are versioned independently. A benchmark result names the exact
versions used. Deprecated signatures are kept with a reason.
