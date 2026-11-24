"""T15 unauthorized cross-account writes and mod actions; T16 injection / oversized input (partial;
the full T16 review including SSRF and Markdown rendering is a Phase 5/6 gate)."""

from sqlalchemy import text


def test_cross_account_writes_are_rejected_without_side_effects(make_user, migrator_engine):
    owner, intruder = make_user("sec_owner"), make_user("sec_intruder")
    owner.community("sec_comm")
    post = owner.text_post("sec_comm", "owner post", "original")
    comment = owner.comment(post["id"], "owner comment")
    attempts = [
        intruder.patch(f"/v1/posts/{post['id']}", json={"body": "pwned"}),
        intruder.patch(f"/v1/posts/{post['id']}", json={"flair": "pwned"}),
        intruder.delete(f"/v1/posts/{post['id']}"),
        intruder.patch(f"/v1/comments/{comment['id']}", json={"body": "pwned"}),
        intruder.delete(f"/v1/comments/{comment['id']}"),
        intruder.patch("/v1/communities/sec_comm", json={"description": "pwned"}),
        intruder.put("/v1/communities/sec_comm/moderators/sec_intruder"),
        intruder.delete("/v1/communities/sec_comm/moderators/sec_owner"),
    ]
    assert [r.status_code for r in attempts] == [403] * len(attempts)
    with migrator_engine.connect() as conn:
        assert conn.execute(text("SELECT body, flair, state FROM posts")).one() == ("original", None, "visible")
        assert conn.execute(text("SELECT body, state FROM comments")).one() == ("owner comment", "visible")
        assert conn.execute(text("SELECT description FROM communities")).scalar() == ""
        assert conn.execute(text("SELECT count(*) FROM memberships WHERE role <> 'member'")).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM moderation_actions")).scalar() == 0


def test_moderation_is_scoped_to_own_community(make_user):
    mod_a, user_b = make_user("scope_mod_a"), make_user("scope_user_b")
    mod_a.community("scope_a")
    user_b.community("scope_b")
    victim = user_b.text_post("scope_b", "in b")
    # Owner of community A has no moderator power in community B.
    assert mod_a.delete(f"/v1/posts/{victim['id']}").status_code == 403
    assert mod_a.patch(f"/v1/posts/{victim['id']}", json={"flair": "x"}).status_code == 403


def test_injection_strings_are_inert(make_user, client):
    a = make_user("inject_user")
    a.community("inject_comm")
    payloads = ["' OR 1=1 --", "x'; DROP TABLE users; --", "%' UNION SELECT password_hash FROM users --"]
    for p in payloads:
        assert client.get("/v1/communities", params={"q": p}).json()["items"] == []
        r = client.get(f"/v1/users/{p}")
        assert r.status_code in (404, 422), r.status_code
        post = a.text_post("inject_comm", p, p)
        assert a.get(f"/v1/posts/{post['id']}").json()["body"] == p
    assert client.get("/v1/users/inject_user").status_code == 200  # users table intact


def test_oversized_body_is_rejected(make_user):
    a = make_user("big_body")
    a.community("big_comm")
    r = a.post("/v1/posts", json={"community": "big_comm", "title": "t", "body": "x" * 300_000})
    assert r.status_code == 413 and r.json()["error"]["code"] == "payload_too_large"
    r = a.post("/v1/posts", json={"community": "big_comm", "title": "t", "body": "x" * 40_001})
    assert r.status_code == 422


def test_error_responses_do_not_leak_internals(client):
    r = client.post("/v1/auth/login", json={"handle": "x" * 41, "password": "y"})
    assert r.status_code == 422
    blob = r.text.lower()
    for needle in ("traceback", "sqlalchemy", "psycopg", "select ", "password_hash"):
        assert needle not in blob
