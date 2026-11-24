"""T06 new/top/hot/controversial ordering with deterministic fixtures, cursor pagination without
duplicates in a static snapshot, home vs all scoping. T26 (server part): normal feed by default."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from app.ranking import controversy, hot_rank

BASE = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def _force(engine, post_id: str, *, created_at: datetime, up: int = 0, down: int = 0) -> None:
    """Deterministic fixture state: set timestamp and vote counters, recomputing ranks with the
    production formulas (synthetic data; no fake accounts are created)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE posts SET created_at=:c, upvotes=:u, downvotes=:d, score=:s, hot_rank=:h, controversy=:x "
                "WHERE id=:i"
            ),
            {
                "c": created_at,
                "u": up,
                "d": down,
                "s": up - down,
                "h": hot_rank(up - down, created_at),
                "x": controversy(up, down),
                "i": post_id,
            },
        )


def _walk(api, path, params, page_size):
    seen, cursor, pages = [], None, 0
    while True:
        q = dict(params, limit=page_size) | ({"cursor": cursor} if cursor else {})
        r = api.get(path, params=q)
        assert r.status_code == 200, r.text
        body = r.json()
        seen += [p["id"] for p in body["items"]]
        cursor, pages = body["next_cursor"], pages + 1
        if not cursor:
            return seen, pages


def test_ranking_formulas():
    assert hot_rank(0, BASE) < hot_rank(10, BASE) < hot_rank(100, BASE)
    assert hot_rank(-10, BASE) < hot_rank(0, BASE)
    # 12.5 hours newer ≈ one order of magnitude of score.
    assert abs(hot_rank(1, BASE + timedelta(seconds=45000)) - hot_rank(10, BASE)) < 1e-6
    assert controversy(10, 0) == 0 and controversy(0, 10) == 0
    assert controversy(10, 10) == 20 and controversy(10, 10) > controversy(15, 5) > controversy(19, 1)


def test_sort_orders_are_deterministic(make_user, migrator_engine):
    a = make_user("feed_owner")
    a.community("feed_comm")
    ids = {name: a.text_post("feed_comm", name)["id"] for name in ("old_top", "new_low", "mid_contro", "fresh")}
    _force(migrator_engine, ids["old_top"], created_at=BASE - timedelta(days=3), up=500)
    _force(migrator_engine, ids["new_low"], created_at=BASE - timedelta(hours=2), up=1)
    _force(migrator_engine, ids["mid_contro"], created_at=BASE - timedelta(hours=5), up=40, down=38)
    _force(migrator_engine, ids["fresh"], created_at=BASE - timedelta(minutes=10))

    def order(sort, t="all"):
        items = a.get("/v1/communities/feed_comm/posts", params={"sort": sort, "t": t}).json()["items"]
        return [next(k for k, v in ids.items() if v == p["id"]) for p in items]

    assert order("new") == ["fresh", "new_low", "mid_contro", "old_top"]
    assert order("top") == ["old_top", "mid_contro", "new_low", "fresh"]
    assert order("controversial")[0] == "mid_contro"
    # hot-v1: log10(score) is worth 12.5h of age. mid_contro (score 2, 5h old) ≈ 1.24h effective age;
    # old_top (score 500, 72h old) ≈ 38h effective age; score 1 adds nothing (log10(1) = 0).
    assert order("hot") == ["fresh", "mid_contro", "new_low", "old_top"]
    page = a.get("/v1/feed", params={"scope": "all", "sort": "hot"}).json()
    assert page["ranking_version"] == "hot-v1" and page["time_window"] == "all"


def test_top_time_window_excludes_older_posts(make_user, migrator_engine):
    a = make_user("window_owner")
    a.community("window_comm")
    now = datetime.now(UTC)
    recent = a.text_post("window_comm", "recent")["id"]
    old = a.text_post("window_comm", "old")["id"]
    _force(migrator_engine, recent, created_at=now - timedelta(hours=3), up=5)
    _force(migrator_engine, old, created_at=now - timedelta(days=10), up=50)
    day = [
        p["id"] for p in a.get("/v1/communities/window_comm/posts", params={"sort": "top", "t": "day"}).json()["items"]
    ]
    month = [
        p["id"]
        for p in a.get("/v1/communities/window_comm/posts", params={"sort": "top", "t": "month"}).json()["items"]
    ]
    assert day == [recent] and month == [old, recent]


def test_pagination_has_no_duplicates_or_gaps(make_user, migrator_engine):
    a = make_user("pager")
    a.community("pager_comm")
    ids = []
    for i in range(37):
        pid = a.text_post("pager_comm", f"p{i}")["id"]
        # Many ties on score and timestamp to exercise the id tie-break.
        _force(migrator_engine, pid, created_at=BASE - timedelta(minutes=i // 4), up=i % 5, down=i % 3)
        ids.append(pid)
    for sort in ("new", "hot", "top", "controversial"):
        params = {"sort": sort, "t": "all"}
        full = [
            p["id"] for p in a.get("/v1/communities/pager_comm/posts", params=params | {"limit": 100}).json()["items"]
        ]
        paged, pages = _walk(a, "/v1/communities/pager_comm/posts", params, 6)
        assert paged == full, sort
        assert len(paged) == 37 and len(set(paged)) == 37 and pages == 7, sort


def test_cursor_snapshot_excludes_posts_created_after_first_page(make_user):
    a = make_user("snap_user")
    a.community("snap_comm")
    for i in range(5):
        a.text_post("snap_comm", f"s{i}")
    first = a.get("/v1/communities/snap_comm/posts", params={"sort": "hot", "limit": 2}).json()
    late = a.text_post("snap_comm", "late arrival")["id"]
    rest, _ = [], first["next_cursor"]
    cursor = first["next_cursor"]
    while cursor:
        page = a.get("/v1/communities/snap_comm/posts", params={"sort": "hot", "limit": 2, "cursor": cursor}).json()
        rest += [p["id"] for p in page["items"]]
        cursor = page["next_cursor"]
    seen = [p["id"] for p in first["items"]] + rest
    assert late not in seen and len(seen) == 5 == len(set(seen))


def test_tampered_or_mismatched_cursor_is_rejected(make_user):
    a = make_user("cursor_user")
    a.community("cursor_comm")
    for i in range(3):
        a.text_post("cursor_comm", f"c{i}")
    page = a.get("/v1/communities/cursor_comm/posts", params={"sort": "new", "limit": 1}).json()
    good = page["next_cursor"]
    # A cursor is bound to its sort/scope.
    r = a.get("/v1/communities/cursor_comm/posts", params={"sort": "top", "cursor": good})
    assert r.status_code == 422
    for bad in ("garbage", "eyJrIjoxfQ", "e30", "x" * 600):
        r = a.get("/v1/communities/cursor_comm/posts", params={"sort": "new", "cursor": bad})
        assert r.status_code == 422, bad
    import base64
    import json

    forged = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "k": "posts:hot:all:c/cursor_comm",
                    "v": "DROP TABLE",
                    "id": page["items"][0]["id"],
                    "at": "2026-01-01T00:00:00+00:00",
                }
            ).encode()
        )
        .decode()
        .rstrip("=")
    )
    assert a.get("/v1/communities/cursor_comm/posts", params={"sort": "hot", "cursor": forged}).status_code == 422


def test_home_is_subscriptions_and_all_is_everything(make_user, client):
    a, b = make_user("home_a"), make_user("home_b")
    a.community("home_one")
    b.community("home_two")
    p1 = a.text_post("home_one", "in one")["id"]
    p2 = b.text_post("home_two", "in two")["id"]

    def ids(api, scope):
        return {p["id"] for p in api.get("/v1/feed", params={"scope": scope, "sort": "new"}).json()["items"]}

    assert ids(a, "home") == {p1} and ids(b, "home") == {p2}
    assert ids(a, "all") == ids(b, "all") == {p1, p2}
    b.put("/v1/communities/home_one/membership")
    assert ids(b, "home") == {p1, p2}
    anon = client.get("/v1/feed").json()
    assert anon["scope"] == "all" and {p["id"] for p in anon["items"]} == {p1, p2}
    assert all(p["my_vote"] == 0 for p in anon["items"])


def test_user_posts_listing(make_user):
    a = make_user("lister")
    a.community("lister_comm")
    ids = [a.text_post("lister_comm", f"u{i}")["id"] for i in range(3)]
    got = [p["id"] for p in a.get("/v1/users/lister/posts").json()["items"]]
    assert got == list(reversed(ids))
    assert a.get("/v1/users/nobody_xyz/posts").status_code == 404
