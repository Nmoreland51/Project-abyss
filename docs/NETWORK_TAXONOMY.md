<!-- GENERATED FILE: do not edit by hand. Source: data/taxonomy/network_taxonomy.yaml + evidence/phase0/citation_report.json. Regenerate with `python -m abyss render-docs`. -->

# Network Taxonomy (v0.1.1)

Phase 0 taxonomy of information networks and architectural patterns named in the owner's directive (section 3). Systems (concrete networks) and patterns/categories (architectural families) are kept as different kinds, because mixing them in one flat label set would make classification targets ambiguous (IPFS is both a system and an instance of the DHT and P2P patterns). Layers separate physical infrastructure, transport, overlay, application and information ecosystem, as MASTER_AUDIT section 2 requires.

- Schema version: `0.1.1`; taxonomy released: 2026-11-24
- Taxonomy file SHA-256: `6a0553820bd922a5e6438a47ba6ffcc2ec384678bb111cecbd9d82f5084426fe`
- Citation check: run 2026-11-24T07:38:29Z: 221 of 222 citations verified against live retrievals
  - outcomes: SOURCE_UNEXTRACTABLE=1, VERIFIED=221

**How to read this.** Each facet is labelled with its epistemic basis: **sourced** (stated by the cited source; each citation carries a verbatim quote that is machine-checked against the live document), **analysis** (synthesis or comparison by the Abyss authors; not a sourced fact), or **unverified** (commonly stated but not yet checked against a retrieved source). A ✔ means only that the quoted text was present in the retrieved document at check time.

## Summary

| id | name | kind | lifecycle | layers | topology | sourced / analysis / unverified | citations ✔ / total |
|---|---|---|---|---|---|---|---|
| `arpanet` | ARPANET | system | historical | physical, network, transport, application | distributed | 6 / 4 / 2 | 13 / 13 |
| `www` | World Wide Web | system | operational | application, information_ecosystem | client_server, decentralized | 7 / 5 / 0 | 17 / 17 |
| `tor` | Tor | system | operational | overlay, information_ecosystem | decentralized, client_server | 6 / 5 / 1 | 15 / 15 |
| `i2p` | I2P | system | operational | overlay, information_ecosystem | distributed, peer_to_peer | 6 / 3 / 3 | 13 / 13 |
| `hyphanet` | Hyphanet | system | renamed | overlay, application, information_ecosystem | peer_to_peer, friend_to_friend, distributed | 7 / 4 / 1 | 19 / 19 |
| `freenet` | Freenet (formerly Locutus) | system | experimental | overlay, application | peer_to_peer, decentralized | 6 / 2 / 4 | 12 / 12 |
| `gnunet` | GNUnet | system | operational | overlay, application | peer_to_peer, decentralized | 7 / 4 / 1 | 13 / 13 |
| `ipfs` | IPFS | system | operational | overlay, application, information_ecosystem | peer_to_peer, distributed | 9 / 3 / 0 | 14 / 14 |
| `zeronet` | ZeroNet | system | unknown | overlay, application, information_ecosystem | peer_to_peer, hybrid | 8 / 2 / 2 | 12 / 12 |
| `gopher` | Gopher | system | operational | application, information_ecosystem | client_server, decentralized | 9 / 3 / 0 | 14 / 14 |
| `gemini` | Gemini | system | operational | application, information_ecosystem | client_server, decentralized | 8 / 4 / 0 | 9 / 9 |
| `usenet` | Usenet | system | operational | application, information_ecosystem | federated, decentralized | 8 / 4 / 0 | 16 / 16 |
| `dht` | Distributed hash tables | pattern | mixed | overlay | distributed, peer_to_peer | 6 / 6 / 0 | 7 / 8 |
| `p2p` | Peer-to-peer architectures | pattern | mixed | overlay, application | peer_to_peer, hybrid, distributed | 6 / 6 / 0 | 8 / 8 |
| `mesh` | Mesh networks | pattern | mixed | physical, link, network | distributed, decentralized, peer_to_peer | 6 / 5 / 1 | 10 / 10 |
| `federated` | Federated information systems | pattern | mixed | application, information_ecosystem | federated, decentralized | 6 / 6 / 0 | 12 / 12 |
| `experimental_protocols` | Experimental networking architectures | category | experimental | network, overlay | distributed, decentralized | 4 / 6 / 2 | 6 / 6 |
| `private_intranet` | Private intranet architectures | pattern | mixed | network, transport, application | centralized, hierarchical, client_server | 7 / 5 / 0 | 11 / 11 |

## ARPANET (`arpanet`)

- Kind: system; lifecycle: historical; last reviewed: 2026-11-24
- Layers: physical, network, transport, application
- Topology: distributed
- Resource identification: network_address
- Discovery: out_of_band, directory_listing
- Architectural patterns: packet_switching
- Related entries: `www`, `usenet`, `private_intranet`

**1. Origin** _(sourced)_. The first Interface Message Processor (IMP) was installed by BBN at UCLA in September 1969, and four hosts were connected by the end of 1969. RFC 1, the first memo of the RFC series, is dated 7 April 1969.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "in September 1969 when BBN installed the first IMP at UCLA and the first host computer was connected"
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "by the end of 1969, four host computers were connected together into the initial ARPANET"
  - [✔ verified] `rfc1` (RFC 1: Host Software): "Date: 7 April 1969"

**2. Why it was developed** _(sourced)_. Resource sharing: giving users access to expensive remote computing resources instead of duplicating them.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "A major initial motivation for both the ARPANET and the Internet was resource sharing"

**3. How it became publicly known** _(sourced)_. A large demonstration at the International Computer Communication Conference (ICCC) in October 1972, described by participants as the first public demonstration. The RFC series, established in 1969, was meant as an informal, fast way to share ideas with other network researchers.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "In October 1972, Kahn organized a large, very successful demonstration of the ARPANET at the International Computer Communication Conference (ICCC)"
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "This was the first public demonstration of this new network technology to the public."
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "These memos were intended to be an informal fast distribution way to share ideas with other network researchers."

**4. Architecture** _(sourced)_. Host computers attached to Interface Message Processors (IMPs), whose software BBN specified. Agreeing on host software was the responsibility of the host groups.
  - [✔ verified] `rfc1` (RFC 1: Host Software): "The software for the ARPA Network exists partly in the IMPs and partly in the respective HOSTs."
  - [✔ verified] `rfc1` (RFC 1: Host Software): "BB&N has specified the software of the IMPs and it is the responsibility of the HOST groups to agree on HOST software."

**5. Communication protocols** _(sourced)_. The host protocol NCP was replaced by TCP/IP in a flag-day transition as of 1 January 1983, following the plan published in RFC 801.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "the transition of the ARPANET host protocol from NCP to TCP/IP as of January 1, 1983"
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "style transition, requiring all hosts to convert simultaneously"
  - [✔ verified] `rfc801` (RFC 801: NCP/TCP Transition Plan): "The goal is to make a complete switch over from the NCP to IP/TCP by 1 January 1983."

**6. Resource identification** _(unverified)_. Hosts were identified by numeric host/IMP addresses, and names were mapped through centrally maintained host tables before DNS. Commonly stated, but no primary source for the naming mechanism was retrieved in this version.

**7. Information discovery** _(unverified)_. There was no search mechanism. Resources were learned through RFCs, network information centre directories and personal contact. Not checked against a retrieved source in this version.

**8. Public technical documentation** _(sourced)_. The Request for Comments (RFC) series, begun in 1969, is the primary public documentation.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "In 1969 a key step was taken by S. Crocker (then at UCLA) in establishing the Request for Comments (or RFC) series of notes."

**9. Relationship to existing infrastructure** _(analysis)_. ARPANET was itself infrastructure (dedicated switching nodes). It is the ancestor of the Internet layer that later overlays (Tor, I2P, IPFS) run on, rather than an overlay itself.

**10. Distinguishing characteristics** _(analysis)_. For Abyss, ARPANET is the reference case of a network whose existence and design became public through incremental, openly circulated specifications plus a staged public demonstration. That disclosure pattern (specs, then demo, then papers) can be used as a template when assessing how other networks became known.

**11. Observable limitations** _(analysis)_. Historical system: there is no live observation, and all evidence is documentary. Participant retrospectives (isoc_brief_history) are authoritative but not contemporaneous, so they need corroboration with period documents (RFCs).

**12. Similarities and differences** _(analysis)_. Shares packet switching with all later Internet systems. Unlike the overlays in this taxonomy it owned its switching layer. Unlike private intranets it was a multi-institution research network documented in public.

_Open questions:_
- Register a primary source for host naming (e.g. RFCs on host tables) to upgrade resource_identification.

## World Wide Web (`www`)

- Aliases: WWW, the Web
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: application, information_ecosystem
- Topology: client_server, decentralized
- Resource identification: location_url, human_name_registry
- Discovery: hyperlinks, search_engine, directory_listing
- Architectural patterns: client_server, hypertext
- Related entries: `gopher`, `gemini`, `arpanet`, `usenet`

**1. Origin** _(sourced)_. Proposed by Tim Berners-Lee at CERN in "Information Management: A Proposal", written in March 1989 and redistributed in May 1990. CERN hosts the first website at info.cern.ch.
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "Information Management: A Proposal"
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "Tim Berners-Lee, CERN"
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "written in March 1989 and later redistributed unchanged apart from the date added in May 1990"
  - [✔ verified] `cern_info_first_website` (info.cern.ch: home of the first website): "home of the first website"

**2. Why it was developed** _(sourced)_. To manage general information about accelerators and experiments at CERN. The proposal discusses the loss of information about complex evolving systems and derives a solution based on distributed hypertext.
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "This proposal concerns the management of general information about accelerators and experiments at CERN."
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "It discusses the problems of loss of information about complex evolving systems and derives a solution based on a distributed hypertext system."

**3. How it became publicly known** _(sourced)_. Among the early public descriptions is Berners-Lee's Usenet post to alt.hypertext dated 6 August 1991, describing the WorldWideWeb project. This version doesn't establish whether it was the first public announcement.
  - [✔ verified] `w3c_tbl_alt_hypertext_1991` (Berners-Lee, alt.hypertext post 'Re: Qualifiers on Hypertext links' (6 Aug 1991), archived copy): "(Tim Berners-Lee) Newsgroups: alt.hypertext"
  - [✔ verified] `w3c_tbl_alt_hypertext_1991` (Berners-Lee, alt.hypertext post 'Re: Qualifiers on Hypertext links' (6 Aug 1991), archived copy): "Date: 6 Aug 91 14:56:20 GMT"
  - [✔ verified] `w3c_tbl_alt_hypertext_1991` (Berners-Lee, alt.hypertext post 'Re: Qualifiers on Hypertext links' (6 Aug 1991), archived copy): "The WorldWideWeb (WWW) project aims to allow links to be made to any information anywhere."

**4. Architecture** _(sourced)_. A distributed hypertext information system. Links can point to any information anywhere, and HTTP is the protocol defined for such systems.
  - [✔ verified] `w3c_tbl_proposal_1989` (Information Management: A Proposal (Berners-Lee, 1989/1990), HTML conversion): "derives a solution based on a distributed hypertext system"
  - [✔ verified] `w3c_tbl_alt_hypertext_1991` (Berners-Lee, alt.hypertext post 'Re: Qualifiers on Hypertext links' (6 Aug 1991), archived copy): "The WorldWideWeb (WWW) project aims to allow links to be made to any information anywhere."
  - [✔ verified] `rfc9110` (RFC 9110: HTTP Semantics): "for distributed, collaborative, hypertext information systems"

**5. Communication protocols** _(sourced)_. HTTP (semantics in RFC 9110) and the URI generic syntax (RFC 3986). HTML is not cited in this version.
  - [✔ verified] `rfc9110` (RFC 9110: HTTP Semantics): "HTTP Semantics"
  - [✔ verified] `rfc3986` (RFC 3986: Uniform Resource Identifier (URI): Generic Syntax): "This specification defines the generic URI syntax"

**6. Resource identification** _(sourced)_. Uniform Resource Identifiers. Web URLs combine an access method (scheme), a host and a path, so they identify a location rather than the content itself.
  - [✔ verified] `rfc3986` (RFC 3986: Uniform Resource Identifier (URI): Generic Syntax): "A Uniform Resource Identifier (URI) is a compact sequence of characters that identifies an abstract or physical resource."
  - [✔ verified] `w3c_tbl_alt_hypertext_1991` (Berners-Lee, alt.hypertext post 'Re: Qualifiers on Hypertext links' (6 Aug 1991), archived copy): "The address format includes an access method (=namespace), and for most name spaces a hostname and some sort of path."

**7. Information discovery** _(analysis)_. Following hyperlinks, curated directories and, mainly, crawler-based search engines. Content that isn't linked or indexed is effectively undiscoverable to most users. That gap is the premise of the Abyss hidden-value engine.

**8. Public technical documentation** _(sourced)_. IETF RFCs (HTTP, URI) plus W3C and WHATWG specifications (the latter are not registered in this version).
  - [✔ verified] `rfc9110` (RFC 9110: HTTP Semantics): "HTTP Semantics"

**9. Relationship to existing infrastructure** _(analysis)_. An application-layer system running over the Internet's transport and naming (TCP/QUIC, DNS). It is not the Internet itself, which is the distinction MASTER_AUDIT section 1 draws.

**10. Distinguishing characteristics** _(analysis)_. One address format spanning many access methods, so the Web could link into pre-existing systems (Gopher, news) instead of replacing them. Publication needs only a server, not anyone's permission.

**11. Observable limitations** _(analysis)_. Location addressing means links break when content moves (no built-in integrity or persistence). Discovery is concentrated in a small number of commercial search indexes, which define what counts as "findable".

**12. Similarities and differences** _(analysis)_. Compared with Gopher: free-form hypertext instead of menus. Compared with Gemini: richer and extensible, where Gemini deliberately constrains features. Compared with IPFS: location-addressed, where IPFS is content-addressed.

## Tor (`tor`)

- Aliases: The Onion Router, onion services
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: overlay, information_ecosystem
- Topology: decentralized, client_server
- Resource identification: location_url, public_key
- Discovery: consensus_directory, out_of_band
- Architectural patterns: onion_routing, self_certifying_names
- Related entries: `i2p`, `hyphanet`, `gnunet`

**1. Origin** _(sourced)_. Onion routing began in 1995 with Goldschlag, Reed and Syverson at the U.S. Naval Research Lab. The Tor network was first deployed in October 2002, and the Tor Project, Inc. was founded as a nonprofit in 2006.
  - [✔ verified] `tor_history` (Tor Project: History): "in 1995, David Goldschlag, Michael G. Reed, and Paul Syverson at the U.S. Naval Research Lab (NRL)"
  - [✔ verified] `tor_history` (Tor Project: History): "in October 2002 when the Tor network was initially deployed, its code was released under a free and open software license"
  - [✔ verified] `tor_history` (Tor Project: History): "In 2006, the Tor Project, Inc., a 501(c)(3) nonprofit organization, was founded"

**2. Why it was developed** _(sourced)_. To anonymize low-latency TCP-based applications such as web browsing, secure shell and instant messaging.
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "Tor is a distributed overlay network designed to anonymize low-latency TCP-based applications such as web browsing, secure shell, and instant messaging."

**3. How it became publicly known** _(sourced)_. The code was released under a free and open software licence when the network was first deployed in October 2002. The design was published at the 13th USENIX Security Symposium as "Tor: The Second- Generation Onion Router".
  - [✔ verified] `tor_history` (Tor Project: History): "in October 2002 when the Tor network was initially deployed, its code was released under a free and open software license"
  - [✔ verified] `tor_design_2004` (Tor: The Second-Generation Onion Router (USENIX Security 2004), abstract page): "13th USENIX Security Symposium"
  - [✔ verified] `tor_design_2004` (Tor: The Second-Generation Onion Router (USENIX Security 2004), abstract page): "Tor: The Second-Generation Onion Router"
  - [✔ verified] `tor_design_2004` (Tor: The Second-Generation Onion Router (USENIX Security 2004), abstract page): "We present Tor, a circuit-based low-latency anonymous communication service."

**4. Architecture** _(sourced)_. An overlay built of servers called relays. Clients download a signed directory of relays and build multi- hop circuits, typically through three relays. The second-generation design added perfect forward secrecy, congestion control, directory servers and location-hidden services through rendezvous points.
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "The network is built of a number of servers, called relays"
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "To connect to the network, a client needs to download an up-to-date signed directory of the relays on the network."
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "A circuit is built over a sequence of relays (typically three)."
  - [✔ verified] `tor_design_2004` (Tor: The Second-Generation Onion Router (USENIX Security 2004), abstract page): "adding perfect forward secrecy, congestion control, directory servers, integrity checking, configurable exit policies, and a practical design for location-hidden services via rendezvous points"

**5. Communication protocols** _(sourced)_. Clients and relays exchange messages called cells over channels, which are TLS connections over TCP. Onion services use a rendezvous protocol that aims to give the responder anonymity.
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "Under the hood, a channel is just a TLS connection over TCP, with a specified encoding for cells."
  - [✔ verified] `tor_rend_spec_overview` (Tor Specifications: Hidden services: overview and preliminaries): "Hidden services aim to provide responder anonymity for bidirectional stream-based communication on the Tor network."

**6. Resource identification** _(unverified)_. Ordinary web resources are reached by URL through exit relays. Onion services use .onion addresses derived from the service's public key (self-certifying). The key-derivation details were not quoted from the specification in this version.

**7. Information discovery** _(analysis)_. Relays are discovered through the signed consensus directory. Onion services aren't globally enumerable by design: their addresses spread out of band (links, lists). Abyss must not attempt to enumerate them.

**8. Public technical documentation** _(sourced)_. Public specifications at spec.torproject.org and peer-reviewed design papers.
  - [✔ verified] `tor_spec_intro` (Tor Specifications: A short introduction to Tor): "A short introduction to Tor"

**9. Relationship to existing infrastructure** _(analysis)_. An overlay on the public Internet. Relays are ordinary Internet hosts, and exit relays connect to ordinary Internet services. It depends on TCP/IP and, for bootstrapping, on reachable directory authorities.

**10. Distinguishing characteristics** _(analysis)_. Client anonymity for low-latency streams through a directory-coordinated relay set. Responder anonymity comes through onion services. Directory authorities are a semi-centralized trust anchor in an otherwise distributed system.

**11. Observable limitations** _(analysis)_. Low-latency design trades resistance to global traffic analysis for usability. The directory authority set is a centralization point. For Abyss, onion-service content is out of scope in Phase 0 (see SCOPE_AND_RESTRICTIONS.md).

**12. Similarities and differences** _(analysis)_. Compared with I2P: bidirectional circuits and an exit-to-Internet focus, where I2P uses unidirectional tunnels and an internal-services focus. Compared with Hyphanet: real-time streams, where Hyphanet is store-and-retrieve publication.

## I2P (`i2p`)

- Aliases: Invisible Internet Project
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: overlay, information_ecosystem
- Topology: distributed, peer_to_peer
- Resource identification: public_key, human_name_registry
- Discovery: dht_lookup, out_of_band
- Architectural patterns: garlic_routing, distributed_hash_table, self_certifying_names
- Related entries: `tor`, `hyphanet`, `gnunet`

**1. Origin** _(sourced)_. In active development since early 2003. The project's technical introduction was originally written by jrandom in 2003.
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "It has been in active development since early 2003"
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "This document was originally written by jrandom in 2003."

**2. Why it was developed** _(sourced)_. To provide an anonymous network layer on which anonymity- or security-conscious applications can run, each making its own anonymity, latency and throughput trade-offs.
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "I2P is a scalable, self organizing, resilient packet switched anonymous network layer, upon which any number of different anonymity or security conscious applications can operate."
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "Each of these applications may make their own anonymity, latency, and throughput tradeoffs"

**3. How it became publicly known** _(unverified)_. Open-source development with public documentation from the start. The project's own history page wasn't retrieved in this version, so details of the early announcement are unverified.

**4. Architecture** _(sourced)_. An overlay on a packet-switched network using unidirectional tunnels: the sender sets up an outbound tunnel and the receiver an inbound one. Garlic encryption bundles multiple messages, and a network database (netDb) DHT is served by "floodfill" routers.
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "I2P is an overlay network designed to be run on top of a functional packet switched network"
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "unidirectional tunnel creation with a single message"
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "sets up an outbound tunnel, while the receiver"
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "lets Alice's router wrap up multiple messages into a single "garlic message""
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "Those routers that do participate in the DHT and respond to leaseset lookups are called 'floodfills'."

**5. Communication protocols** _(unverified)_. Router-to-router transports (NTCP2 and SSU2 at the time of writing) carry tunnel messages. The specific transport names were not quoted in this version.

**6. Resource identification** _(unverified)_. Services are identified by cryptographic destinations (public-key based), with human-readable names through a local address book. The page's "Naming Library and Address Book" appendix exists, but its claims weren't quoted.

**7. Information discovery** _(sourced)_. The netDb carries two kinds of metadata: routerInfo (how to contact a router) and leaseSets (how to contact a destination). Routers that take part in the DHT and answer leaseSet lookups are floodfills.
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "The two types of metadata carried are "routerInfo" and "leaseSets""
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "Those routers that do participate in the DHT and respond to leaseset lookups are called 'floodfills'."

**8. Public technical documentation** _(sourced)_. Public documentation and specifications at geti2p.net. The intro page warns that parts may be obsolete.
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "some information may be obsolete or incomplete"

**9. Relationship to existing infrastructure** _(sourced)_. An overlay on an existing packet-switched network (the Internet).
  - [✔ verified] `i2p_intro` (I2P: A Scalable Framework for Anonymous Communication): "I2P is an overlay network designed to be run on top of a functional packet switched network"

**10. Distinguishing characteristics** _(analysis)_. Every participant is a router, and inbound and outbound paths are separate unidirectional tunnels. Garlic bundling is used, and the design favours services hosted inside the network over exit to the public Internet.

**11. Observable limitations** _(analysis)_. Documentation self-describes as partly obsolete, so claims need current specifications. Floodfill routers are a concentration point for netDb.

**12. Similarities and differences** _(analysis)_. Compared with Tor: a DHT-based netDb served by floodfill routers, where Tor has directory authorities, and unidirectional packet tunnels, where Tor has TCP circuits. Compared with GNUnet: both are full-stack privacy-oriented P2P frameworks with their own naming.

## Hyphanet (`hyphanet`)

- Aliases: Freenet (1999-2023 name), Fred
- Kind: system; lifecycle: renamed; last reviewed: 2026-11-24
- Layers: overlay, application, information_ecosystem
- Topology: peer_to_peer, friend_to_friend, distributed
- Resource identification: content_hash, public_key
- Discovery: out_of_band, hyperlinks
- Architectural patterns: content_addressing, self_certifying_names, small_world_routing
- Related entries: `freenet`, `gnunet`, `i2p`, `ipfs`

**1. Origin** _(sourced)_. Started as the Freenet Project by Ian Clarke around July 1999, based on his paper "A Distributed Decentralised Information Storage and Retrieval System". In early 2023 the board of Freenet Project, Inc. gave the "Freenet" name to its new project Locutus, and the original Freenet was renamed Hyphanet.
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "Ian Clarke Hyphanet is based on Ian's paper "A Distributed Decentralised Information Storage and Retrieval System""
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "Ian started the Freenet Project around July of 1999"
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "In early 2023, the board of Freenet Project, Inc"
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "decided to rename its new project Locutus to "Freenet." This required that Freenet change its name."
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "Freenet renamed to Hyphanet"

**2. Why it was developed** _(sourced)_. Censorship-resistant and privacy-respecting publishing and communication.
  - [✔ verified] `hyphanet_home` (Hyphanet home page): "Hyphanet is peer-to-peer network for censorship-resistant and privacy-respecting publishing and communication."

**3. How it became publicly known** _(sourced)_. Development began in 1999, based on Ian Clarke's paper. The rename was announced on the project site on 26 June 2023.
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "Freenet began development in 1999."
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "Hyphanet is based on Ian's paper"
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "Mon 26 June 2023"

**4. Architecture** _(sourced)_. A decentralized peer-to-peer data store. Nodes contribute bandwidth and disk ("data store") for encrypted chunks, and traffic is routed through other nodes. In "darknet" mode nodes connect only to friends.
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "Communications by Hyphanet nodes are encrypted and routed through other nodes"
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "Users contribute to the network by giving bandwidth and a portion of their hard drive (called the "data store") for storing encrypted chunks of data."
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "if used in "darknet" mode, where users only connect to their friends, is very difficult to detect"

**5. Communication protocols** _(unverified)_. Hyphanet's own node-to-node protocol (the "Fred" reference implementation). Routing is commonly described as small-world greedy routing. Not verified against a protocol specification in this version.

**6. Resource identification** _(sourced)_. Content Hash Keys (CHKs) guarantee the integrity of retrieved data. Signed Subspace Keys (SSKs) allow content to be digitally signed and are more flexible than CHKs.
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "Hyphanet has long-supported the concept of "Content Hash Keys" which guarantee the integrity of retrieved data."
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "Hyphanet also supports "Signed Subspace Keys" which allow content to be digitally signed."
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "is more flexible than CHKs"

**7. Information discovery** _(analysis)_. No global search. Keys and freesite links spread out of band and through index sites inside the network. Content persists according to popularity, not by publisher guarantee.

**8. Public technical documentation** _(sourced)_. Project documentation at hyphanet.org, plus the founding paper.
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "Forward Error Correction"

**9. Relationship to existing infrastructure** _(analysis)_. An overlay running on Internet hosts. It needs no servers, but bootstrapping in opennet mode depends on reachable seed nodes (not verified in this version).

**10. Distinguishing characteristics** _(sourced)_. Forward error correction lets a file be reconstructed even if some parts can't be retrieved, and "healing" reconstructs and reinserts missing file components. In darknet mode, where users connect only to friends, a node is very difficult to detect.
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "which allows a file to be reconstructed even if some of the parts of that file can't be retrieved"
  - [✔ verified] `hyphanet_docs` (Hyphanet: Documentation): "Uniquely, Hyphanet also supports "healing", which involves the reconstruction and reinsertion of missing file components."
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "if used in "darknet" mode, where users only connect to their friends, is very difficult to detect"

**11. Observable limitations** _(analysis)_. Unpopular content can disappear, so persistence isn't guaranteed. Naming history is confusing: sources before 2023 that say "Freenet" mean Hyphanet, and later ones may mean the new Freenet. Abyss entity resolution must handle this explicitly.

**12. Similarities and differences** _(analysis)_. Compared with IPFS: both are content-addressed, but Hyphanet adds anonymity and popularity-driven storage, while IPFS has no anonymity and pinning-based persistence. Compared with Tor and I2P: storage-centric rather than streams.

_Open questions:_
- Register Clarke 1999/2001 papers and the Fred protocol docs to upgrade 'protocols' and 'public_disclosure'.
- Compare the rename account with the new Freenet project's account (only one side registered).

## Freenet (formerly Locutus) (`freenet`)

- Kind: system; lifecycle: experimental; last reviewed: 2026-11-24
- Layers: overlay, application
- Topology: peer_to_peer, decentralized
- Resource identification: public_key
- Discovery: out_of_band
- Related entries: `hyphanet`

**1. Origin** _(sourced)_. Developed under the name Locutus from 2019, and renamed "Freenet" in early 2023 by the board of Freenet Project, Inc. According to the Hyphanet account it has different design priorities from the original Freenet.
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "In early 2023, the board of Freenet Project, Inc"
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "decided to rename its new project Locutus to "Freenet.""
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "Locutus began development in 2019, and has different design priorities."

**2. Why it was developed** _(sourced)_. A peer-to-peer platform for applications that no company controls and that need no servers behind them.
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "Freenet is a peer-to-peer platform for apps that no company controls."
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "need no servers behind them"

**3. How it became publicly known** _(sourced)_. Took the Freenet name at the 2023 rename announced by Hyphanet. The project site now promotes end-user apps such as River group chat.
  - [✔ verified] `hyphanet_rename_2023` (Freenet renamed to Hyphanet (26 June 2023)): "decided to rename its new project Locutus to "Freenet.""
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "River, group chat that feels like Signal or WhatsApp with nobody in the middle"

**4. Architecture** _(unverified)_. Described by the project as apps that run on users' peers in a global network. Its contract and state model and its routing weren't checked against the project's whitepaper in this version.

**5. Communication protocols** _(unverified)_. Not documented in this version; the project's whitepaper and manual need registering.

**6. Resource identification** _(unverified)_. Not documented in this version.

**7. Information discovery** _(unverified)_. Not documented in this version.

**8. Public technical documentation** _(sourced)_. The project site links a whitepaper, a manual and a tutorial (titles seen on the landing page; contents not read).
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "Whitepaper"

**9. Relationship to existing infrastructure** _(sourced)_. Runs on users' own computers, peer-to-peer and not on the cloud, according to the project.
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "Your computer becomes part of a global network"
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "run peer-to-peer, not on the cloud"

**10. Distinguishing characteristics** _(sourced)_. An application platform: the site invites developers to build apps with Rust and TypeScript. Hyphanet's account calls it a "not privacy related" project. That is one side's claim and hasn't been corroborated.
  - [✔ verified] `freenet_home` (Freenet (formerly Locutus) home page): "Build apps with familiar tools (Rust, TypeScript)"
  - [✔ verified] `hyphanet_about` (Hyphanet: About): "not privacy related project to Freenet"

**11. Observable limitations** _(analysis)_. Young system with little independent documentation registered. The landing page is promotional. The name collides with 1999-2023 sources about Hyphanet.

**12. Similarities and differences** _(analysis)_. Compared with Hyphanet: shares organisational lineage and name, but differs in goals and design. A classifier must not merge the two entities on name alone.

_Open questions:_
- Register the Freenet whitepaper and manual; fill architecture/protocols/resource_identification/discovery.

## GNUnet (`gnunet`)

- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: overlay, application
- Topology: peer_to_peer, decentralized
- Resource identification: public_key, human_name_registry
- Discovery: dht_lookup, naming_resolution
- Architectural patterns: distributed_hash_table, self_certifying_names
- Related entries: `i2p`, `tor`, `hyphanet`

**1. Origin** _(sourced)_. Maintained by GNUnet e.V. The site's copyright notice runs from 2001, which is weak evidence of the start date. The founding history, and whether GNUnet is an official GNU package, weren't verified in this version (the GNU Project is listed among its hosting supporters).
  - [✔ verified] `gnunet_home` (GNUnet home page): "Copyright © GNUnet e.V. 2001"
  - [✔ verified] `gnunet_about` (GNUnet: About): "The GNU Project"

**2. Why it was developed** _(sourced)_. A Free Software network architecture following a decentralized peer-to-peer paradigm with privacy-preserving cryptographic protocols.
  - [✔ verified] `gnunet_about` (GNUnet: About): "We believe liberal societies need a network architecture that uses the anti-authoritarian decentralized peer-to-peer paradigm and privacy-preserving cryptographic protocols."
  - [✔ verified] `gnunet_about` (GNUnet: About): "The goal of the GNUnet project is to provide a Free Software realization of this ideal."

**3. How it became publicly known** _(sourced)_. The GNU Name System was published as RFC 9498 in November 2023, an Informational RFC from the Independent Submission stream.
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "November 2023 The GNU Name System"
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "Category: Informational"
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "Independent Submission"

**4. Architecture** _(unverified)_. A layered P2P framework (transport, core, DHT, applications). The DHT is commonly identified as R5N. Not quoted from a retrieved source in this version.

**5. Communication protocols** _(sourced)_. GNS is specified as a decentralized, censorship-resistant name resolution protocol.
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "GNS is a decentralized and censorship-resistant domain name resolution protocol that provides a privacy-enhancing alternative to the Domain Name System (DNS) protocols."

**6. Resource identification** _(sourced)_. Names are resolved within zones that have zone keys (a blinded key is derived from a zone key and a label), with zone top-level domains (zTLDs) and the delegation record types PKEY and EDKEY.
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "A blinded zone key is a key derived from a zone key and a label."
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "Zone Top-Level Domain (zTLD)"
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "5.1.1. PKEY 5.1.2. EDKEY"

**7. Information discovery** _(sourced)_. Name resolution through GNS, with DHTs used as remote storage for records.
  - [✔ verified] `rfc9498` (RFC 9498: The GNU Name System): "DHTs as Remote Storage"

**8. Public technical documentation** _(sourced)_. Project handbook and an RFC-published specification for GNS. The GNU Name System is called its most mature component.
  - [✔ verified] `gnunet_about` (GNUnet: About): "start with its most mature component, the GNU Name System"

**9. Relationship to existing infrastructure** _(analysis)_. Runs on Internet hosts. GNS is positioned as an alternative to DNS, not a replacement for IP.

**10. Distinguishing characteristics** _(analysis)_. A whole privacy-oriented networking stack in one framework, with a decentralized naming system published as an Informational RFC (not a standard) that other projects could adopt independently.

**11. Observable limitations** _(analysis)_. The project itself names GNS as its most mature component, which implies other components are less mature. The start date rests only on a copyright notice.

**12. Similarities and differences** _(analysis)_. Compared with I2P: both are full-stack privacy P2P with their own naming, but GNUnet's naming is formally specified in an RFC. Compared with DNS: key-based delegation without a root authority.

_Open questions:_
- Register GNUnet handbook and the R5N paper to upgrade 'architecture'.

## IPFS (`ipfs`)

- Aliases: InterPlanetary File System
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: overlay, application, information_ecosystem
- Topology: peer_to_peer, distributed
- Resource identification: content_hash, public_key
- Discovery: dht_lookup, out_of_band
- Architectural patterns: content_addressing, distributed_hash_table, swarming
- Related entries: `dht`, `p2p`, `hyphanet`, `zeronet`

**1. Origin** _(sourced)_. Described in Juan Benet's arXiv preprint, submitted 14 July 2014.
  - [✔ verified] `ipfs_whitepaper_arxiv` (IPFS - Content Addressed, Versioned, P2P File System (arXiv:1407.3561), abstract page): "Submitted on 14 Jul 2014"
  - [✔ verified] `ipfs_whitepaper_arxiv` (IPFS - Content Addressed, Versioned, P2P File System (arXiv:1407.3561), abstract page): "Versioned, P2P File System, by Juan Benet"

**2. Why it was developed** _(sourced)_. A peer-to-peer distributed file system intended to connect all computing devices with the same system of files.
  - [✔ verified] `ipfs_whitepaper_arxiv` (IPFS - Content Addressed, Versioned, P2P File System (arXiv:1407.3561), abstract page): "The InterPlanetary File System (IPFS) is a peer-to-peer distributed file system that seeks to connect all computing devices with the same system of files."

**3. How it became publicly known** _(sourced)_. Disclosed by public preprint (2014) and open-source implementations with public documentation.
  - [✔ verified] `ipfs_whitepaper_arxiv` (IPFS - Content Addressed, Versioned, P2P File System (arXiv:1407.3561), abstract page): "Submitted on 14 Jul 2014"

**4. Architecture** _(sourced)_. A set of open protocols for addressing, routing and transferring content-addressed data. The DHT, IPFS's version of Kademlia, is the core of content routing, mapping identifiers to providing peers.
  - [✔ verified] `ipfs_docs_what` (IPFS Docs: What is IPFS): "IPFS is a set of open protocols for addressing, routing, and transferring"
  - [✔ verified] `ipfs_docs_dht` (IPFS Docs: Distributed Hash Tables (DHTs)): "IPFS's take on Kademlia"
  - [✔ verified] `ipfs_docs_dht` (IPFS Docs: Distributed Hash Tables (DHTs)): "In IPFS, the DHT is used as the fundamental component of the content routing system"

**5. Communication protocols** _(sourced)_. The Kademlia-derived DHT and IPNS (mutable naming) are quoted here. Bitswap (block exchange), IPLD (data model) and libp2p (networking) are named in the documentation navigation but not quoted in this version.
  - [✔ verified] `ipfs_docs_dht` (IPFS Docs: Distributed Hash Tables (DHTs)): "IPFS's take on Kademlia"
  - [✔ verified] `ipfs_docs_dht` (IPFS Docs: Distributed Hash Tables (DHTs)): "IPNS (InterPlanetary Name System)"

**6. Resource identification** _(sourced)_. Content Identifiers (CIDs) derived from the content's cryptographic hash (sha-256 by default).
  - [✔ verified] `ipfs_docs_cid` (IPFS Docs: Content Identifiers (CIDs)): "CIDs are based on the content's cryptographic hash."
  - [✔ verified] `ipfs_docs_cid` (IPFS Docs: Content Identifiers (CIDs)): "IPFS uses the sha-256 hashing algorithm by default"

**7. Information discovery** _(sourced)_. Provider records in the DHT map a content identifier to peers that advertise they have it.
  - [✔ verified] `ipfs_docs_dht` (IPFS Docs: Distributed Hash Tables (DHTs)): "It maps what the user is looking for to the peer that is storing the matching content."

**8. Public technical documentation** _(sourced)_. Public documentation at docs.ipfs.tech, plus the 2014 preprint.
  - [✔ verified] `ipfs_docs_what` (IPFS Docs: What is IPFS): "What is IPFS"

**9. Relationship to existing infrastructure** _(analysis)_. An overlay on the Internet. HTTP gateways (such as ipfs.io, registered as a candidate source) bridge IPFS content into the Web. How much access goes through gateways rather than native peers isn't measured here.

**10. Distinguishing characteristics** _(sourced)_. Content addressing gives verifiability, since any change in content produces a different CID.
  - [✔ verified] `ipfs_docs_cid` (IPFS Docs: Content Identifiers (CIDs)): "Any difference in the content will produce a different CID."

**11. Observable limitations** _(analysis)_. Content addressing doesn't guarantee availability: content persists only while someone provides it. There's no anonymity, because providers are visible in the DHT. Gateway use re-centralizes access.

**12. Similarities and differences** _(analysis)_. Compared with BitTorrent: similar swarming and DHT ideas, generalised to a file system and linked data. Compared with Hyphanet: content-addressed without anonymity. Compared with the Web: what, not where.

## ZeroNet (`zeronet`)

- Kind: system; lifecycle: unknown; last reviewed: 2026-11-24
- Layers: overlay, application, information_ecosystem
- Topology: peer_to_peer, hybrid
- Resource identification: public_key, human_name_registry
- Discovery: tracker, out_of_band
- Architectural patterns: self_certifying_names, swarming, blockchain_naming
- Related entries: `ipfs`, `p2p`, `hyphanet`

**1. Origin** _(unverified)_. Commonly dated to 2015 and to a single original author. Neither is stated in the retrieved README, and the GitHub repository history couldn't be queried from this environment.

**2. Why it was developed** _(sourced)_. Decentralized websites using Bitcoin cryptography and the BitTorrent network.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "Decentralized websites using Bitcoin crypto and the BitTorrent network"

**3. How it became publicly known** _(analysis)_. Open-source repository and project website. Not investigated further in this version.

**4. Architecture** _(sourced)_. Each visited site is also served by the visitor. Every site has a content.json manifest holding sha512 hashes of all other files and a signature made with the site's private key. When the owner changes the site they sign a new content.json, and peers verify its integrity using the signature.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "Each visited site is also served by you."
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "Every site contains a `content.json` file which holds all other files in a sha512 hash and a signature generated using the site's private key."
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "the peers verify the `content.json` integrity (using the signature)"

**5. Communication protocols** _(sourced)_. Peer discovery through the BitTorrent network, with its own file exchange and TLS-encrypted connections.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "it tries to find peers using the BitTorrent network so it can download the site files"
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "TLS encrypted connections"

**6. Resource identification** _(sourced)_. Sites are addressed by a site address whose private key the site owner holds. Namecoin .bit domains are supported for human-readable names.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "who has the private key for the site address"
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "Namecoin .bit domains support"

**7. Information discovery** _(sourced)_. When visiting a site, the client looks for peers through the BitTorrent network. How site addresses themselves spread wasn't investigated in this version.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "it tries to find peers using the BitTorrent network so it can download the site files"

**8. Public technical documentation** _(sourced)_. The repository README and the project website.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "How does it work?"

**9. Relationship to existing infrastructure** _(sourced)_. Runs a local HTTP server, which users browse with an ordinary browser (127.0.0.1:43110). It reuses Bitcoin cryptography and BitTorrent peer discovery.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "http://127.0.0.1:43110/{zeronet_address}"

**10. Distinguishing characteristics** _(sourced)_. Real-time updated, signed, peer-served websites.
  - [✔ verified] `zeronet_readme` (ZeroNet README (HelloZeroNet/ZeroNet, py3 branch)): "Real-time updated sites"

**11. Observable limitations** _(unverified)_. Maintenance status is unknown. Reports that the original repository is inactive and that forks exist couldn't be checked here (GitHub API blocked from this environment).

**12. Similarities and differences** _(analysis)_. Compared with IPFS: per-site signed manifests and BitTorrent-based discovery, where IPFS has a general content-addressed file system. Compared with Hyphanet: anonymity isn't part of the core design described in the README (its README links an .onion address, but Tor support wasn't verified).

_Open questions:_
- Check maintenance status and forks from an environment with GitHub API access.

## Gopher (`gopher`)

- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: application, information_ecosystem
- Topology: client_server, decentralized
- Resource identification: host_selector, location_url
- Discovery: directory_listing, search_engine
- Architectural patterns: client_server, menu_hierarchy
- Related entries: `www`, `gemini`

**1. Origin** _(sourced)_. Developed at the University of Minnesota. The protocol was documented as RFC 1436 in March 1993.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "University of Minnesota March 1993"

**2. Why it was developed** _(sourced)_. A distributed document search and retrieval protocol.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "The Internet Gopher Protocol (a distributed document search and retrieval protocol)"

**3. How it became publicly known** _(sourced)_. Published as an Informational RFC (not an Internet standard). The 1991 origin date is commonly cited but not verified in this version.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "This memo provides information for the Internet community. It does not specify an Internet standard."

**4. Architecture** _(sourced)_. Client-server: documents reside on many autonomous servers, and client software presents users with a hierarchy of items and directories, much like a file system.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "Documents reside on many autonomous servers on the Internet."
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "Gopher client software presents users with a hierarchy of items and directories much like a file system"

**5. Communication protocols** _(sourced)_. The client connects over TCP and sends a selector (a line of text). The server responds and closes the connection, and retains no state. Servers should listen on IANA-assigned port 70.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "connecting to a server and sending the server a selector (a line of text, which may be empty)"
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "No state is retained by the server."
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "Gopher servers should listen on port 70 (port 70 is assigned to Internet Gopher by IANA)."

**6. Resource identification** _(sourced)_. An item is reached by sending its selector string to a server, and clients display item types (e.g. directories compared with files). RFC 4266 later defined a gopher URI scheme.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "connecting to a server and sending the server a selector (a line of text, which may be empty)"
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "item types could be denoted by other text tags or by icons"
  - [✔ verified] `rfc4266` (RFC 4266: The gopher URI Scheme): "The gopher URI Scheme"

**7. Information discovery** _(analysis)_. Browsing menus and links between servers. Gopher-specific search services existed (commonly cited: Veronica), but they're not verified in this version.

**8. Public technical documentation** _(sourced)_. RFC 1436 and RFC 4266.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "The Internet Gopher Protocol"

**9. Relationship to existing infrastructure** _(sourced)_. An application protocol over TCP on the Internet.
  - [✔ verified] `rfc1436` (RFC 1436: The Internet Gopher Protocol): "This protocol assumes a reliable data stream; TCP is assumed."

**10. Distinguishing characteristics** _(analysis)_. Strict menu-and-document model with typed items. Easy to implement and to index, but it lacks inline hypertext. Whether a Gopherspace community is still active, and how large it is, is not measured in this version.

**11. Observable limitations** _(analysis)_. No encryption in the base protocol and no inline links. Abyss can't reach native Gopher (port 70) from the current cloud environment (outbound port closed), so live Gopher ingestion is BLOCKED here.

**12. Similarities and differences** _(sourced)_. Gemini explicitly positions itself as an incremental improvement over Gopher rather than a stripped-down HTTP.
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "It can be thought of as an incremental improvement over Gopher [RFC1436] rather than a stripped down HTTP"

## Gemini (`gemini`)

- Aliases: Project Gemini, Geminispace
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: application, information_ecosystem
- Topology: client_server, decentralized
- Resource identification: location_url
- Discovery: hyperlinks, search_engine, out_of_band
- Architectural patterns: client_server, hypertext, trust_on_first_use
- Related entries: `gopher`, `www`

**1. Origin** _(sourced)_. Project Gemini started in June 2019.
  - [✔ verified] `gemini_faq` (Project Gemini FAQ): "Project Gemini started in June 2019."

**2. Why it was developed** _(sourced)_. To coexist alongside Gopher and the Web as one more option, explicitly not to replace them.
  - [✔ verified] `gemini_faq` (Project Gemini FAQ): "Gemini is not intended to replace either Gopher or the web, but to co-exist peacefully alongside them"

**3. How it became publicly known** _(analysis)_. Developed in public, with its specification and FAQ published by the project.

**4. Architecture** _(sourced)_. A single request, single response client-server protocol over TLS.
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "with a simple request and response transaction"

**5. Communication protocols** _(sourced)_. The Gemini protocol on TCP port 1965 with mandatory TLS. Clients are strongly recommended to use Trust-On-First-Use certificate pinning.
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "It runs over TCP [STD7] port 1965 with encryption provided by TLS [RFC8446]"
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "Clients are strongly RECOMMENDED to use a Trust on First Use or "TOFU" certificate-pinning system"

**6. Resource identification** _(sourced)_. gemini:// URIs (location-based).
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "gemini://example.net/search?hello"

**7. Information discovery** _(analysis)_. Links in gemtext documents, community aggregators and Gemini-native search engines. Total size is unmeasured by Abyss.

**8. Public technical documentation** _(sourced)_. Specification and FAQ at geminiprotocol.net (also served natively over Gemini).
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "This document specifies the Gemini protocol for file transfer."

**9. Relationship to existing infrastructure** _(analysis)_. An application protocol over TCP/TLS on the Internet. It uses DNS hostnames, and TOFU avoids dependence on the CA system.

**10. Distinguishing characteristics** _(sourced)_. "Geminispace" names the total collection of content served over Gemini, by analogy with Gopherspace.
  - [✔ verified] `gemini_faq` (Project Gemini FAQ): ""Geminispace" is simply the total collection of every single file that is served via the Gemini protocol."

**11. Observable limitations** _(analysis)_. Deliberately minimal (no inline media or scripting). Native port 1965 is closed in the current cloud environment, so the Phase 0 citations came from the project's HTTPS mirror and native ingestion is BLOCKED here.

**12. Similarities and differences** _(sourced)_. Positioned between Gopher and the Web, as an improvement over Gopher rather than a stripped-down HTTP.
  - [✔ verified] `gemini_spec` (Gemini network protocol specification): "It can be thought of as an incremental improvement over Gopher [RFC1436] rather than a stripped down HTTP"

## Usenet (`usenet`)

- Aliases: Netnews
- Kind: system; lifecycle: operational; last reviewed: 2026-11-24
- Layers: application, information_ecosystem
- Topology: federated, decentralized
- Resource identification: message_id, topic_hierarchy
- Discovery: flooding, directory_listing
- Architectural patterns: store_and_forward_flooding, federation
- Related entries: `federated`, `arpanet`, `www`

**1. Origin** _(sourced)_. Grew out of the UNIX ecosystem, built on UNIX's built-in UUCP communication. The commonly cited 1979-1980 Duke University origin is unverified in this version.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "spawned USENET, based on UNIX' built-in UUCP communication protocols"

**2. Why it was developed** _(sourced)_. Distributing news articles organised into newsgroups, so that each reader can see all articles posted to the newsgroups they take part in. Copies propagate by flooding among participating servers.
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): "will be able to see all articles posted to each newsgroup in which he participates"
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): "These protocols most commonly use a flooding algorithm that propagates copies throughout a network of participating servers."

**3. How it became publicly known** _(sourced)_. The message format was published as RFC 850 (June 1983) and RFC 1036 (December 1987), and NNTP as RFC 977 (February 1986).
  - [✔ verified] `rfc850` (RFC 850: Standard for Interchange of USENET Messages): "June 1983 Standard for Interchange of USENET Messages"
  - [✔ verified] `rfc1036` (RFC 1036: Standard for Interchange of USENET Messages): "December 1987 Standard for Interchange of USENET Messages"
  - [✔ verified] `rfc977` (RFC 977: Network News Transfer Protocol): "February 1986 Network News Transfer Protocol"

**4. Architecture** _(sourced)_. A federation of news servers. Articles flood between peered servers, usually with one stored copy per server served to local readers. Usenet is one particular public network built on the Netnews protocols.
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): "Typically, only one copy is stored per server"
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): ""Usenet" is a particular worldwide, publicly accessible network based on the Netnews protocols."

**5. Communication protocols** _(sourced)_. UUCP historically, then NNTP (RFC 977, superseded by RFC 3977).
  - [✔ verified] `rfc977` (RFC 977: Network News Transfer Protocol): "NNTP specifies a protocol for the distribution, inquiry, retrieval, and posting of news articles"
  - [✔ verified] `rfc3977` (RFC 3977: Network News Transfer Protocol (NNTP)): "Network News Transfer Protocol (NNTP)"

**6. Resource identification** _(sourced)_. Each article has a Message-ID, a unique identifier that may not be reused during the lifetime of an earlier message. Articles are posted to named newsgroups (e.g. news.announce).
  - [✔ verified] `rfc1036` (RFC 1036: Standard for Interchange of USENET Messages): "The "Message-ID" line gives the message a unique identifier."
  - [✔ verified] `rfc1036` (RFC 1036: Standard for Interchange of USENET Messages): "Newsgroups: news.announce"

**7. Information discovery** _(analysis)_. Subscribing to newsgroups in the hierarchy, with articles arriving by flooding. Archives (third-party) provide search over historical posts.

**8. Public technical documentation** _(sourced)_. RFCs 850, 1036, 977, 3977 and 5537.
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): "Netnews Architecture and Protocols"

**9. Relationship to existing infrastructure** _(sourced)_. Built on UNIX's UUCP communication protocols. NNTP later carried news as a reliable stream among the ARPA- Internet community. Netnews protocols are also used in deployments other than Usenet.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "spawned USENET, based on UNIX' built-in UUCP communication protocols"
  - [✔ verified] `rfc977` (RFC 977: Network News Transfer Protocol): "using a reliable stream-based transmission of news among the ARPA-Internet community"
  - [✔ verified] `rfc5537` (RFC 5537: Netnews Architecture and Protocols): "there are deployments of the Netnews protocols other than Usenet"

**10. Distinguishing characteristics** _(analysis)_. An early large-scale federated information ecosystem with no central server. Content is replicated by flooding, and a "Path" header records propagation.

**11. Observable limitations** _(analysis)_. Server retention limits mean history is lost unless archived. Spam and abuse controls rely on operator cooperation. Native NNTP (port 119) is closed in the current cloud environment.

**12. Similarities and differences** _(analysis)_. Shares the federation pattern with email, which is older (see federated.origin), and with later systems such as ActivityPub and Matrix. Usenet floods articles to all peered servers, while ActivityPub delivers to subscribers. The Web's 1991 description was posted to a Usenet group (see www.public_disclosure).

## Distributed hash tables (`dht`)

- Kind: pattern; lifecycle: mixed; last reviewed: 2026-11-24
- Layers: overlay
- Topology: distributed, peer_to_peer
- Resource identification: content_hash, public_key
- Discovery: dht_lookup
- Architectural patterns: distributed_hash_table
- Examples: Chord, Kademlia, BitTorrent Mainline DHT (BEP 5), IPFS DHT, I2P netDb
- Related entries: `p2p`, `ipfs`, `i2p`, `gnunet`

**1. Origin** _(sourced)_. Structured lookup overlays were published by 2001 (Chord at SIGCOMM 2001). Kademlia (IPTPS 2002) uses an XOR distance metric. Its PDF couldn't be machine-checked, but BEP 5 states the XOR metric for Kademlia.
  - [✔ verified] `chord_sigcomm2001` (Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications (SIGCOMM 2001)): "SIGCOMM'01, August 27-31, 2001, San Diego, California, USA."
  - [⚠ text unextractable] `kademlia_iptps2002` (Kademlia: A Peer-to-peer Information System Based on the XOR Metric (IPTPS 2002), authors' copy): "Kademlia: A Peer-to-peer Information System Based on the XOR Metric"
  - [✔ verified] `bep5` (BEP 5: DHT Protocol (BitTorrent Mainline DHT)): "In Kademlia, the distance metric is XOR and the result is interpreted as an unsigned integer."

**2. Why it was developed** _(sourced)_. To efficiently locate the node that stores a particular data item in a peer-to-peer system.
  - [✔ verified] `chord_sigcomm2001` (Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications (SIGCOMM 2001)): "A fundamental problem that confronts peer-to-peer applications is to efficiently locate the node that stores a particular data item."

**3. How it became publicly known** _(sourced)_. Disclosed through peer-reviewed research papers.
  - [✔ verified] `chord_sigcomm2001` (Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications (SIGCOMM 2001)): "Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications"

**4. Architecture** _(sourced)_. Nodes and keys share an identifier space, and each key maps onto a responsible node. Chord supports exactly that one operation.
  - [✔ verified] `chord_sigcomm2001` (Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications (SIGCOMM 2001)): "Chord provides support for just one operation: given a key, it maps the key onto a node."

**5. Communication protocols** _(sourced)_. Instance-specific. BitTorrent's Mainline DHT (BEP 5) uses Kademlia with XOR distance.
  - [✔ verified] `bep5` (BEP 5: DHT Protocol (BitTorrent Mainline DHT)): "In Kademlia, the distance metric is XOR and the result is interpreted as an unsigned integer."

**6. Resource identification** _(analysis)_. Keys are fixed-length identifiers, typically hashes of content or of public keys.

**7. Information discovery** _(analysis)_. Iterative or recursive lookup converging on the nodes closest to a key in the identifier metric.

**8. Public technical documentation** _(sourced)_. Research papers plus protocol specifications of deployed instances (e.g. BEP 5).
  - [✔ verified] `bep5` (BEP 5: DHT Protocol (BitTorrent Mainline DHT)): "DHT Protocol"

**9. Relationship to existing infrastructure** _(analysis)_. An overlay pattern used as a component by many systems, not a standalone information ecosystem.

**10. Distinguishing characteristics** _(analysis)_. Logarithmic lookup without central index, using an identifier-space metric and routing tables.

**11. Observable limitations** _(analysis)_. Vulnerable to Sybil and eclipse attacks without countermeasures, and churn costs maintenance traffic. For recognition, a DHT is a component signature and doesn't identify a single system.

**12. Similarities and differences** _(analysis)_. Compared with flooding (Usenet): targeted lookup rather than full replication. Compared with a central tracker: no single point of failure.

## Peer-to-peer architectures (`p2p`)

- Kind: pattern; lifecycle: mixed; last reviewed: 2026-11-24
- Layers: overlay, application
- Topology: peer_to_peer, hybrid, distributed
- Resource identification: content_hash, location_url
- Discovery: tracker, dht_lookup, out_of_band
- Architectural patterns: swarming, distributed_hash_table
- Examples: BitTorrent, Bitcoin, IPFS, Hyphanet
- Related entries: `dht`, `ipfs`, `zeronet`, `hyphanet`

**1. Origin** _(analysis)_. A design paradigm rather than a single invention. RFC 5694 surveys its definition and taxonomies (see documentation). Historical first instances aren't asserted in this version.

**2. Why it was developed** _(sourced)_. To share resources directly between participants instead of through a central server or intermediary.
  - [✔ verified] `bep3` (BEP 3: The BitTorrent Protocol Specification): "when multiple downloads of the same file happen concurrently, the downloaders upload to each other"
  - [✔ verified] `bitcoin_whitepaper` (Bitcoin: A Peer-to-Peer Electronic Cash System): "A purely peer-to-peer version of electronic cash would allow online payments to be sent directly from one party to another without going through a financial institution."

**3. How it became publicly known** _(sourced)_. Through specifications, whitepapers and IAB/IETF surveys.
  - [✔ verified] `rfc5694` (RFC 5694: Peer-to-Peer (P2P) Architecture: Definition, Taxonomies, Examples, and Applicability): "In this document, we provide a survey of P2P (Peer-to-Peer) systems."

**4. Architecture** _(sourced)_. RFC 5694 provides a definition and several taxonomies of P2P systems, and discusses when to design an application with a P2P paradigm or a different model such as client-server.
  - [✔ verified] `rfc5694` (RFC 5694: Peer-to-Peer (P2P) Architecture: Definition, Taxonomies, Examples, and Applicability): "The survey includes a definition and several taxonomies of P2P systems."
  - [✔ verified] `rfc5694` (RFC 5694: Peer-to-Peer (P2P) Architecture: Definition, Taxonomies, Examples, and Applicability): "using a P2P paradigm or a different model (e.g., a client-server paradigm)"

**5. Communication protocols** _(sourced)_. Instance-specific. BitTorrent combines a tracker (central coordinator) with peer swarming, which makes it a hybrid design.
  - [✔ verified] `bep3` (BEP 3: The BitTorrent Protocol Specification): "A BitTorrent tracker"

**6. Resource identification** _(sourced)_. Instance-specific. BitTorrent identifies content by URL and is designed to integrate with the web.
  - [✔ verified] `bep3` (BEP 3: The BitTorrent Protocol Specification): "It identifies content by URL and is designed to integrate seamlessly with the web."

**7. Information discovery** _(analysis)_. Trackers, DHTs, peer exchange, or out-of-band sharing of identifiers.

**8. Public technical documentation** _(sourced)_. RFC 5694 plus instance specifications (BEPs, whitepapers).
  - [✔ verified] `rfc5694` (RFC 5694: Peer-to-Peer (P2P) Architecture: Definition, Taxonomies, Examples, and Applicability): "Peer-to-Peer (P2P) Architecture: Definition, Taxonomies, Examples, and Applicability"

**9. Relationship to existing infrastructure** _(analysis)_. Usually an overlay on the Internet. Some instances bootstrap through web servers (trackers, metainfo files).

**10. Distinguishing characteristics** _(analysis)_. Participants are both consumers and providers, so capacity scales with participation.

**11. Observable limitations** _(analysis)_. NAT traversal, free-riding, Sybil attacks and legal misuse. "P2P" is too broad to be a useful recognition label alone, so it should be a parent family with sub-families.

**12. Similarities and differences** _(analysis)_. The parent pattern of the DHT, swarming and friend-to-friend designs in this taxonomy. Federation differs in that servers stay distinct from clients.

## Mesh networks (`mesh`)

- Kind: pattern; lifecycle: mixed; last reviewed: 2026-11-24
- Layers: physical, link, network
- Topology: distributed, decentralized, peer_to_peer
- Resource identification: network_address, public_key
- Discovery: routing_announcements, manual_peering
- Architectural patterns: mesh_routing
- Examples: OLSR, Babel, B.A.T.M.A.N. (batman-adv), Meshtastic, Reticulum
- Related entries: `experimental_protocols`, `private_intranet`

**1. Origin** _(sourced)_. IETF MANET work on routing for mobile ad hoc networks was documented in RFC 2501 (January 1999), and OLSR was published as an Experimental RFC in October 2003.
  - [✔ verified] `rfc2501` (RFC 2501: Mobile Ad hoc Networking (MANET): Routing Protocol Performance Issues and Evaluation Considerations): "January 1999 Mobile Ad hoc Networking"
  - [✔ verified] `rfc3626` (RFC 3626: Optimized Link State Routing Protocol (OLSR)): "October 2003 Optimized Link State Routing Protocol (OLSR)"
  - [✔ verified] `rfc3626` (RFC 3626: Optimized Link State Routing Protocol (OLSR)): "Category: Experimental"

**2. Why it was developed** _(sourced)_. Communication where infrastructure is missing or unreliable. For example, Meshtastic uses inexpensive LoRa radios for long-range off-grid communication.
  - [✔ verified] `meshtastic_docs` (Meshtastic documentation: Introduction): "radios as a long range off-grid communication platform in areas without existing or reliable communications infrastructure"

**3. How it became publicly known** _(analysis)_. Through IETF RFCs and open-source community projects.

**4. Architecture** _(sourced)_. batman-adv implements the B.A.T.M.A.N. routing protocol as a Linux kernel module at layer 2. OLSR is a routing protocol for mobile ad hoc networks.
  - [✔ verified] `batman_adv_docs` (batman-adv documentation overview (Open Mesh)): "is an implementation of the B.A.T.M.A.N. routing protocol in form of a Linux kernel module operating on layer 2"
  - [✔ verified] `rfc3626` (RFC 3626: Optimized Link State Routing Protocol (OLSR)): "This document describes the Optimized Link State Routing (OLSR) protocol for mobile ad hoc networks."

**5. Communication protocols** _(sourced)_. OLSR (link-state, using multipoint relays) and Babel (loop-avoiding distance-vector, for wired and wireless mesh networks).
  - [✔ verified] `rfc3626` (RFC 3626: Optimized Link State Routing Protocol (OLSR)): "The key concept used in the protocol is that of multipoint relays (MPRs)."
  - [✔ verified] `rfc8966` (RFC 8966: The Babel Routing Protocol): "Babel is a loop-avoiding, distance-vector routing protocol that is robust and efficient both in ordinary wired networks and in wireless mesh networks."

**6. Resource identification** _(unverified)_. Usually IP addresses. Some stacks (Reticulum, Yggdrasil) are reported to derive addresses from public keys. Neither claim was checked against a retrieved source in this version.

**7. Information discovery** _(analysis)_. Neighbour discovery and routing announcements; community maps for physical nodes.

**8. Public technical documentation** _(sourced)_. RFCs for routing protocols and project documentation for community stacks.
  - [✔ verified] `reticulum_home` (Reticulum Network home page): "Reticulum is the cryptography-based networking stack for building local and wide-area networks with readily available hardware."

**9. Relationship to existing infrastructure** _(analysis)_. Can be fully independent of the Internet (own radios) or bridge to it. It is one of the few families in this taxonomy that can include its own physical layer (ARPANET also had its own switching nodes).

**10. Distinguishing characteristics** _(sourced)_. Some stacks target very poor links. Reticulum, for example, is designed to keep operating with very high latency and extremely low bandwidth.
  - [✔ verified] `reticulum_home` (Reticulum Network home page): "Reticulum can continue to operate even in adverse conditions with very high latency and extremely low bandwidth."

**11. Observable limitations** _(analysis)_. Observable only locally (radio range) or through published maps. Remote discovery of a radio mesh without any Internet presence is not possible for Abyss, which is a fundamental observability limit.

**12. Similarities and differences** _(analysis)_. Compared with overlays (Tor, Yggdrasil): a mesh can own the physical and link layers, where overlays reuse the Internet. Yggdrasil targets both.

## Federated information systems (`federated`)

- Kind: pattern; lifecycle: mixed; last reviewed: 2026-11-24
- Layers: application, information_ecosystem
- Topology: federated, decentralized
- Resource identification: user_at_domain, location_url, message_id
- Discovery: federation_protocol, naming_resolution, hyperlinks
- Architectural patterns: federation
- Examples: Email (SMTP), XMPP, Usenet, Matrix, ActivityPub (fediverse)
- Related entries: `usenet`, `www`

**1. Origin** _(sourced)_. Electronic mail was introduced on the ARPANET in 1972, and Netnews (Usenet) message standards were published in 1983. A recent federation standard is ActivityPub, a W3C Recommendation dated 23 January 2018.
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "It was also in 1972 that the initial"
  - [✔ verified] `isoc_brief_history` (A Brief History of the Internet): "application, electronic mail, was introduced"
  - [✔ verified] `rfc850` (RFC 850: Standard for Interchange of USENET Messages): "June 1983 Standard for Interchange of USENET Messages"
  - [✔ verified] `w3c_activitypub` (ActivityPub, W3C Recommendation): "W3C Recommendation 23 January 2018"

**2. Why it was developed** _(sourced)_. Decentralized communication across independently operated servers with no single point of control.
  - [✔ verified] `matrix_spec` (Matrix Specification (latest)): "over a global open federation of servers with no single point of control"

**3. How it became publicly known** _(sourced)_. Through open standards bodies (IETF, W3C) and public specifications.
  - [✔ verified] `w3c_activitypub` (ActivityPub, W3C Recommendation): "W3C Recommendation 23 January 2018"

**4. Architecture** _(sourced)_. ActivityPub has two layers: a server-to-server federation protocol and a client-to-server protocol.
  - [✔ verified] `w3c_activitypub` (ActivityPub, W3C Recommendation): "A server to server federation protocol (so decentralized websites can share information)"
  - [✔ verified] `w3c_activitypub` (ActivityPub, W3C Recommendation): "A client to server protocol"

**5. Communication protocols** _(sourced)_. SMTP (email transport), XMPP (XML streams), ActivityPub (ActivityStreams 2.0) and the Matrix APIs.
  - [✔ verified] `rfc5321` (RFC 5321: Simple Mail Transfer Protocol): "This document is a specification of the basic protocol for Internet electronic mail transport."
  - [✔ verified] `rfc6120` (RFC 6120: Extensible Messaging and Presence Protocol (XMPP): Core): "The Extensible Messaging and Presence Protocol (XMPP) is an application profile of the Extensible Markup Language (XML)"
  - [✔ verified] `w3c_activitypub` (ActivityPub, W3C Recommendation): "The ActivityPub protocol is a decentralized social networking protocol based upon the [ActivityStreams] 2.0 data format."

**6. Resource identification** _(analysis)_. user@domain identifiers (email, XMPP JIDs, fediverse handles) and HTTP URIs for objects (ActivityPub).

**7. Information discovery** _(analysis)_. Following and subscriptions, server-to-server delivery, DNS for server location, and per-server or relay-based search. No global index exists by design.

**8. Public technical documentation** _(sourced)_. IETF RFCs, W3C Recommendations and the Matrix specification.
  - [✔ verified] `matrix_spec` (Matrix Specification (latest)): "Matrix defines a set of open APIs for decentralised communication"

**9. Relationship to existing infrastructure** _(analysis)_. An application layer over the Internet and DNS. Each server is an ordinary Internet host.

**10. Distinguishing characteristics** _(analysis)_. Servers are distinct from clients (unlike P2P), but no single server controls the network (unlike centralized services).

**11. Observable limitations** _(analysis)_. Content visibility depends on which servers federate with which. There's no complete public view, so "absent from search" is common and is not evidence of hiddenness.

**12. Similarities and differences** _(analysis)_. Usenet floods everything to all peers, while ActivityPub and Matrix deliver to subscribers. Email is an early, widely deployed instance (see origin).

## Experimental networking architectures (`experimental_protocols`)

- Kind: category; lifecycle: experimental; last reviewed: 2026-11-24
- Layers: network, overlay
- Topology: distributed, decentralized
- Resource identification: name_prefix, public_key, network_address
- Discovery: routing_announcements, manual_peering
- Architectural patterns: information_centric_networking, path_aware_networking, self_certifying_names
- Examples: Named Data Networking (NDN), SCION, Yggdrasil, Reticulum
- Related entries: `mesh`, `ipfs`

**1. Origin** _(sourced)_. A heterogeneous category. Example: the NDN project launched with NSF funding in September 2010 under the NSF Future Internet Architecture Program.
  - [✔ verified] `ndn_project` (Named Data Networking: Project Overview): "The NDN project was launched with National Science Foundation funding in September 2010 as one of the four projects under NSF's Future Internet Architecture Program."

**2. Why it was developed** _(sourced)_. To explore alternatives to current Internet routing and addressing. Example: Yggdrasil aims to be a decentralised alternative to structured routing protocols.
  - [✔ verified] `yggdrasil_home` (Yggdrasil Network home page): "It is designed to be a future-proof and decentralised alternative to the structured routing protocols commonly used today on the Internet"

**3. How it became publicly known** _(analysis)_. Research programmes, papers, IETF drafts and open-source repositories.

**4. Architecture** _(sourced)_. Varies by system. Yggdrasil is an experimental compact routing scheme for end-to-end encrypted IPv6 networking, and SCION describes itself as a more secure and reliable Internet. The NDN and SCION architectures aren't quoted in this version (see open questions).
  - [✔ verified] `yggdrasil_home` (Yggdrasil Network home page): "Yggdrasil is a new experimental compact routing scheme."
  - [✔ verified] `yggdrasil_home` (Yggdrasil Network home page): "End-to-end encrypted IPv6 networking"
  - [✔ verified] `scion_home` (SCION home page): "SCION, a more secure and reliable Internet"

**5. Communication protocols** _(unverified)_. Instance-specific: NDN Interest/Data packets, SCION path construction and Yggdrasil routing. None of these were quoted from a retrieved source in this version.

**6. Resource identification** _(unverified)_. Reported: named-data prefixes (NDN), key-derived IPv6 addresses (Yggdrasil) and conventional addresses with path information (SCION). Not checked against retrieved sources in this version.

**7. Information discovery** _(analysis)_. Routing announcements and manual peering. Public peer lists exist for some overlays.

**8. Public technical documentation** _(sourced)_. Project sites and research publications.
  - [✔ verified] `ndn_project` (Named Data Networking: Project Overview): "Named Data Networking"

**9. Relationship to existing infrastructure** _(analysis)_. Mostly deployed as overlays or testbeds on the Internet, although some target eventual replacement of current layers.

**10. Distinguishing characteristics** _(analysis)_. The category exists because these systems redefine the network layer's identity or routing model, which makes them prime test cases for "unknown architecture" recognition.

**11. Observable limitations** _(analysis)_. The category is defined by being non-mainstream, which isn't an architectural property. For recognition benchmarks, each instance should be its own family or held-out family, not lumped together.

**12. Similarities and differences** _(analysis)_. NDN and IPFS both name data rather than hosts, NDN at the network layer and IPFS as an overlay. Yggdrasil shares goals with mesh networks.

_Open questions:_
- Register NDN and SCION architecture specifications to source the architecture, protocols and resource identification facets.

## Private intranet architectures (`private_intranet`)

- Kind: pattern; lifecycle: mixed; last reviewed: 2026-11-24
- Layers: network, transport, application
- Topology: centralized, hierarchical, client_server
- Resource identification: network_address, location_url, human_name_registry
- Discovery: directory_listing, naming_resolution
- Architectural patterns: private_addressing, tunneling, zero_trust
- Examples: RFC 1918 private addressing, BGP/MPLS VPNs, WireGuard tunnels, zero-trust architectures
- Related entries: `arpanet`, `mesh`, `federated`

**1. Origin** _(sourced)_. Private address space was formalised by RFC 1918 (BCP, February 1996).
  - [✔ verified] `rfc1918` (RFC 1918: Address Allocation for Private Internets): "February 1996 Address Allocation for Private Internets"

**2. Why it was developed** _(sourced)_. To build networks for an organisation's own hosts that aren't routed on the public Internet.
  - [✔ verified] `rfc1918` (RFC 1918: Address Allocation for Private Internets): "has reserved the following three blocks of the IP address space for private internets"

**3. How it became publicly known** _(analysis)_. The architecture is public (RFCs, NIST). Specific intranets are private by definition, and Abyss must not attempt to discover them without authorisation.

**4. Architecture** _(sourced)_. Private addressing behind gateways. Provider VPNs (BGP/MPLS) and encrypted tunnels (WireGuard) extend private networks across public infrastructure. Zero-trust architectures remove implicit trust based on location.
  - [✔ verified] `rfc4364` (RFC 4364: BGP/MPLS IP Virtual Private Networks (VPNs)): "This document describes a method by which a Service Provider may use an IP backbone to provide IP Virtual Private Networks (VPNs) for its customers."
  - [✔ verified] `wireguard_paper` (WireGuard: Next Generation Kernel Network Tunnel (whitepaper, draft revision)): "WireGuard is a secure network tunnel, operating at layer 3"
  - [✔ verified] `nist_sp800_207` (NIST SP 800-207: Zero Trust Architecture): "Zero trust assumes there is no implicit trust granted to assets or user accounts based solely on their physical or network location"

**5. Communication protocols** _(sourced)_. Standard IP stacks plus tunnelling protocols. WireGuard's key exchange is based on Noise IK.
  - [✔ verified] `wireguard_paper` (WireGuard: Next Generation Kernel Network Tunnel (whitepaper, draft revision)): "It uses a single round trip key exchange, based on NoiseIK"

**6. Resource identification** _(sourced)_. RFC 1918 reserves three blocks for private internets: 10/8, 172.16/12 and 192.168/16.
  - [✔ verified] `rfc1918` (RFC 1918: Address Allocation for Private Internets): "10.0.0.0 - 10.255.255.255 (10/8 prefix)"
  - [✔ verified] `rfc1918` (RFC 1918: Address Allocation for Private Internets): "172.16.0.0 - 172.31.255.255 (172.16/12 prefix)"
  - [✔ verified] `rfc1918` (RFC 1918: Address Allocation for Private Internets): "192.168.0.0 - 192.168.255.255 (192.168/16 prefix)"

**7. Information discovery** _(analysis)_. Internal directories, internal DNS and search. They aren't visible from outside, which is why they're out of scope without authorisation.

**8. Public technical documentation** _(sourced)_. RFCs and NIST guidance.
  - [✔ verified] `nist_sp800_207` (NIST SP 800-207: Zero Trust Architecture): "NIST Special Publication 800-207 Zero Trust Architecture"

**9. Relationship to existing infrastructure** _(sourced)_. Overlaid on or carved out of public infrastructure. Zero trust moves defences from network perimeters to resources.
  - [✔ verified] `nist_sp800_207` (NIST SP 800-207: Zero Trust Architecture): "move defenses from static, network-based perimeters to focus on users, assets, and resources"

**10. Distinguishing characteristics** _(analysis)_. Defined by access control and non-routability, not by a novel information model.

**11. Observable limitations** _(analysis)_. Only owner-authorised intranets (OWNER_AUTHORIZED sources) or lab networks (LAB_OWNED) may be studied. Absence from public view is the designed behaviour, not an anomaly.

**12. Similarities and differences** _(analysis)_. The architectural opposite of public federated and P2P ecosystems, because membership is closed. It shares tunnelling with overlays like Tor and Yggdrasil.

## Controlled vocabulary

### Layers

| term | definition |
|---|---|
| `physical` | Physical media and radio links (fibre, copper, Wi-Fi radio, LoRa). |
| `link` | Link-layer framing and local delivery, including layer-2 mesh routing. |
| `network` | Internetworking, addressing and routing (IP, BGP, early ARPANET host-IMP networking). |
| `transport` | End-to-end transport (TCP, UDP, QUIC). |
| `overlay` | A logical network formed by end hosts on top of an existing network (onion routing, DHTs, overlay IPv6). |
| `application` | Application protocol and data formats (HTTP, Gopher, Gemini, NNTP, SMTP, ActivityPub). |
| `information_ecosystem` | The content, naming conventions, communities and discovery practices that grow around a system. |

### Topology

| term | definition |
|---|---|
| `centralized` | A single operator or server is required for core function. |
| `client_server` | Clients request resources from servers that hold them. |
| `hierarchical` | Tree-structured delegation (e.g. naming or newsgroup hierarchies). |
| `decentralized` | Many independent operators, with no single point of control for the whole. |
| `distributed` | Function spread across many nodes that cooperate algorithmically. |
| `federated` | Independent servers interoperate through a common server-to-server protocol. |
| `peer_to_peer` | Participants act as both clients and servers. |
| `friend_to_friend` | Peers connect only to explicitly trusted peers. |
| `hybrid` | Combines a central component with distributed operation (e.g. a tracker plus a P2P swarm). |

### Resource identification

| term | definition |
|---|---|
| `location_url` | A URL naming a host and a path; identifies where, not what. |
| `host_selector` | Host, port and an opaque selector string (Gopher). |
| `content_hash` | Identifier derived from a cryptographic hash of the content. |
| `public_key` | Identifier derived from a public key (self-certifying address or name). |
| `network_address` | Numeric network address (ARPANET host numbers, IPv4/IPv6 addresses). |
| `message_id` | A globally unique message identifier. |
| `topic_hierarchy` | Hierarchical topic names (e.g. newsgroup names). |
| `user_at_domain` | Account identifiers scoped to a server's domain (user@host). |
| `name_prefix` | Hierarchical names for data, routed by prefix. |
| `human_name_registry` | Human-readable names resolved through a naming system or registry. |

### Discovery

| term | definition |
|---|---|
| `hyperlinks` | Following links embedded in documents. |
| `search_engine` | Crawler-built indexes queried by users. |
| `directory_listing` | Curated directories or menus. |
| `consensus_directory` | A signed directory of network nodes distributed to clients. |
| `dht_lookup` | Iterative lookup in a distributed hash table. |
| `flooding` | Propagating copies of items to all participating peers or servers. |
| `tracker` | A central coordinator that introduces peers to each other. |
| `out_of_band` | Addresses or keys shared outside the system (word of mouth, other websites). |
| `manual_peering` | Operators configure peer links by hand. |
| `routing_announcements` | Routing protocol advertisements between nodes. |
| `federation_protocol` | Server-to-server delivery and subscription. |
| `naming_resolution` | Resolving names through a naming system. |

### Architectural patterns

| term | definition |
|---|---|
| `packet_switching` | Data split into independently routed packets. |
| `client_server` | Request/response between clients and servers. |
| `hypertext` | Documents with embedded links to other documents. |
| `menu_hierarchy` | Navigation through hierarchical menus of items. |
| `onion_routing` | Layered encryption over a multi-hop circuit; each relay removes one layer. |
| `garlic_routing` | Bundling several encrypted messages into one layered message over unidirectional tunnels. |
| `distributed_hash_table` | Key-to-node mapping spread across participants. |
| `content_addressing` | Retrieval by identifier derived from the content itself. |
| `self_certifying_names` | Names that embed or derive from a key, so possession of the name authenticates the holder. |
| `store_and_forward_flooding` | Servers store items and forward copies to neighbours. |
| `federation` | Interoperation of independently operated servers. |
| `swarming` | Many downloaders exchange pieces of the same content with each other. |
| `mesh_routing` | Nodes route for each other over multi-hop links without fixed infrastructure. |
| `small_world_routing` | Greedy routing that exploits a small-world graph of peer connections. |
| `blockchain_naming` | Names registered on a blockchain (e.g. Namecoin .bit). |
| `trust_on_first_use` | Accept and pin a peer's key or certificate on first contact. |
| `private_addressing` | Address space reserved for networks not routed on the public Internet. |
| `tunneling` | Encapsulating one network's traffic inside another's. |
| `zero_trust` | No implicit trust based on network location. |
| `information_centric_networking` | The network routes requests for named data rather than to host addresses. |
| `path_aware_networking` | End hosts can see and choose inter-domain paths. |
