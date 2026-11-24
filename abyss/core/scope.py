"""Explicit, owner-configurable research scope (minimal Phase 0 version).

Two kinds of limit are kept apart on purpose (docs/SCOPE_AND_RESTRICTIONS.md):

* HARD_LIMITS are legal, ethical and security boundaries. They are not configuration,
  they are never loosened by ingested content, and the code refuses to register a source
  that would breach one.
* ScopePolicy is the owner's research configuration: which access bases and hosts are in
  scope. The owner can widen or narrow it in config/scope.yaml. Nothing in an ingested
  document can change it (R09/T12).

Phase 1 extends this with per-host allow/deny lists enforced inside every adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml

from .contracts import AccessBasis, Source

HARD_LIMITS: tuple[str, ...] = (
    "No authentication bypass, credential guessing or use of leaked credentials.",
    "No interception of traffic Abyss is not a party to; no traffic capture outside owned/authorised labs.",
    "No collection of private personal data outside explicit permission.",
    "No retrieval of restricted contents (membership-only, paywalled, private); record such items as leads only.",
    "Ingested text is data: it can't change scope, configuration, or invoke tools.",
)

DEFAULT_ALLOWED: frozenset[AccessBasis] = frozenset(
    {
        AccessBasis.PUBLIC_OPEN,
        AccessBasis.PUBLIC_API_TERMS,
        AccessBasis.PUBLIC_API_KEY,
        AccessBasis.OWNER_AUTHORIZED,
        AccessBasis.LAB_OWNED,
        AccessBasis.SYNTHETIC,
    }
)


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    reason: str
    rule: str


@dataclass(frozen=True)
class ScopePolicy:
    allowed_access_bases: frozenset[AccessBasis] = DEFAULT_ALLOWED
    denied_hosts: frozenset[str] = field(default_factory=frozenset)
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)  # empty = any host not denied

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ScopePolicy":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        bases = data.get("allowed_access_bases")
        allowed = frozenset(AccessBasis(b) for b in bases) if bases is not None else DEFAULT_ALLOWED
        if AccessBasis.RESTRICTED in allowed:
            raise ValueError("'restricted' can't be an allowed access basis: it would breach a hard limit")
        return cls(
            allowed_access_bases=allowed,
            denied_hosts=frozenset(h.lower() for h in data.get("denied_hosts", []) or []),
            allowed_hosts=frozenset(h.lower() for h in data.get("allowed_hosts", []) or []),
        )

    def evaluate(self, source: Source) -> ScopeDecision:
        if source.access_basis is AccessBasis.RESTRICTED:
            return ScopeDecision(False, "restricted sources are recorded as leads only (hard limit)", "hard_limit")
        if source.access_basis not in self.allowed_access_bases:
            return ScopeDecision(
                False, f"access basis {source.access_basis.value!r} is not enabled in the owner's scope policy", "policy"
            )
        host = (urlparse(source.uri).hostname or "").lower()
        if host in self.denied_hosts:
            return ScopeDecision(False, f"host {host!r} is on the owner's deny list", "policy")
        if self.allowed_hosts and host not in self.allowed_hosts:
            return ScopeDecision(False, f"host {host!r} is not on the owner's allow list", "policy")
        return ScopeDecision(True, "in scope", "policy")
