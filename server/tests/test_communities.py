"""T03 community create/join, persistent memberships, role checks. Part of T15."""

from sqlalchemy import text


def test_create_makes_creator_owner_and_subscriber(make_user):
    a = make_user("owner_one")
    c = a.community("retro_games", description="Old games", rules=[{"title": "Be kind", "description": "x"}])
    assert c["membership"] == {"subscribed": True, "role": "owner"}
    assert c["subscriber_count"] == 1 and c["rules"][0]["title"] == "Be kind"
    mods = a.get("/v1/communities/retro_games/moderators").json()
    assert [(m["user"]["handle"], m["role"]) for m in mods] == [("owner_one", "owner")]


def test_slug_rules(make_user):
    a = make_user("slug_tester")
    for bad in ("ab", "has-dash", "UPPER CASE", "all", "x" * 22):
        r = a.post("/v1/communities", json={"slug": bad})
        assert r.status_code == 422, bad
    a.community("mixed_case")
    r = a.post("/v1/communities", json={"slug": "MIXED_CASE"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "slug_taken"


def test_subscribe_is_idempotent_and_persistent(make_user, migrator_engine):
    a, b = make_user("idem_owner"), make_user("idem_member")
    a.community("idem_comm")
    for _ in range(3):
        r = b.put("/v1/communities/idem_comm/membership")
        assert r.status_code == 200
    assert r.json()["subscriber_count"] == 2 and r.json()["membership"]["role"] == "member"
    with migrator_engine.connect() as conn:
        n = conn.execute(
            text(
                "SELECT count(*) FROM memberships m JOIN communities c ON c.id=m.community_id WHERE c.slug='idem_comm'"
            )
        ).scalar()
    assert n == 2
    for _ in range(2):
        r = b.delete("/v1/communities/idem_comm/membership")
        assert r.status_code == 200
    assert r.json()["subscriber_count"] == 1 and r.json()["membership"] is None
    assert [c["slug"] for c in b.get("/v1/me/communities").json()] == []
    assert [c["slug"] for c in a.get("/v1/me/communities").json()] == ["idem_comm"]


def test_owner_unsubscribe_keeps_role(make_user):
    a = make_user("keeps_role")
    a.community("role_kept")
    r = a.delete("/v1/communities/role_kept/membership")
    assert r.json()["membership"] == {"subscribed": False, "role": "owner"}
    assert r.json()["subscriber_count"] == 0
    assert a.patch("/v1/communities/role_kept", json={"description": "still mine"}).status_code == 200


def test_role_checks(make_user):
    owner, mod, member = make_user("rc_owner"), make_user("rc_mod"), make_user("rc_member")
    owner.community("roles_comm")
    member.put("/v1/communities/roles_comm/membership")

    assert member.patch("/v1/communities/roles_comm", json={"description": "hijack"}).status_code == 403
    assert member.put("/v1/communities/roles_comm/moderators/rc_member").status_code == 403

    assert owner.put("/v1/communities/roles_comm/moderators/rc_mod").status_code == 200
    assert mod.patch("/v1/communities/roles_comm", json={"description": "mod edit"}).status_code == 200
    # Moderators cannot appoint or remove moderators; only the owner can.
    assert mod.put("/v1/communities/roles_comm/moderators/rc_member").status_code == 403
    assert mod.delete("/v1/communities/roles_comm/moderators/rc_owner").status_code == 403
    # Owner role cannot be removed.
    r = owner.delete("/v1/communities/roles_comm/moderators/rc_owner")
    assert r.status_code == 409
    assert owner.delete("/v1/communities/roles_comm/moderators/rc_mod").status_code == 200
    assert mod.patch("/v1/communities/roles_comm", json={"description": "x"}).status_code == 403
    assert owner.put("/v1/communities/roles_comm/moderators/does_not_exist").status_code == 404


def test_anonymous_can_read_but_not_write(client, make_user):
    make_user("anon_seed").community("public_read")
    assert client.get("/v1/communities").status_code == 200
    assert client.get("/v1/communities/public_read").json()["membership"] is None
    assert client.post("/v1/communities", json={"slug": "nope_anon"}).status_code == 401
    assert client.put("/v1/communities/public_read/membership").status_code == 401


def test_browse_pagination_and_prefix(make_user):
    a = make_user("browser")
    for i in range(7):
        a.community(f"browse_{i}")
    seen, cursor = [], None
    while True:
        params = {"limit": 3} | ({"cursor": cursor} if cursor else {})
        page = a.get("/v1/communities", params=params).json()
        seen += [c["slug"] for c in page["items"]]
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert sorted(seen) == [f"browse_{i}" for i in range(7)] and len(seen) == len(set(seen))
    pref = a.get("/v1/communities", params={"q": "browse_1"}).json()["items"]
    assert [c["slug"] for c in pref] == ["browse_1"]
    # LIKE wildcards in the filter are treated literally.
    assert a.get("/v1/communities", params={"q": "%"}).json()["items"] == []


def test_unknown_community_is_404(client):
    assert client.get("/v1/communities/missing_comm").status_code == 404
    assert client.get("/v1/communities/missing_comm/posts").status_code == 404
