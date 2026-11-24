"""Input normalisation and validation for user-supplied text and URLs.

The server stores Markdown/plain source text and never renders HTML. Clients must render as
text (or through a sanitising Markdown renderer). URLs are validated but never fetched by the
server (no SSRF surface)."""

import re
import unicodedata
from urllib.parse import urlsplit

from .errors import invalid

HANDLE_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
SLUG_RE = re.compile(r"^[a-z0-9_]{3,21}$")
_CONTROL_RE = re.compile("[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f\\u200b-\\u200f\\u202a-\\u202e\\u2066-\\u2069]")

RESERVED_HANDLES = {
    "admin",
    "administrator",
    "root",
    "system",
    "support",
    "moderator",
    "mod",
    "staff",
    "official",
    "deleted",
    "removed",
    "anonymous",
    "null",
    "undefined",
    "me",
    "api",
    "help",
}
RESERVED_SLUGS = {"all", "home", "popular", "mod", "admin", "api", "new", "top", "hot", "search", "settings"}


def clean_text(value: str | None, *, field: str, max_len: int, min_len: int = 0, multiline: bool = True) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = _CONTROL_RE.sub("", value)
    if not multiline:
        value = " ".join(value.split())
    value = value.strip()
    if len(value) < min_len:
        raise invalid(f"{field} must be at least {min_len} characters", field)
    if len(value) > max_len:
        raise invalid(f"{field} must be at most {max_len} characters", field)
    return value


def normalize_handle(handle: str) -> str:
    handle = unicodedata.normalize("NFKC", handle).strip()
    if not HANDLE_RE.fullmatch(handle):
        raise invalid("Handle must be 3-20 characters: letters, digits, '_' or '-'", "handle")
    return handle.lower()


def validate_new_handle(handle: str) -> tuple[str, str]:
    norm = normalize_handle(handle)
    if norm in RESERVED_HANDLES:
        raise invalid("That handle is reserved", "handle")
    return unicodedata.normalize("NFKC", handle).strip(), norm


def validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise invalid("Community name must be 3-21 characters: a-z, 0-9 or '_'", "slug")
    if slug in RESERVED_SLUGS:
        raise invalid("That community name is reserved", "slug")
    return slug


def validate_password(password: str, handle_norm: str) -> None:
    if len(password) < 10:
        raise invalid("Password must be at least 10 characters", "password")
    if len(password) > 256:
        raise invalid("Password must be at most 256 characters", "password")
    if handle_norm and handle_norm in password.lower():
        raise invalid("Password must not contain your handle", "password")


def validate_link(url: str) -> str:
    url = url.strip()
    if len(url) > 2048:
        raise invalid("URL is too long", "url")
    if _CONTROL_RE.search(url) or any(c.isspace() for c in url):
        raise invalid("URL contains invalid characters", "url")
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise invalid("URL is not valid", "url") from exc
    if parts.scheme.lower() not in ("http", "https"):
        raise invalid("Only http and https links are allowed", "url")
    if not parts.hostname or "." not in parts.hostname and parts.hostname != "localhost":
        raise invalid("URL must include a valid host", "url")
    if parts.username or parts.password:
        raise invalid("URLs with embedded credentials are not allowed", "url")
    return url


def url_domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlsplit(url).hostname or ""
    return host[4:] if host.startswith("www.") else host
