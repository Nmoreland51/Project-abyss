"""Minimal, bounded HTTP retrieval and text extraction (stdlib only, plus optional pypdf).

Retrieved content is untrusted data. It is hashed, converted to text and string-matched.
Nothing here interprets, executes or follows instructions found in it (R09/T12).
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Callable, Optional
from urllib.parse import urlparse

from .. import __version__
from ..core.contracts import RetrievalOutcome, RetrievalRecord

USER_AGENT = f"ProjectAbyss-research/{__version__} (evidence verification; local research prototype)"
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_TIMEOUT = 45.0


@dataclass(frozen=True)
class FetchResult:
    record: RetrievalRecord
    body: bytes = b""


Fetcher = Callable[[str, str], FetchResult]  # (source_id, uri) -> FetchResult


def _ssl_context() -> ssl.SSLContext:
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if cafile and os.path.exists(cafile):
        return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


class _HostPacer:
    """At most one request per host per `interval` seconds (politeness / rate-limit control)."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._last: dict[str, float] = {}

    def wait(self, uri: str) -> None:
        host = urlparse(uri).hostname or ""
        now = time.monotonic()
        last = self._last.get(host)
        if last is not None and now - last < self.interval:
            time.sleep(self.interval - (now - last))
        self._last[host] = time.monotonic()


_PACER = _HostPacer()


def http_fetch(
    source_id: str,
    uri: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout: float = DEFAULT_TIMEOUT,
    allow_truncation: bool = False,
) -> FetchResult:
    """GET `uri` with a byte cap. Always returns a RetrievalRecord; never raises for network errors."""
    _PACER.wait(uri)
    started = datetime.now(timezone.utc)
    t0 = time.monotonic()
    req = urllib.request.Request(uri, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    status: Optional[int] = None
    ctype: Optional[str] = None

    def rec(outcome: RetrievalOutcome, **kw) -> RetrievalRecord:
        return RetrievalRecord(
            source_id=source_id, uri=uri, retrieved_at=started, outcome=outcome,
            http_status=status, content_type=ctype,
            elapsed_ms=int((time.monotonic() - t0) * 1000), **kw,
        )

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            status = resp.status
            ctype = resp.headers.get("Content-Type")
            body = resp.read(max_bytes + 1)
            truncated = len(body) > max_bytes
            if truncated:
                body = body[:max_bytes]
                if not allow_truncation:
                    return FetchResult(rec(RetrievalOutcome.FETCH_FAILED, bytes=len(body), truncated=True,
                                           sha256=hashlib.sha256(body).hexdigest(),
                                           error=f"response exceeded max_bytes={max_bytes}"))
            return FetchResult(
                rec(RetrievalOutcome.OK, bytes=len(body), truncated=truncated, sha256=hashlib.sha256(body).hexdigest()),
                body,
            )
    except urllib.error.HTTPError as e:
        status = e.code
        ctype = e.headers.get("Content-Type") if e.headers else None
        if e.code == 429:
            return FetchResult(rec(RetrievalOutcome.RATE_LIMITED, error=f"HTTP 429 {e.reason}"))
        if e.code in (401, 403, 407, 451):
            return FetchResult(rec(RetrievalOutcome.BLOCKED, error=f"HTTP {e.code} {e.reason} (origin or egress policy)"))
        return FetchResult(rec(RetrievalOutcome.FETCH_FAILED, error=f"HTTP {e.code} {e.reason}"))
    except urllib.error.URLError as e:
        msg = str(e.reason)
        if re.search(r"Tunnel connection failed: (403|407)", msg):
            return FetchResult(rec(RetrievalOutcome.BLOCKED, error=f"egress proxy refused CONNECT: {msg}"))
        return FetchResult(rec(RetrievalOutcome.FETCH_FAILED, error=f"URLError: {msg}"))
    except (TimeoutError, ConnectionError, OSError) as e:  # resets, timeouts, TLS errors
        return FetchResult(rec(RetrievalOutcome.FETCH_FAILED, error=f"{type(e).__name__}: {e}"))


# ----------------------------------------------------------------- text extraction

_BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table", "h1", "h2", "h3", "h4", "h5", "h6",
    "section", "article", "header", "footer", "nav", "pre", "blockquote", "dd", "dt", "dl", "hr", "main", "aside",
}
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1
        elif tag in _BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    p.close()
    return "".join(p.parts)


def _pdf_text_pypdf(body: bytes) -> Optional[str]:
    try:
        import pypdf  # optional dependency
    except ImportError:
        return None
    try:
        reader = pypdf.PdfReader(io.BytesIO(body))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:  # malformed PDFs are data errors, not crashes
        return None


def _pdf_text_pdftotext(body: bytes) -> Optional[str]:
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "in.pdf")
        with open(src, "wb") as fh:
            fh.write(body)
        try:
            out = subprocess.run([exe, "-q", src, "-"], capture_output=True, timeout=120, check=False)
        except (subprocess.TimeoutExpired, OSError):
            return None
        return out.stdout.decode("utf-8", "replace") if out.returncode == 0 else None


_READABLE = re.compile(r"[A-Za-z0-9\s.,;:'\"()\[\]/\-]")


def text_quality(text: str) -> float:
    """Fraction of characters that are ordinary readable Latin text. Low = encoding garbage."""
    sample = text[:20000]
    if not sample:
        return 0.0
    return len(_READABLE.findall(sample)) / len(sample)


def extract_text(body: bytes, content_type: Optional[str]) -> tuple[str, str]:
    """Return (text, method). method is 'none' if no usable text could be extracted."""
    ctype = (content_type or "").lower()
    if body[:5] == b"%PDF-" or "application/pdf" in ctype:
        candidates = [("pypdf", _pdf_text_pypdf(body)), ("pdftotext", _pdf_text_pdftotext(body))]
        best = max(
            ((m, t) for m, t in candidates if t),
            key=lambda mt: (text_quality(mt[1]) > 0.85, len(mt[1])),
            default=None,
        )
        if best is None or text_quality(best[1]) < 0.85:
            return "", "none"
        return best[1], best[0]
    text = body.decode("utf-8", "replace")
    head = text[:3000].lower()
    if "html" in ctype or "<html" in head or "<!doctype html" in head:
        return html_to_text(text), "html"
    return text, "text"


# ----------------------------------------------------------------- quote matching

_TRANSLATE = str.maketrans(
    {
        "‘": "'", "’": "'", "‚": "'", "‛": "'",
        "“": '"', "”": '"', "„": '"',
        "–": "-", "—": "-", "−": "-", "‐": "-", "‑": "-",
        " ": " ", "­": None, "​": None, "﻿": None,
    }
)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(_TRANSLATE)
    return re.sub(r"\s+", " ", s).strip().casefold()


def find_quote(normalized_text: str, quote: str) -> Optional[str]:
    """Return the match mode if `quote` occurs in the (already normalized) text, else None."""
    q = normalize(quote)
    if q in normalized_text:
        return "exact_normalized"
    # HTML pages sometimes glue adjacent inline elements together without whitespace.
    if q.replace(" ", "") in normalized_text.replace(" ", ""):
        return "whitespace_insensitive"
    return None
