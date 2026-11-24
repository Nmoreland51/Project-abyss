"""LIVE tests (ABYSS_LIVE=1). These retrieve real documents. If skipped, report them as SKIPPED, never as passed.

T01 (Phase 0 part): real public sources are retrieved with provenance and content hashes.
T08 (Phase 0 part): every taxonomy citation's quote is present in its live source; fabricated quotes are caught.
"""

import pytest

from abyss.core.contracts import RetrievalOutcome
from abyss.foundation.citations import verify_citations
from abyss.foundation.fetch import extract_text, find_quote, http_fetch, normalize
from abyss.foundation.registry import load_registry
from abyss.foundation.taxonomy import load_taxonomy

pytestmark = pytest.mark.live


def test_negative_control_fabricated_quote_is_not_found():
    """The checker must not be vacuous: a plausible but invented claim must fail against the real RFC."""
    r = http_fetch("rfc1436", "https://www.rfc-editor.org/rfc/rfc1436.txt")
    assert r.record.outcome is RetrievalOutcome.OK, r.record.error
    text = normalize(extract_text(r.body, r.record.content_type)[0])
    assert find_quote(text, "The Internet Gopher Protocol (a distributed document search and retrieval protocol)")
    assert find_quote(text, "Gopher was invented at MIT in 1975 as a successor to the Web") is None
    assert find_quote(text, "University of Minnesota March 1994") is None  # off-by-one date must fail


def test_all_taxonomy_citations_against_live_sources(tmp_path):
    report = verify_citations(load_taxonomy(), load_registry())
    by = report["summary"]["citations_by_outcome"]
    missing = [c for c in report["citations"] if c["outcome"] == "QUOTE_NOT_FOUND"]
    assert not missing, f"unsupported citations: {missing}"
    # Source-availability problems are environment issues; surface them instead of hiding them.
    unavailable = {k: v for k, v in by.items() if k not in ("VERIFIED", "QUOTE_NOT_FOUND")}
    print(f"\nlive citation outcomes: {by}; unavailable: {unavailable}")
    for r in report["retrievals"]:
        if r["outcome"] == "ok":
            assert r["sha256"] and r["bytes"] > 0
