"""T02 register/login/logout/refresh; independent sessions; revocation. Part of T16 (token misuse)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.security import token_digest


def test_two_users_have_independent_sessions(make_user):
    a, b = make_user("alice_t02"), make_user("bob_t02")
    assert a.get("/v1/me").json()["handle"] == "alice_t02"
    assert b.get("/v1/me").json()["handle"] == "bob_t02"
    assert a.tokens["session_id"] != b.tokens["session_id"]
    assert a.post("/v1/auth/logout").status_code == 204
    assert a.get("/v1/me").status_code == 401
    assert b.get("/v1/me").status_code == 200  # other account unaffected


def test_duplicate_handle_is_case_insensitive(client, make_user):
    make_user("Carol_dup")
    r = client.post("/v1/auth/register", json={"handle": "carol_DUP", "password": "another-long-password"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "handle_taken"


def test_registration_validation(client):
    cases = [
        ({"handle": "ab", "password": "long-enough-pass"}, "handle"),
        ({"handle": "bad handle!", "password": "long-enough-pass"}, "handle"),
        ({"handle": "admin", "password": "long-enough-pass"}, "handle"),
        ({"handle": "dave_ok", "password": "short"}, "password"),
        ({"handle": "dave_ok", "password": "xx-dave_ok-xx-yy"}, "password"),
    ]
    for payload, field in cases:
        r = client.post("/v1/auth/register", json=payload)
        assert r.status_code == 422, (payload, r.text)
        assert r.json()["error"]["details"][0]["field"] == field


def test_login_failures_do_not_reveal_which_part_was_wrong(client, make_user):
    make_user("erin_login")
    wrong_pw = client.post("/v1/auth/login", json={"handle": "erin_login", "password": "not-the-password"})
    no_user = client.post("/v1/auth/login", json={"handle": "nobody_here", "password": "not-the-password"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["error"]["message"] == no_user.json()["error"]["message"]
    ok = client.post("/v1/auth/login", json={"handle": "ERIN_LOGIN", "password": "correct-horse-battery"})
    assert ok.status_code == 200 and ok.json()["user"]["handle"] == "erin_login"


def test_credentials_are_not_stored_in_plaintext(make_user, migrator_engine):
    a = make_user("frank_hash")
    with migrator_engine.connect() as conn:
        pw_hash = conn.execute(text("SELECT password_hash FROM users WHERE handle_norm='frank_hash'")).scalar()
        row = conn.execute(text("SELECT access_hash, refresh_hash FROM sessions")).one()
    assert pw_hash.startswith("$argon2id$")
    assert a.tokens["access_token"] not in row and a.tokens["refresh_token"] not in row
    assert row.access_hash == token_digest(a.tokens["access_token"])


def test_refresh_rotates_tokens_and_invalidates_old_access(client, make_user):
    a = make_user("gina_rot")
    old = dict(a.tokens)
    r = client.post("/v1/auth/refresh", json={"refresh_token": old["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != old["refresh_token"] and new["access_token"] != old["access_token"]
    assert new["session_id"] == old["session_id"]
    assert client.get("/v1/me", headers={"Authorization": f"Bearer {old['access_token']}"}).status_code == 401
    assert client.get("/v1/me", headers={"Authorization": f"Bearer {new['access_token']}"}).status_code == 200


def test_refresh_retry_within_grace_window_succeeds(client, make_user):
    """A lost refresh response: the client retries with the previous refresh token."""
    a = make_user("hank_grace")
    first = client.post("/v1/auth/refresh", json={"refresh_token": a.tokens["refresh_token"]})
    retry = client.post("/v1/auth/refresh", json={"refresh_token": a.tokens["refresh_token"]})
    assert first.status_code == 200 and retry.status_code == 200
    # The retry rotated again, so the first response's refresh token is now the "previous" one.
    latest = retry.json()
    assert client.get("/v1/me", headers={"Authorization": f"Bearer {latest['access_token']}"}).status_code == 200


def test_refresh_reuse_after_grace_revokes_session(client, make_user, migrator_engine):
    a = make_user("ivy_reuse")
    stolen = a.tokens["refresh_token"]
    rotated = client.post("/v1/auth/refresh", json={"refresh_token": stolen}).json()
    with migrator_engine.begin() as conn:
        conn.execute(text("UPDATE sessions SET rotated_at = now() - interval '5 minutes'"))
    replay = client.post("/v1/auth/refresh", json={"refresh_token": stolen})
    assert replay.status_code == 401
    # The whole session is revoked, including the legitimately rotated tokens.
    assert client.post("/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code == 401
    assert client.get("/v1/me", headers={"Authorization": f"Bearer {rotated['access_token']}"}).status_code == 401


def test_logout_revokes_refresh_token(client, make_user):
    a = make_user("jack_logout")
    refresh = a.tokens["refresh_token"]
    assert a.post("/v1/auth/logout").status_code == 204
    assert client.post("/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_expired_access_token_reports_token_expired(client, make_user, migrator_engine):
    a = make_user("kim_expiry")
    with migrator_engine.begin() as conn:
        conn.execute(
            text("UPDATE sessions SET access_expires_at = :t"), {"t": datetime.now(UTC) - timedelta(seconds=1)}
        )
    r = a.get("/v1/me")
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_expired"
    refreshed = client.post("/v1/auth/refresh", json={"refresh_token": a.tokens["refresh_token"]})
    assert refreshed.status_code == 200


def test_list_and_revoke_other_session(client, make_user):
    a = make_user("lena_devices")
    second = client.post("/v1/auth/login", json={"handle": "lena_devices", "password": a.password}).json()["tokens"]
    h2 = {"Authorization": f"Bearer {second['access_token']}"}
    sessions = client.get("/v1/me/sessions", headers=h2).json()
    assert len(sessions) == 2 and sum(s["current"] for s in sessions) == 1
    assert client.delete(f"/v1/me/sessions/{a.tokens['session_id']}", headers=h2).status_code == 204
    assert a.get("/v1/me").status_code == 401
    assert client.get("/v1/me", headers=h2).status_code == 200


def test_cannot_revoke_another_users_session(make_user):
    a, b = make_user("mia_owner"), make_user("ned_attacker")
    assert b.delete(f"/v1/me/sessions/{a.tokens['session_id']}").status_code == 404
    assert a.get("/v1/me").status_code == 200


def test_token_misuse(client, make_user):
    a = make_user("oli_tokens")
    bad = [
        {"Authorization": "Basic Zm9vOmJhcg=="},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer at_forged"},
        {"Authorization": f"Bearer {a.tokens['refresh_token']}"},  # refresh token is not an access token
    ]
    for h in bad:
        assert client.get("/v1/me", headers=h).status_code == 401, h


def test_suspended_account_is_rejected(make_user, migrator_engine, client):
    a = make_user("pat_suspended")
    with migrator_engine.begin() as conn:
        conn.execute(text("UPDATE users SET status='suspended' WHERE handle_norm='pat_suspended'"))
    assert a.get("/v1/me").status_code == 403
    r = client.post("/v1/auth/login", json={"handle": "pat_suspended", "password": a.password})
    assert r.status_code == 403


def test_profile_update_and_public_profile(make_user, client):
    a = make_user("quinn_prof")
    r = a.patch("/v1/me", json={"display_name": "  Quinn   Q  ", "bio": "hello\r\nworld"})
    assert r.status_code == 200
    assert r.json()["display_name"] == "Quinn Q" and r.json()["bio"] == "hello\nworld"
    pub = client.get("/v1/users/QUINN_PROF").json()
    assert pub["handle"] == "quinn_prof" and "is_admin" not in pub


def test_rate_limiter_blocks_after_limit():
    from app.errors import ApiError
    from app.ratelimit import SlidingWindowLimiter

    lim = SlidingWindowLimiter()
    for _ in range(3):
        lim.check("k", 3)
    try:
        lim.check("k", 3)
        raise AssertionError("limit not enforced")
    except ApiError as exc:
        assert exc.status == 429
