"""T14 (partial): scope decisions are explicit, explained and owner-configurable; hard limits are not configurable."""

import dataclasses
from datetime import date

import pytest

from abyss.cli import SCOPE_PATH
from abyss.core.contracts import AccessBasis, Reliability, Source, SourceKind
from abyss.core.scope import DEFAULT_ALLOWED, HARD_LIMITS, ScopePolicy
from abyss.foundation.registry import load_registry


def _src(basis=AccessBasis.PUBLIC_OPEN, uri="https://example.org/a", kind=SourceKind.REFERENCE_DOCUMENT):
    return Source(id="s", kind=kind, title="t t t", uri=uri, publisher="pp", access_basis=basis,
                  license_or_terms="unverified", reliability=Reliability.UNKNOWN, added=date(2026, 11, 24))


def test_restricted_is_rejected_as_hard_limit():
    d = ScopePolicy().evaluate(_src(AccessBasis.RESTRICTED))
    assert not d.allowed and d.rule == "hard_limit"


def test_policy_rejection_is_explained():
    policy = ScopePolicy(allowed_access_bases=frozenset({AccessBasis.PUBLIC_OPEN}))
    d = policy.evaluate(_src(AccessBasis.PUBLIC_API_KEY))
    assert not d.allowed and d.rule == "policy" and "public_api_key" in d.reason


def test_denied_and_allowed_hosts():
    assert not ScopePolicy(denied_hosts=frozenset({"example.org"})).evaluate(_src()).allowed
    only = ScopePolicy(allowed_hosts=frozenset({"rfc-editor.org"}))
    assert not only.evaluate(_src()).allowed
    assert only.evaluate(_src(uri="https://rfc-editor.org/x")).allowed


def test_restricted_cannot_be_enabled_by_config(tmp_path):
    p = tmp_path / "scope.yaml"
    p.write_text("allowed_access_bases: [public_open, restricted]\n")
    with pytest.raises(ValueError, match="hard limit"):
        ScopePolicy.from_yaml(p)


def test_policy_is_immutable():
    policy = ScopePolicy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.allowed_access_bases = frozenset(AccessBasis)


def test_repo_scope_config_matches_documented_default():
    assert ScopePolicy.from_yaml(SCOPE_PATH).allowed_access_bases == DEFAULT_ALLOWED


def test_every_registered_source_is_in_default_scope():
    policy = ScopePolicy.from_yaml(SCOPE_PATH)
    rejected = {sid: policy.evaluate(s).reason for sid, s in load_registry().sources.items() if not policy.evaluate(s).allowed}
    assert rejected == {}


def test_hard_limits_are_stated():
    assert len(HARD_LIMITS) >= 5 and any("interception" in h for h in HARD_LIMITS)
