# ADR-0002 Authentication and sessions

Status: accepted (Phase 1) · Date: 2026-11-24

## Decision
- **Accounts are local.** No import of passwords or identities from any other service (R02, A03).
- **Passwords:** Argon2id via `argon2-cffi` defaults (RFC 9106 profile); rehash on login when
  parameters change. Unknown handles are verified against a dummy hash to equalise timing.
- **Tokens:** opaque 256-bit random strings (`at_…` access, `rt_…` refresh). Only SHA-256 digests
  are stored (`sessions.access_hash`, `refresh_hash`); a database leak does not yield usable tokens.
  Opaque tokens make revocation immediate (no JWT denylist needed).
- **Lifetimes:** access 15 minutes, refresh 30 days from last rotation (configurable).
- **Rotation:** every refresh issues a new access *and* refresh token on the same session row.
- **Reuse detection:** presenting a previous refresh token more than **30 s** after rotation revokes
  the whole session (theft signal). Within 30 s it rotates again — this tolerates a mobile client
  whose refresh response was lost in transit. Trade-off: a stolen previous token is usable for at
  most 30 s after a rotation, and only if the thief races the legitimate client.
- **Client:** the Android client serialises refreshes with a mutex, retries the original call once,
  clears local tokens and signs out only when the server rejects the refresh with 401 (never when
  offline). Tokens are AES-256-GCM encrypted with a non-exportable Android Keystore key and excluded
  from backups/device transfer.
- **Sessions:** users can list sessions and revoke any of their own (`/v1/me/sessions`). Logout
  revokes the current session server-side.
- **Rate limits:** 20/min per IP and per handle on register/login (in-process, single node).

## Not yet done (tracked in STATUS.md)
Password recovery (needs an owner decision on email or another channel: OD-09), account deletion and
export (Phase 5), 2FA, distributed rate limiting (Phase 6 reverse proxy).
