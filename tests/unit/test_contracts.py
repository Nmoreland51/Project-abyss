"""T22: data-contract invariants. Each test is a rule of evidence enforced by the types."""

from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from abyss.core.contracts import (
    AccessBasis, Budget, Citation, Finding, FindingStatus, Hypothesis, HypothesisStatus, Job, JobStatus,
    Observation, RecordScope, Reliability, RetrievalOutcome, RetrievalRecord, Signature, Source, SourceKind, Tool,
)

NOW = datetime(2026, 11, 24, tzinfo=timezone.utc)
SHA = "a" * 64


def _source(**kw):
    base = dict(id="s1", kind=SourceKind.REFERENCE_DOCUMENT, title="A source", uri="https://example.org/x",
                publisher="Example", access_basis=AccessBasis.PUBLIC_OPEN, license_or_terms="unverified",
                reliability=Reliability.PRIMARY, added=date(2026, 11, 24))
    base.update(kw)
    return Source(**base)


class TestCitation:
    def test_valid(self):
        assert Citation(ref="rfc1", quote="Date: 7 April 1969").ref == "rfc1"

    def test_quote_too_short_is_rejected(self):
        with pytest.raises(ValidationError):
            Citation(ref="rfc1", quote="1969")

    @pytest.mark.parametrize("q", ["first part ... second part", "first part … second"])
    def test_ellipsis_is_rejected(self, q):
        with pytest.raises(ValidationError, match="contiguous"):
            Citation(ref="rfc1", quote=q)

    def test_unknown_fields_rejected(self):
        with pytest.raises(ValidationError):
            Citation(ref="rfc1", quote="Date: 7 April 1969", verified=True)

    def test_records_are_immutable(self):
        c = Citation(ref="rfc1", quote="Date: 7 April 1969")
        with pytest.raises(ValidationError):
            c.quote = "something else entirely"


class TestSource:
    def test_valid(self):
        assert _source().access_basis is AccessBasis.PUBLIC_OPEN

    def test_non_http_uri_rejected(self):
        with pytest.raises(ValidationError, match="http"):
            _source(uri="gemini://geminiprotocol.net/")

    def test_restricted_cannot_be_ingestion_endpoint(self):
        with pytest.raises(ValidationError, match="lead"):
            _source(kind=SourceKind.INGESTION_ENDPOINT, access_basis=AccessBasis.RESTRICTED)

    def test_restricted_reference_allowed_as_lead(self):
        assert _source(access_basis=AccessBasis.RESTRICTED).access_basis is AccessBasis.RESTRICTED

    def test_terms_verified_requires_terms_uri(self):
        with pytest.raises(ValidationError, match="terms_uri"):
            _source(terms_verified=True)
        assert _source(terms_verified=True, terms_uri="https://example.org/terms").terms_verified


class TestRetrievalRecord:
    def test_ok_requires_hash(self):
        with pytest.raises(ValidationError, match="sha256"):
            RetrievalRecord(source_id="s1", uri="https://x", retrieved_at=NOW, outcome=RetrievalOutcome.OK)

    def test_failure_requires_error(self):
        with pytest.raises(ValidationError, match="error"):
            RetrievalRecord(source_id="s1", uri="https://x", retrieved_at=NOW, outcome=RetrievalOutcome.BLOCKED)

    def test_valid_failure(self):
        r = RetrievalRecord(source_id="s1", uri="https://x", retrieved_at=NOW, outcome=RetrievalOutcome.BLOCKED,
                            http_status=403, error="HTTP 403")
        assert r.outcome is RetrievalOutcome.BLOCKED


class TestObservationAndSignature:
    def test_observation_requires_real_hash_and_scope(self):
        with pytest.raises(ValidationError):
            Observation(id="o1", source_id="s1", content_sha256="not-a-hash", observed_at=NOW, scope=RecordScope.LABORATORY)
        with pytest.raises(ValidationError):
            Observation(id="o1", source_id="s1", content_sha256=SHA, observed_at=NOW)  # scope is mandatory
        assert Observation(id="o1", source_id="s1", content_sha256=SHA, observed_at=NOW, scope=RecordScope.SYNTHETIC)

    def test_signature_requires_provenance_and_limitations(self):
        with pytest.raises(ValidationError):
            Signature(id="sig1", version="0.1.0", family="tor", feature="signed_directory",
                      definition="Clients fetch a signed relay directory", provenance=[], reliability=Reliability.PRIMARY,
                      limitations="Shared by other directory-based overlays")


def _hyp(**kw):
    base = dict(id="h1", claim="Observation o1 reflects an undocumented overlay family", observation_ids=["o1"],
                alternative_explanations=["measurement error", "known family with new version"],
                proposed_test="Re-measure with a second independent capture", falsification_conditions=["o1 matches a known signature"],
                confidence=0.2, confidence_rationale="single observation", scope=RecordScope.LABORATORY)
    base.update(kw)
    return Hypothesis(**base)


class TestHypothesis:
    def test_valid(self):
        assert _hyp().status is HypothesisStatus.OPEN

    @pytest.mark.parametrize("field", ["alternative_explanations", "falsification_conditions", "observation_ids"])
    def test_must_be_falsifiable_and_grounded(self, field):
        with pytest.raises(ValidationError):
            _hyp(**{field: []})

    def test_refuted_needs_contradicting_evidence(self):
        with pytest.raises(ValidationError, match="contradicting"):
            _hyp(status=HypothesisStatus.REFUTED)
        assert _hyp(status=HypothesisStatus.REFUTED, contradicting_evidence_ids=["e9"]).status is HypothesisStatus.REFUTED

    def test_supported_needs_supporting_evidence(self):
        with pytest.raises(ValidationError, match="supporting"):
            _hyp(status=HypothesisStatus.SUPPORTED)

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            _hyp(confidence=1.5)


def _finding(**kw):
    base = dict(id="f1", statement="Tool X solves problem Y as documented", confidence_rationale="two sources", scope=RecordScope.REAL_WORLD)
    base.update(kw)
    return Finding(**base)


class TestFinding:
    def test_verified_requires_evidence(self):
        with pytest.raises(ValidationError, match="evidence"):
            _finding(status=FindingStatus.VERIFIED, verification_method="manual")

    def test_real_world_verified_requires_two_independent_sources(self):
        with pytest.raises(ValidationError, match="2 distinct"):
            _finding(status=FindingStatus.VERIFIED, evidence_ids=["e1"], verification_method="m",
                     corroborating_source_ids=["src_a", "src_a"])
        ok = _finding(status=FindingStatus.VERIFIED, evidence_ids=["e1"], verification_method="m",
                      corroborating_source_ids=["src_a", "src_b"])
        assert ok.status is FindingStatus.VERIFIED

    def test_lab_verified_needs_method_but_not_two_sources(self):
        f = _finding(scope=RecordScope.LABORATORY, status=FindingStatus.VERIFIED, evidence_ids=["e1"], verification_method="replicated run")
        assert f.scope is RecordScope.LABORATORY

    def test_fixture_can_never_be_verified(self):
        with pytest.raises(ValidationError, match="fixture"):
            _finding(scope=RecordScope.FIXTURE, status=FindingStatus.VERIFIED, evidence_ids=["e1"], verification_method="m")

    def test_retraction_keeps_reason(self):
        with pytest.raises(ValidationError, match="retraction"):
            _finding(status=FindingStatus.RETRACTED)


class TestTool:
    def test_capabilities_must_be_cited(self):
        with pytest.raises(ValidationError):
            Tool(id="t1", name="X", source_uris=["https://x"], problem_solved="does a thing", documented_capabilities=[],
                 availability="public", license="MIT", cost="free")


class TestJob:
    def _job(self, **kw):
        base = dict(id="j1", objective="Survey gemini tools", allowed_source_ids=["pypi_json"],
                    budget=Budget(max_seconds=60, max_requests=10, max_bytes=10_000, max_attempts=3),
                    created_at=NOW, updated_at=NOW)
        base.update(kw)
        return Job(**base)

    def test_attempts_bounded_by_budget(self):
        with pytest.raises(ValidationError, match="max_attempts"):
            self._job(attempts=4)

    def test_running_requires_started_at(self):
        with pytest.raises(ValidationError, match="started_at"):
            self._job(status=JobStatus.RUNNING)

    def test_failed_requires_error(self):
        with pytest.raises(ValidationError, match="last_error"):
            self._job(status=JobStatus.FAILED, started_at=NOW)

    def test_time_order(self):
        with pytest.raises(ValidationError, match="precedes"):
            self._job(updated_at=NOW - timedelta(seconds=1))

    def test_scope_required(self):
        with pytest.raises(ValidationError):
            self._job(allowed_source_ids=[])
