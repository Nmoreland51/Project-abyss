"""Versioned, machine-readable network taxonomy: schema, loading and cross-validation (R03 foundation).

Every entry documents the twelve facets the owner's directive requires (section 3). Each facet
states its epistemic basis: ``sourced`` facets must carry verbatim quotations from registered
reference documents, and ``analysis`` and ``unverified`` facets are labelled as such so that
synthesis is never presented as sourced fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator, model_validator

from ..core.contracts import Citation, ClaimBasis, SourceKind, _Strict
from .registry import REPO_ROOT, Registry, sha256_file

TAXONOMY_PATH = REPO_ROOT / "data" / "taxonomy" / "network_taxonomy.yaml"

# The owner's directive, section 3, "Study at minimum". Hyphanet and Freenet are two
# distinct systems since the 2023 rename, so both are required.
REQUIRED_SUBJECTS: frozenset[str] = frozenset(
    {
        "www", "arpanet", "tor", "i2p", "hyphanet", "freenet", "gnunet", "ipfs", "zeronet",
        "gopher", "gemini", "usenet", "dht", "p2p", "mesh", "federated",
        "experimental_protocols", "private_intranet",
    }
)

# The twelve facets in directive section 3, in order.
FACETS: tuple[str, ...] = (
    "origin",  # 1. how it originated
    "purpose",  # 2. why it was developed
    "public_disclosure",  # 3. how its existence became publicly known
    "architecture",  # 4. underlying architecture
    "protocols",  # 5. communication protocols
    "resource_identification",  # 6. resource identification model
    "discovery",  # 7. information discovery mechanisms
    "documentation",  # 8. public technical documentation
    "infrastructure_relationship",  # 9. relationship to existing infrastructure
    "distinguishing_characteristics",  # 10. distinguishing architectural characteristics
    "limitations",  # 11. observable limitations
    "comparison",  # 12. similarities and differences relative to other systems
)


class Facet(_Strict):
    text: str = Field(min_length=10)
    basis: ClaimBasis
    citations: list[Citation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _basis_rules(self) -> "Facet":
        if self.basis is ClaimBasis.SOURCED and not self.citations:
            raise ValueError("a 'sourced' facet must carry at least one citation with a verbatim quote")
        return self


class Vocabulary(_Strict):
    layers: dict[str, str] = Field(min_length=1)
    topology: dict[str, str] = Field(min_length=1)
    resource_identification: dict[str, str] = Field(min_length=1)
    discovery: dict[str, str] = Field(min_length=1)
    patterns: dict[str, str] = Field(min_length=1)


class Entry(_Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_]*$")
    name: str
    kind: Literal["system", "pattern", "category"]
    aliases: list[str] = Field(default_factory=list)
    lifecycle: Literal["historical", "operational", "experimental", "mixed", "renamed", "unknown"]
    layers: list[str] = Field(min_length=1)
    topology: list[str] = Field(min_length=1)
    resource_identification_types: list[str] = Field(min_length=1)
    discovery_types: list[str] = Field(min_length=1)
    patterns: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list, description="Named instances for pattern/category entries")
    facets: dict[str, Facet]
    open_questions: list[str] = Field(default_factory=list)
    last_reviewed: date

    @field_validator("facets")
    @classmethod
    def _all_facets(cls, v: dict[str, Facet]) -> dict[str, Facet]:
        missing = [f for f in FACETS if f not in v]
        extra = [f for f in v if f not in FACETS]
        if missing or extra:
            raise ValueError(f"facets must be exactly the twelve required facets; missing={missing} extra={extra}")
        return v


class Taxonomy(_Strict):
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    taxonomy_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    released: date
    description: str
    vocabulary: Vocabulary
    entries: list[Entry] = Field(min_length=1)

    @model_validator(mode="after")
    def _integrity(self) -> "Taxonomy":
        errors: list[str] = []
        ids = [e.id for e in self.entries]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            errors.append(f"duplicate entry ids: {sorted(dupes)}")
        idset = set(ids)
        missing = REQUIRED_SUBJECTS - idset
        if missing:
            errors.append(f"required subjects missing: {sorted(missing)}")
        v = self.vocabulary
        for e in self.entries:
            for field, vocab in (
                ("layers", v.layers),
                ("topology", v.topology),
                ("resource_identification_types", v.resource_identification),
                ("discovery_types", v.discovery),
                ("patterns", v.patterns),
            ):
                bad = [x for x in getattr(e, field) if x not in vocab]
                if bad:
                    errors.append(f"{e.id}.{field}: values not in vocabulary: {bad}")
            bad_rel = [r for r in e.related if r not in idset]
            if bad_rel:
                errors.append(f"{e.id}.related: unknown entry ids {bad_rel}")
            if e.id in e.related:
                errors.append(f"{e.id}.related: an entry can't relate to itself")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    def iter_citations(self):
        for e in self.entries:
            for fname in FACETS:
                for c in e.facets[fname].citations:
                    yield e.id, fname, c


@dataclass(frozen=True)
class LoadedTaxonomy:
    path: Path
    sha256: str
    taxonomy: Taxonomy


def load_taxonomy(path: Path = TAXONOMY_PATH) -> LoadedTaxonomy:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return LoadedTaxonomy(path=path, sha256=sha256_file(path), taxonomy=Taxonomy.model_validate(data))


def cross_validate(tax: Taxonomy, registry: Registry) -> list[str]:
    """Check that every citation resolves to a registered reference document."""
    errors: list[str] = []
    sources = registry.sources
    for entry_id, facet, c in tax.iter_citations():
        src = sources.get(c.ref)
        if src is None:
            errors.append(f"{entry_id}.{facet}: citation ref {c.ref!r} is not in the source registry")
        elif src.kind is not SourceKind.REFERENCE_DOCUMENT:
            errors.append(f"{entry_id}.{facet}: citation ref {c.ref!r} is a {src.kind.value}, not a reference_document")
    return errors


def basis_counts(entry: Entry) -> dict[str, int]:
    counts = {b.value: 0 for b in ClaimBasis}
    for f in FACETS:
        counts[entry.facets[f].basis.value] += 1
    return counts
