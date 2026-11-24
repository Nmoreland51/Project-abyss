"""T04 two accounts post/comment, visible in feed/thread. T07 deep threads, wrong parent, edit/delete.
Idempotent creation, input handling (parts of T16)."""

import concurrent.futures
import uuid

import httpx2
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


def _setup(make_user):
    a, b = make_user("ann_t04"), make_user("ben_t04")
    a.community("t04_comm")
    assert b.put("/v1/communities/t04_comm/membership").status_code == 200
    return a, b


def test_two_accounts_post_comment_reply_and_see_each_other(make_user):
    a, b = _setup(make_user)
    post = b.text_post("t04_comm", "Hello from Ben", "first body")
    assert post["author"]["handle"] == "ben_t04" and post["origin"] == "local" and post["score"] == 0
    top = a.comment(post["id"], "Welcome, Ben!")
    reply = b.comment(post["id"], "Thanks Ann", parent_id=top["id"])
    assert reply["depth"] == 1 and reply["parent_id"] == top["id"]

    home_a = a.get("/v1/feed", params={"scope": "home", "sort": "new"}).json()
    assert [p["id"] for p in home_a["items"]] == [post["id"]]
    assert home_a["items"][0]["comment_count"] == 2

    thread = b.get(f"/v1/posts/{post['id']}/comments").json()["items"]
    assert len(thread) == 1 and thread[0]["author"]["handle"] == "ann_t04"
    assert thread[0]["reply_count"] == 1 and thread[0]["replies"][0]["body"] == "Thanks Ann"
    assert thread[0]["more_replies"] == 0


def test_link_post_validation(make_user):
    a, _ = _setup(make_user)
    bad = [
        "javascript:alert(1)",
        "ftp://example.com/file",
        "https://user:pass@example.com/",
        "https://",
        "https://exa mple.com",
        "data:text/html;base64,PHNjcmlwdD4=",
    ]
    for url in bad:
        r = a.post("/v1/posts", json={"community": "t04_comm", "kind": "link", "title": "x", "url": url})
        assert r.status_code == 422, url
    ok = a.post(
        "/v1/posts",
        json={"community": "t04_comm", "kind": "link", "title": "A link", "url": "https://www.example.org/a?b=c"},
    )
    assert ok.status_code == 201 and ok.json()["url_domain"] == "example.org"
    r = a.post("/v1/posts", json={"community": "t04_comm", "kind": "text", "title": "t", "url": "https://x.org"})
    assert r.status_code == 422
    r = a.post("/v1/posts", json={"community": "t04_comm", "kind": "link", "title": "t"})
    assert r.status_code == 422


def test_title_and_body_normalisation(make_user):
    a, _ = _setup(make_user)
    p = a.text_post("t04_comm", "  Multi\n line \t title  ", "keep\r\nnewlines\x00‮")
    assert p["title"] == "Multi line title" and p["body"] == "keep\nnewlines"
    r = a.post("/v1/posts", json={"community": "t04_comm", "title": "   "})
    assert r.status_code == 422
    r = a.post("/v1/posts", json={"community": "t04_comm", "title": "x" * 301})
    assert r.status_code == 422
    r = a.post("/v1/posts", json={"community": "t04_comm", "title": "ok", "score": 1000})
    assert r.status_code == 422  # unknown fields are rejected, clients cannot set server fields


def test_markup_is_stored_as_text_not_rendered(make_user):
    a, _ = _setup(make_user)
    payload = "<script>alert('x')</script><img src=x onerror=alert(1)>"
    p = a.text_post("t04_comm", payload, payload)
    r = a.get(f"/v1/posts/{p['id']}")
    assert r.headers["content-type"].startswith("application/json")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.json()["title"] == payload  # returned verbatim as JSON data; clients render as text


def test_wrong_and_missing_parent_rejected(make_user, migrator_engine):
    a, b = _setup(make_user)
    p1 = a.text_post("t04_comm", "post one")
    p2 = a.text_post("t04_comm", "post two")
    c1 = b.comment(p1["id"], "on post one")
    r = b.post(f"/v1/posts/{p2['id']}/comments", json={"body": "cross", "parent_id": c1["id"]})
    assert r.status_code == 422 and r.json()["error"]["details"][0]["field"] == "parent_id"
    r = b.post(f"/v1/posts/{p1['id']}/comments", json={"body": "ghost", "parent_id": str(uuid.uuid4())})
    assert r.status_code == 422
    # The database itself rejects a cross-post parent even if application checks were bypassed.
    with migrator_engine.begin() as conn:
        try:
            conn.execute(
                text("INSERT INTO comments (id, post_id, parent_id, body, depth) VALUES (:i, :p, :par, 'x', 1)"),
                {"i": str(uuid.uuid4()), "p": p2["id"], "par": c1["id"]},
            )
            raise AssertionError("cross-post parent accepted by database")
        except IntegrityError:
            pass


def test_deep_thread_is_bounded_and_continuable(make_user):
    a, b = _setup(make_user)
    post = a.text_post("t04_comm", "deep")
    parent = None
    chain = []
    for i in range(20):
        author = a if i % 2 == 0 else b
        node = author.comment(post["id"], f"level {i}", parent_id=parent)
        assert node["depth"] == i
        chain.append(node["id"])
        parent = node["id"]
    page = a.get(f"/v1/posts/{post['id']}/comments", params={"depth": 5}).json()
    node, levels = page["items"][0], 1
    while node["replies"]:
        node = node["replies"][0]
        levels += 1
    assert levels == 6  # root + 5 reply levels
    assert node["more_replies"] == 1 and node["reply_count"] == 1
    cont = a.get(f"/v1/comments/{node['id']}", params={"depth": 15}).json()
    deepest = cont
    while deepest["replies"]:
        deepest = deepest["replies"][0]
    assert deepest["id"] == chain[-1] and deepest["body"] == "level 19"


def test_comment_pagination_covers_all_roots_once(make_user):
    a, b = _setup(make_user)
    post = a.text_post("t04_comm", "many comments")
    ids = {b.comment(post["id"], f"c{i}")["id"] for i in range(23)}
    for sort in ("new", "old", "top"):
        seen, cursor = [], None
        while True:
            params = {"sort": sort, "limit": 10} | ({"cursor": cursor} if cursor else {})
            page = a.get(f"/v1/posts/{post['id']}/comments", params=params).json()
            seen += [c["id"] for c in page["items"]]
            cursor = page["next_cursor"]
            if not cursor:
                break
        assert len(seen) == 23 and set(seen) == ids, sort
    old = a.get(f"/v1/posts/{post['id']}/comments", params={"sort": "old", "limit": 100}).json()["items"]
    assert [c["body"] for c in old] == [f"c{i}" for i in range(23)]


def test_edit_and_delete_permissions(make_user, migrator_engine):
    a, b = _setup(make_user)
    post = b.text_post("t04_comm", "editable", "v1")
    c = b.comment(post["id"], "comment v1")
    child = a.comment(post["id"], "child", parent_id=c["id"])

    assert a.patch(f"/v1/posts/{post['id']}", json={"body": "hacked"}).status_code == 403
    assert a.patch(f"/v1/comments/{c['id']}", json={"body": "hacked"}).status_code == 403
    r = b.patch(f"/v1/posts/{post['id']}", json={"body": "v2"})
    assert r.status_code == 200 and r.json()["body"] == "v2" and r.json()["edited_at"]
    r = b.patch(f"/v1/comments/{c['id']}", json={"body": "comment v2"})
    assert r.status_code == 200 and r.json()["edited_at"]

    # Author deletes comment: placeholder keeps thread structure; replying to it is refused.
    assert b.delete(f"/v1/comments/{c['id']}").status_code == 204
    tree = a.get(f"/v1/posts/{post['id']}/comments").json()["items"][0]
    assert tree["state"] == "deleted" and tree["body"] == "[deleted]" and tree["author"] is None
    assert tree["replies"][0]["id"] == child["id"]
    r = a.post(f"/v1/posts/{post['id']}/comments", json={"body": "late", "parent_id": c["id"]})
    assert r.status_code == 409

    # Non-moderator cannot delete someone else's content.
    stranger = make_user("stranger_t07")
    assert stranger.delete(f"/v1/posts/{post['id']}").status_code == 403
    # Community owner (a) removes the post as moderator: audited, redacted, gone from feeds.
    assert a.delete(f"/v1/posts/{post['id']}", params={"reason": "off topic"}).status_code == 204
    got = stranger.get(f"/v1/posts/{post['id']}").json()
    assert got["state"] == "removed" and got["title"] == "[removed]" and got["body"] is None
    assert got["author"] is None
    feed_ids = [p["id"] for p in stranger.get("/v1/feed", params={"scope": "all", "sort": "new"}).json()["items"]]
    assert post["id"] not in feed_ids
    with migrator_engine.connect() as conn:
        action = conn.execute(text("SELECT action, reason FROM moderation_actions")).one()
    assert tuple(action) == ("remove_post", "off topic")
    assert b.post(f"/v1/posts/{post['id']}/comments", json={"body": "x"}).status_code == 409
    assert b.put(f"/v1/posts/{post['id']}/vote", json={"value": 1}).status_code == 409


def test_idempotent_post_creation(make_user, migrator_engine):
    a, _ = _setup(make_user)
    key = {"Idempotency-Key": "client-key-000001"}
    body = {"community": "t04_comm", "title": "only once", "body": "b"}
    r1 = a.post("/v1/posts", json=body, headers=key)
    r2 = a.post("/v1/posts", json=body, headers=key)
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"] and r2.headers.get("idempotent-replayed") == "true"
    r3 = a.post("/v1/posts", json=body | {"title": "different"}, headers=key)
    assert r3.status_code == 409 and r3.json()["error"]["code"] == "idempotency_key_reused"
    with migrator_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM posts WHERE title='only once'")).scalar() == 1
    # A failed request (validation error) does not burn the key.
    k2 = {"Idempotency-Key": "client-key-000002"}
    assert a.post("/v1/posts", json=body | {"community": "nope_none"}, headers=k2).status_code == 404
    assert a.post("/v1/posts", json=body | {"title": "second"}, headers=k2).status_code == 201


def test_idempotent_comment_under_concurrent_retries(make_user, live_server, migrator_engine):
    a, b = _setup(make_user)
    post = a.text_post("t04_comm", "concurrent comments")
    headers = {**b.headers, "Idempotency-Key": "retry-storm-0001"}
    url = f"{live_server}/v1/posts/{post['id']}/comments"

    def send(_):
        with httpx2.Client(timeout=30) as http:
            return http.post(url, json={"body": "exactly one"}, headers=headers)

    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        results = list(pool.map(send, range(8)))
    assert all(r.status_code == 201 for r in results), [r.text for r in results]
    assert len({r.json()["id"] for r in results}) == 1
    with migrator_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM comments WHERE body='exactly one'")).scalar() == 1
        assert conn.execute(text("SELECT comment_count FROM posts WHERE id=:i"), {"i": post["id"]}).scalar() == 1


def test_anonymous_write_endpoints_require_auth(client, make_user):
    a, _ = _setup(make_user)
    post = a.text_post("t04_comm", "anon target")
    c = a.comment(post["id"], "anon comment")
    pid, cid = post["id"], c["id"]
    calls = [
        ("post", "/v1/posts", {"community": "t04_comm", "title": "x"}),
        ("patch", f"/v1/posts/{pid}", {"body": "x"}),
        ("delete", f"/v1/posts/{pid}", None),
        ("post", f"/v1/posts/{pid}/comments", {"body": "x"}),
        ("patch", f"/v1/comments/{cid}", {"body": "x"}),
        ("delete", f"/v1/comments/{cid}", None),
        ("put", f"/v1/posts/{pid}/vote", {"value": 1}),
        ("put", f"/v1/comments/{cid}/vote", {"value": 1}),
        ("patch", "/v1/me", {"bio": "x"}),
        ("post", "/v1/auth/logout", None),
    ]
    for method, path, body in calls:
        kwargs = {"json": body} if body is not None else {}
        r = getattr(client, method)(path, **kwargs)
        assert r.status_code == 401, (method, path, r.status_code)
    # Anonymous reads of public content work (R01).
    assert client.get(f"/v1/posts/{pid}").status_code == 200
    assert client.get(f"/v1/posts/{pid}/comments").status_code == 200
    assert client.get("/v1/feed").json()["scope"] == "all"
