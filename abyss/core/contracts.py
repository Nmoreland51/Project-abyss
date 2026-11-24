"""Versioned data contracts for Project Abyss (contract version 0.1.0).

These Pydantic models are the Phase 0 implementation of the data contracts in
docs/MASTER_ARCHITECTURE.md section 5. They put the project's rules of evidence
into the types themselves, so that an invalid record can't be built at all:

* a sourced claim must carry at least one verbatim quotation from a registered source;
* a hypothesis must state alternatives and falsification conditions;
* a real-world verified finding needs independent corroboration (>= 2 distinct sources);
* synthetic or laboratory records can't be presented as real-world results;
* a job's attempts can't exceed its budget.

Persistence (Phase 1) and the engines that produce these records (Phases 2-5) are
not implemented yet. See docs/IMPLEMENTATION_STATUS.md.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONTRACT_VERSION = "0.1.0"

_ID = r"^[a-z0-9][a-z0-9_.\-]*$"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = r"^\d+\.\d+\.\d+$"


class _Strict(BaseModel):
    """Base: unknown fields are rejected; records are immutable once built."""

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


# --------------------------------------------------------------------------- enums


class AccessBasis(str, Enum):
    """Why Abyss is permitted to read a source. Recorded on every source."""

    PUBLIC_OPEN = "public_open"  # openly published; no account needed
    PUBLIC_API_TERMS = "public_api_terms"  # public API, usable under published terms/rate limits
    PUBLIC_API_KEY = "public_api_key"  # public API requiring free registration or key
    OWNER_AUTHORIZED = "owner_authorized"  # collection the owner controls or is explicitly authorised for
    LAB_OWNED = "lab_owned"  # generated in an owned, controlled laboratory environment
    SYNTHETIC = "synthetic"  # generated synthetic data (never a real-world result)
    RESTRICTED = "restricted"  # needs membership/permission Abyss does not hold: record as lead only


class SourceKind(str, Enum):
    REFERENCE_DOCUMENT = "reference_document"  # a document cited as evidence (spec, RFC, paper, page)
    INGESTION_ENDPOINT = "ingestion_endpoint"  # an API/feed an adapter may query
    DATASET = "dataset"  # a downloadable dataset


class Reliability(str, Enum):
    PRIMARY = "primary"  # the originator: spec authors, the project itself, the standards body
    AUTHORITATIVE_SECONDARY = "authoritative_secondary"  # e.g. a history written by participants
    SECONDARY = "secondary"
    COMMUNITY = "community"  # forums, wikis, aggregators
    UNKNOWN = "unknown"


class ClaimBasis(str, Enum):
    """Epistemic basis of a statement. Kept separate so analysis is never presented as fact."""

    SOURCED = "sourced"  # asserted by cited source(s); each citation carries a checkable quote
    ANALYSIS = "analysis"  # synthesis/comparison by the Abyss authors; not a sourced fact
    UNVERIFIED = "unverified"  # commonly stated, but not checked against a retrieved source


class RecordScope(str, Enum):
    """Where a record's evidence comes from. Keeps synthetic and live research separate."""

    REAL_WORLD = "real_world"
    LABORATORY = "laboratory"
    SYNTHETIC = "synthetic"
    FIXTURE = "fixture"  # test fixture; never reportable


class RetrievalOutcome(str, Enum):
    OK = "ok"
    FETCH_FAILED = "fetch_failed"  # network/server error
    BLOCKED = "blocked"  # refused by policy (egress proxy, 403/407) - not a pass
    RATE_LIMITED = "rate_limited"  # 429 - not a pass
    TEXT_UNEXTRACTABLE = "text_unextractable"  # retrieved but no usable text (e.g. encoded PDF)


class HypothesisStatus(str, Enum):
    OPEN = "open"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"
    RETRACTED = "retracted"


class FindingStatus(str, Enum):
    CANDIDATE = "candidate"
    CORROBORATED = "corroborated"
    VERIFIED = "verified"
    REJECTED = "rejected"
    RETRACTED = "retracted"


class JobStatus(str, Enum):
    """Real execution states. The UI must show exactly these (R10/T15)."""

    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class ImplementationStatus(str, Enum):
    """Status vocabulary for requirements traceability."""

    NOT_IMPLEMENTED = "not_implemented"
    PARTIAL = "partial"
    IMPLEMENTED_UNVERIFIED = "implemented_unverified"
    SIMULATED_ONLY = "simulated_only"
    VERIFIED = "verified"
    BLOCKED = "blocked"


# ---------------------------------------------------------------------- evidence


class Citation(_Strict):
    """A pointer into a registered source plus a verbatim quotation that supports the claim.

    The quotation is checked against the live retrieved text by abyss.foundation.citations;
    a citation whose quote can't be found is reported as QUOTE_NOT_FOUND, never silently accepted.
    """

    ref: str = Field(pattern=_ID, description="Source id in the registry")
    quote: str = Field(min_length=8, max_length=400)
    locator: Optional[str] = Field(default=None, description="Section, page or anchor, if known")

    @field_validator("quote")
    @classmethod
    def _no_ellipsis(cls, v: str) -> str:
        if "..." in v or "…" in v:
            raise ValueError("quotes must be contiguous verbatim text; split into two citations instead of using ellipses")
        return v


class Source(_Strict):
    """Registry record: what a source is, why Abyss may use it, and how reliable it is."""

    id: str = Field(pattern=_ID)
    kind: SourceKind
    title: str = Field(min_length=3)
    uri: str
    publisher: str = Field(min_length=2)
    access_basis: AccessBasis
    license_or_terms: str = Field(min_length=3, description="What is known about licence/terms; say 'unverified' if not read")
    terms_uri: Optional[str] = None
    terms_verified: bool = Field(default=False, description="True only if the terms text was actually read and recorded")
    published: Optional[str] = Field(default=None, description="Publication date as stated by the source, ISO-like, may be partial")
    reliability: Reliability
    reliability_notes: str = ""
    coverage: str = ""
    limitations: str = ""
    probe_uri: Optional[str] = Field(default=None, description="Lightweight endpoint used to test reachability")
    rate_limit_notes: str = ""
    added: date

    @field_validator("uri", "terms_uri", "probe_uri")
    @classmethod
    def _http_only(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith(("https://", "http://")):
            raise ValueError(f"only http(s) URIs are supported in contract v0: {v!r}")
        return v

    @model_validator(mode="after")
    def _terms_claims_need_a_reference(self) -> "Source":
        if self.terms_verified and not self.terms_uri:
            raise ValueError("terms_verified=True requires the terms_uri that was read")
        return self

    @model_validator(mode="after")
    def _restricted_sources_are_leads_only(self) -> "Source":
        if self.access_basis is AccessBasis.RESTRICTED and self.kind is SourceKind.INGESTION_ENDPOINT:
            raise ValueError("a RESTRICTED source can be recorded as a lead but not registered as an ingestion endpoint")
        return self


class RetrievalRecord(_Strict):
    """One retrieval attempt. Every fetch, including a failed one, produces exactly one of these."""

    source_id: str = Field(pattern=_ID)
    uri: str
    retrieved_at: datetime
    outcome: RetrievalOutcome
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    bytes: int = Field(default=0, ge=0)
    truncated: bool = Field(default=False, description="True if reading stopped at a byte cap; sha256 then covers the prefix only")
    sha256: Optional[str] = None
    text_chars: int = Field(default=0, ge=0)
    extraction_method: Optional[str] = None
    error: Optional[str] = None
    elapsed_ms: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _ok_requires_hash(self) -> "RetrievalRecord":
        if self.outcome in (RetrievalOutcome.OK, RetrievalOutcome.TEXT_UNEXTRACTABLE):
            if not self.sha256 or not _SHA256.match(self.sha256):
                raise ValueError("a successful retrieval must record a sha256 content hash")
        if self.outcome is not RetrievalOutcome.OK and self.outcome is not RetrievalOutcome.TEXT_UNEXTRACTABLE and not self.error:
            raise ValueError("a failed retrieval must record the error")
        return self


# ------------------------------------------------------------------ research data


FeatureValue = Union[float, int, str, bool]


class Observation(_Strict):
    id: str = Field(pattern=_ID)
    source_id: str = Field(pattern=_ID)
    content_sha256: str
    observed_at: datetime
    scope: RecordScope
    features: dict[str, FeatureValue] = Field(default_factory=dict)
    quality_flags: list[str] = Field(default_factory=list)

    @field_validator("content_sha256")
    @classmethod
    def _hash(cls, v: str) -> str:
        if not _SHA256.match(v):
            raise ValueError("content_sha256 must be a lowercase hex sha256 digest")
        return v


class Signature(_Strict):
    """A documented architectural characteristic. See docs/SIGNATURE_SPECIFICATION.md."""

    id: str = Field(pattern=_ID)
    version: str = Field(pattern=_SEMVER)
    family: str = Field(pattern=_ID)
    feature: str = Field(pattern=_ID)
    definition: str = Field(min_length=10)
    provenance: list[Citation] = Field(min_length=1)
    reliability: Reliability
    limitations: str = Field(min_length=5)
    overlaps_with: list[str] = Field(default_factory=list, description="Other families/technologies sharing this trait")
    last_verified: Optional[date] = None


class Hypothesis(_Strict):
    """A research claim that can be tested and disproved. See docs/RESEARCH_METHODOLOGY.md."""

    id: str = Field(pattern=_ID)
    claim: str = Field(min_length=10)
    observation_ids: list[str] = Field(min_length=1)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(min_length=1, description="Ordinary explanations must be stated first")
    proposed_test: str = Field(min_length=10)
    falsification_conditions: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_rationale: str = Field(min_length=5)
    status: HypothesisStatus = HypothesisStatus.OPEN
    scope: RecordScope

    @model_validator(mode="after")
    def _refuted_needs_contradiction(self) -> "Hypothesis":
        if self.status is HypothesisStatus.REFUTED and not self.contradicting_evidence_ids:
            raise ValueError("a REFUTED hypothesis must reference the contradicting evidence")
        if self.status is HypothesisStatus.SUPPORTED and not self.supporting_evidence_ids:
            raise ValueError("a SUPPORTED hypothesis must reference supporting evidence")
        return self


class ReviewEvent(_Strict):
    at: datetime
    reviewer: str = Field(min_length=1)
    from_status: FindingStatus
    to_status: FindingStatus
    reason: str = Field(min_length=3)


class Finding(_Strict):
    id: str = Field(pattern=_ID)
    statement: str = Field(min_length=10)
    hypothesis_id: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    corroborating_source_ids: list[str] = Field(default_factory=list)
    confidence_rationale: str = Field(min_length=5)
    status: FindingStatus = FindingStatus.CANDIDATE
    scope: RecordScope
    verification_method: Optional[str] = None
    retraction_reason: Optional[str] = None
    review_history: list[ReviewEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def _evidence_rules(self) -> "Finding":
        if self.status in (FindingStatus.CORROBORATED, FindingStatus.VERIFIED) and not self.evidence_ids:
            raise ValueError("corroborated/verified findings must reference retrievable evidence")
        if self.status is FindingStatus.VERIFIED:
            if not self.verification_method:
                raise ValueError("verified findings must state the verification method")
            if self.scope is RecordScope.REAL_WORLD and len(set(self.corroborating_source_ids)) < 2:
                raise ValueError("a real-world verified finding needs >= 2 distinct corroborating sources")
            if self.scope is RecordScope.FIXTURE:
                raise ValueError("fixture records can never be verified findings")
        if self.status is FindingStatus.RETRACTED and not self.retraction_reason:
            raise ValueError("retracted findings must keep the retraction reason")
        return self


class MaintenanceStatus(str, Enum):
    ACTIVE = "active"
    LOW_ACTIVITY = "low_activity"
    UNMAINTAINED = "unmaintained"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class Tool(_Strict):
    """A candidate practical tool. Every capability claim is a Citation, never free text."""

    id: str = Field(pattern=_ID)
    name: str = Field(min_length=1)
    source_uris: list[str] = Field(min_length=1)
    problem_solved: str = Field(min_length=5)
    documented_capabilities: list[Citation] = Field(min_length=1)
    availability: str
    license: str = Field(description="SPDX id if known, else 'unknown'")
    cost: str = Field(description="'free', a price, or 'unknown'")
    maintenance: MaintenanceStatus = MaintenanceStatus.UNKNOWN
    last_release: Optional[date] = None
    dependencies: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    requires_membership: bool = Field(default=False, description="True: lead only; Abyss does not obtain restricted contents")


class Budget(_Strict):
    max_seconds: int = Field(gt=0)
    max_requests: int = Field(gt=0)
    max_bytes: int = Field(gt=0)
    max_attempts: int = Field(gt=0, le=20)


class Job(_Strict):
    id: str = Field(pattern=_ID)
    objective: str = Field(min_length=5)
    allowed_source_ids: list[str] = Field(min_length=1)
    budget: Budget
    status: JobStatus = JobStatus.PLANNED
    attempts: int = Field(default=0, ge=0)
    checkpoint: Optional[dict] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    updated_at: datetime
    last_error: Optional[str] = None

    @model_validator(mode="after")
    def _budget_and_state(self) -> "Job":
        if self.attempts > self.budget.max_attempts:
            raise ValueError("attempts exceed the job's max_attempts budget")
        if self.status in (JobStatus.RUNNING, JobStatus.COMPLETE, JobStatus.FAILED) and self.started_at is None:
            raise ValueError(f"a {self.status.value} job must record started_at")
        if self.status is JobStatus.FAILED and not self.last_error:
            raise ValueError("a failed job must record last_error")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at precedes created_at")
        return self

