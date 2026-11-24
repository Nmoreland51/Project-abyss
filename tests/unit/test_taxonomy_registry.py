"""T21: taxonomy and source-registry integrity (offline). Live quote checks are in tests/live."""

import copy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from abyss.core.contracts import ClaimBasis, SourceKind
from abyss.foundation.registry import INGESTION_PATH, REFERENCES_PATH, RegistryError, load_registry
from abyss.foundation.taxonomy import FACETS, REQUIRED_SUBJECTS, TAXONOMY_PATH, Taxonomy, cross_validate, load_taxonomy


@pytest.fixture(scope="module")
def raw():
    return yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def loaded():
    return load_taxonomy()


@pytest.fixture(scope="module")
def registry():
    return load_registry()


def test_taxonomy_loads_and_covers_owner_required_subjects(loaded):
    ids = {e.id for e in loaded.taxonomy.entries}
    assert REQUIRED_SUBJECTS <= ids


def test_every_entry_documents_all_twelve_facets(loaded):
    for e in loaded.taxonomy.entries:
        assert tuple(e.facets) == FACETS or set(e.facets) == set(FACETS), e.id


def test_every_entry_has_at_least_one_sourced_facet(loaded):
    for e in loaded.taxonomy.entries:
        assert any(f.basis is ClaimBasis.SOURCED for f in e.facets.values()), e.id


def test_all_citations_resolve_to_registered_reference_documents(loaded, registry):
    assert cross_validate(loaded.taxonomy, registry) == []


def test_no_orphan_reference_documents(loaded, registry):
    cited = {c.ref for _, _, c in loaded.taxonomy.iter_citations()}
    refs = {sid for sid, s in registry.sources.items() if s.kind is SourceKind.REFERENCE_DOCUMENT}
    assert refs - cited == set(), "registered reference documents nobody cites"


def test_missing_facet_rejected(raw):
    bad = copy.deepcopy(raw)
    del bad["entries"][0]["facets"]["origin"]
    with pytest.raises(ValidationError, match="twelve"):
        Taxonomy.model_validate(bad)


def test_sourced_facet_without_citation_rejected(raw):
    bad = copy.deepcopy(raw)
    f = bad["entries"][0]["facets"]["origin"]
    f["basis"] = "sourced"
    f["citations"] = []
    with pytest.raises(ValidationError, match="at least one citation"):
        Taxonomy.model_validate(bad)


def test_vocabulary_is_enforced(raw):
    bad = copy.deepcopy(raw)
    bad["entries"][0]["topology"] = ["quantum_mesh"]
    with pytest.raises(ValidationError, match="not in vocabulary"):
        Taxonomy.model_validate(bad)


def test_unknown_related_entry_rejected(raw):
    bad = copy.deepcopy(raw)
    bad["entries"][0]["related"] = ["nonexistent_network"]
    with pytest.raises(ValidationError, match="unknown entry"):
        Taxonomy.model_validate(bad)


def test_required_subject_cannot_be_silently_dropped(raw):
    bad = copy.deepcopy(raw)
    bad["entries"] = [e for e in bad["entries"] if e["id"] != "gopher"]
    with pytest.raises(ValidationError, match="required subjects missing"):
        Taxonomy.model_validate(bad)


def test_cross_validate_flags_unregistered_and_wrong_kind_refs(raw, registry):
    bad = copy.deepcopy(raw)
    cites = bad["entries"][0]["facets"]["origin"]["citations"]
    cites.append({"ref": "invented_source", "quote": "a quote that does not exist anywhere"})
    cites.append({"ref": "pypi_json", "quote": "an ingestion endpoint is not evidence"})
    errs = cross_validate(Taxonomy.model_validate(bad), registry)
    assert any("invented_source" in e for e in errs) and any("pypi_json" in e for e in errs)


def test_registries_load_without_duplicates(registry):
    assert len(registry.sources) == sum(len(rf.sources) for _, _, rf in registry.files)


def test_reference_and_ingestion_files_hold_the_right_kinds():
    refs = load_registry(REFERENCES_PATH).sources.values()
    ing = load_registry(INGESTION_PATH).sources.values()
    assert all(s.kind is SourceKind.REFERENCE_DOCUMENT for s in refs)
    assert all(s.kind is not SourceKind.REFERENCE_DOCUMENT for s in ing)


def test_duplicate_ids_across_files_rejected(tmp_path):
    text = REFERENCES_PATH.read_text(encoding="utf-8")
    a, b = tmp_path / "a.yaml", tmp_path / "b.yaml"
    a.write_text(text)
    b.write_text(text)
    with pytest.raises(RegistryError, match="duplicate source id"):
        load_registry(a, b)


def test_no_source_claims_unread_terms_as_verified(registry):
    for s in registry.sources.values():
        if s.terms_verified:
            assert s.terms_uri, s.id
