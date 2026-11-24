"""T08 (offline part): quote matching, text extraction and outcome classification.

The local HTTP server tests exercise the real fetcher over a real socket on 127.0.0.1
(no external network). The taxonomy-scale tests use the real taxonomy with a fake fetcher, to prove that
missing quotes and blocked sources are reported and never counted as verified.
"""

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from abyss.core.contracts import RetrievalOutcome, RetrievalRecord
from abyss.foundation import fetch as fetch_mod
from abyss.foundation.citations import verify_citations
from abyss.foundation.fetch import FetchResult, extract_text, find_quote, html_to_text, http_fetch, normalize, text_quality
from abyss.foundation.registry import load_registry
from abyss.foundation.taxonomy import load_taxonomy


# ------------------------------------------------------------------ pure functions

def test_html_to_text_drops_scripts_and_separates_blocks():
    html = "<html><head><style>x{}</style><script>ignore me</script></head><body><p>Alpha</p><p>Beta</p></body></html>"
    t = html_to_text(html)
    assert "ignore me" not in t and "x{}" not in t
    assert "Alpha" in t and "Beta" in t and "AlphaBeta" not in t


def test_normalize_handles_typography():
    assert normalize("Alice’s “garlic” message – OK") == "alice's \"garlic\" message - ok"
    assert normalize("soft­hyphen") == "softhyphen"


def test_find_quote_modes():
    text = normalize("Hyphanet is peer-to-peer network for privacy-respectingpublishing and communication.")
    assert find_quote(text, "peer-to-peer network") == "exact_normalized"
    assert find_quote(text, "privacy-respecting publishing") == "whitespace_insensitive"
    assert find_quote(text, "Hyphanet was invented in 1975") is None


def test_extract_text_html_and_plain():
    assert extract_text(b"<!doctype html><p>Hi there</p>", "text/html")[1] == "html"
    assert extract_text(b"Plain RFC text", "text/plain") == ("Plain RFC text", "text")


def test_garbage_pdf_text_is_unextractable(monkeypatch):
    monkeypatch.setattr(fetch_mod, "_pdf_text_pypdf", lambda b: "ÃÓÙæ­" * 500)
    monkeypatch.setattr(fetch_mod, "_pdf_text_pdftotext", lambda b: None)
    assert extract_text(b"%PDF-1.4 fake", "application/pdf") == ("", "none")
    assert text_quality("ordinary readable text, (with) punctuation.") > 0.95


# ------------------------------------------------------------- real socket, local server

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        routes = {"/ok": (200, b"<html><p>The Internet Gopher Protocol</p></html>"), "/429": (429, b"slow down"),
                  "/403": (403, b"no"), "/500": (500, b"boom"), "/big": (200, b"x" * 5000)}
        code, body = routes.get(self.path, (404, b"missing"))
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_fetch_ok_records_hash(server):
    r = http_fetch("local", server + "/ok")
    assert r.record.outcome is RetrievalOutcome.OK and r.record.http_status == 200
    assert r.record.sha256 == hashlib.sha256(r.body).hexdigest()


@pytest.mark.parametrize("path,outcome", [("/429", RetrievalOutcome.RATE_LIMITED), ("/403", RetrievalOutcome.BLOCKED),
                                          ("/500", RetrievalOutcome.FETCH_FAILED), ("/nope", RetrievalOutcome.FETCH_FAILED)])
def test_fetch_failures_are_classified_not_raised(server, path, outcome):
    r = http_fetch("local", server + path)
    assert r.record.outcome is outcome and r.record.error


def test_fetch_byte_cap(server):
    assert http_fetch("local", server + "/big", max_bytes=1000).record.outcome is RetrievalOutcome.FETCH_FAILED
    r = http_fetch("local", server + "/big", max_bytes=1000, allow_truncation=True)
    assert r.record.outcome is RetrievalOutcome.OK and r.record.truncated and len(r.body) == 1000


def test_fetch_connection_refused_is_reported():
    r = http_fetch("local", "http://127.0.0.1:9/", timeout=3)
    assert r.record.outcome is RetrievalOutcome.FETCH_FAILED and r.record.error


# ---------------------------------------------------- taxonomy-scale outcome accounting

@pytest.fixture(scope="module")
def tax_and_reg():
    return load_taxonomy(), load_registry()


def _fake_fetcher(loaded, omit_quotes_for=(), blocked=(), rate_limited=()):
    quotes = {}
    for _, _, c in loaded.taxonomy.iter_citations():
        quotes.setdefault(c.ref, []).append(c.quote)

    def fetcher(source_id, uri):
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        if source_id in blocked:
            return FetchResult(RetrievalRecord(source_id=source_id, uri=uri, retrieved_at=now,
                                               outcome=RetrievalOutcome.BLOCKED, http_status=403, error="HTTP 403"))
        if source_id in rate_limited:
            return FetchResult(RetrievalRecord(source_id=source_id, uri=uri, retrieved_at=now,
                                               outcome=RetrievalOutcome.RATE_LIMITED, http_status=429, error="HTTP 429"))
        body = ("unrelated text" if source_id in omit_quotes_for else " | ".join(quotes[source_id])).encode()
        return FetchResult(RetrievalRecord(source_id=source_id, uri=uri, retrieved_at=now, outcome=RetrievalOutcome.OK,
                                           http_status=200, content_type="text/plain", bytes=len(body),
                                           sha256=hashlib.sha256(body).hexdigest()), body)

    return fetcher


def test_all_quotes_present_means_all_verified(tax_and_reg):
    loaded, reg = tax_and_reg
    rep = verify_citations(loaded, reg, fetcher=_fake_fetcher(loaded))
    assert rep["summary"]["citations_by_outcome"] == {"VERIFIED": rep["summary"]["citations_total"]}


def test_missing_quotes_blocked_and_rate_limited_are_never_counted_as_verified(tax_and_reg):
    loaded, reg = tax_and_reg
    rep = verify_citations(loaded, reg, fetcher=_fake_fetcher(loaded, omit_quotes_for={"rfc1436"},
                                                              blocked={"tor_history"}, rate_limited={"gemini_faq"}))
    by = rep["summary"]["citations_by_outcome"]
    n = lambda ref: sum(1 for _, _, c in loaded.taxonomy.iter_citations() if c.ref == ref)  # noqa: E731
    assert by["QUOTE_NOT_FOUND"] == n("rfc1436")
    assert by["SOURCE_BLOCKED"] == n("tor_history")
    assert by["SOURCE_RATE_LIMITED"] == n("gemini_faq")
    assert by["VERIFIED"] == rep["summary"]["citations_total"] - n("rfc1436") - n("tor_history") - n("gemini_faq")


def test_report_records_inputs_and_environment(tax_and_reg):
    loaded, reg = tax_and_reg
    rep = verify_citations(loaded, reg, fetcher=_fake_fetcher(loaded))
    assert rep["inputs"]["taxonomy"]["sha256"] == loaded.sha256
    assert {"python", "platform", "git_commit"} <= set(rep["environment"])
    assert len(rep["retrievals"]) == len({c.ref for _, _, c in loaded.taxonomy.iter_citations()})
