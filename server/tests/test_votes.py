"""T05 concurrent vote retries and reversal: one vote per user/target, correct score and karma."""

import concurrent.futures

import httpx2
from sqlalchemy import text


def _reconcile(engine) -> list[str]:
    """Return a list of inconsistencies between stored counters and vote rows (empty = consistent)."""
    problems = []
    with engine.connect() as conn:
        for table, vt, fk in (("posts", "post_votes", "post_id"), ("comments", "comment_votes", "comment_id")):
            rows = conn.execute(
                text(
                    f"SELECT t.id, t.upvotes, t.downvotes, t.score, "
                    f"coalesce(sum(CASE WHEN v.value = 1 THEN 1 END), 0) AS up, "
                    f"coalesce(sum(CASE WHEN v.value = -1 THEN 1 END), 0) AS down "
                    f"FROM {table} t LEFT JOIN {vt} v ON v.{fk} = t.id GROUP BY t.id"
                )
            ).all()
            for r in rows:
                if (r.upvotes, r.downvotes, r.score) != (r.up, r.down, r.up - r.down):
                    problems.append(f"{table} {r.id}: stored {r.upvotes}/{r.downvotes} actual {r.up}/{r.down}")
        karma = conn.execute(
            text(
                """
                SELECT u.handle, u.post_karma, u.comment_karma,
                  coalesce((SELECT sum(v.value) FROM post_votes v JOIN posts p ON p.id = v.post_id
                            WHERE p.author_id = u.id AND v.user_id <> u.id), 0) AS pk,
                  coalesce((SELECT sum(v.value) FROM comment_votes v JOIN comments c ON c.id = v.comment_id
                            WHERE c.author_id = u.id AND v.user_id <> u.id), 0) AS ck
                FROM users u
                """
            )
        ).all()
        for r in karma:
            if (r.post_karma, r.comment_karma) != (r.pk, r.ck):
                problems.append(f"karma {r.handle}: stored {r.post_karma}/{r.comment_karma} actual {r.pk}/{r.ck}")
    return problems


def test_vote_state_transitions_and_karma(make_user, migrator_engine):
    author, voter = make_user("v_author"), make_user("v_voter")
    author.community("votes_comm")
    post = author.text_post("votes_comm", "vote me")
    assert voter.vote_post(post["id"], 1) == {"target_id": post["id"], "score": 1, "my_vote": 1}
    assert voter.vote_post(post["id"], 1)["score"] == 1  # retry: unchanged
    assert author.get("/v1/me").json()["post_karma"] == 1
    assert voter.vote_post(post["id"], -1)["score"] == -1  # reversal
    assert author.get("/v1/me").json()["post_karma"] == -1
    assert voter.vote_post(post["id"], 0)["score"] == 0  # neutral removes the row
    with migrator_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM post_votes")).scalar() == 0
    assert author.get("/v1/me").json()["post_karma"] == 0
    # Self-votes count toward score but never toward karma.
    assert author.vote_post(post["id"], 1)["score"] == 1
    assert author.get("/v1/me").json()["post_karma"] == 0
    assert voter.get(f"/v1/posts/{post['id']}").json()["my_vote"] == 0
    assert author.get(f"/v1/posts/{post['id']}").json()["my_vote"] == 1
    assert voter.put(f"/v1/posts/{post['id']}/vote", json={"value": 2}).status_code == 422
    assert _reconcile(migrator_engine) == []


def test_comment_votes_and_karma(make_user, migrator_engine):
    a, b = make_user("cv_a"), make_user("cv_b")
    a.community("cv_comm")
    post = a.text_post("cv_comm", "p")
    c = b.comment(post["id"], "vote my comment")
    r = a.put(f"/v1/comments/{c['id']}/vote", json={"value": 1})
    assert r.status_code == 200 and r.json()["score"] == 1
    me = b.get("/v1/me").json()
    assert (me["comment_karma"], me["post_karma"]) == (1, 0)
    tree = a.get(f"/v1/posts/{post['id']}/comments").json()["items"]
    assert tree[0]["my_vote"] == 1 and tree[0]["score"] == 1
    assert _reconcile(migrator_engine) == []


def test_concurrent_votes_from_many_users_and_retry_storms(make_user, live_server, migrator_engine):
    author = make_user("cc_author")
    author.community("cc_comm")
    post = author.text_post("cc_comm", "popular")
    voters = [make_user(f"cc_v{i:02d}") for i in range(12)]
    url = f"{live_server}/v1/posts/{post['id']}/vote"

    def vote(args):
        token, value = args
        with httpx2.Client(timeout=30) as http:
            r = http.put(url, json={"value": value}, headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 200, r.text
            return r.json()

    # Each voter sends the same upvote 4 times concurrently (retry storm), all voters at once.
    jobs = [(v.tokens["access_token"], 1) for v in voters for _ in range(4)]
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        list(pool.map(vote, jobs))
    with migrator_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM post_votes")).scalar() == 12
        assert conn.execute(text("SELECT score FROM posts")).scalar() == 12
    assert author.get("/v1/me").json()["post_karma"] == 12

    # Half reverse to downvote concurrently, a quarter go neutral.
    jobs = [(v.tokens["access_token"], -1) for v in voters[:6]] * 3 + [
        (v.tokens["access_token"], 0) for v in voters[6:9]
    ] * 3
    with concurrent.futures.ThreadPoolExecutor(16) as pool:
        list(pool.map(vote, jobs))
    final = author.get(f"/v1/posts/{post['id']}").json()["score"]
    assert final == 3 - 6  # 3 remaining up, 6 down, 3 neutral
    assert author.get("/v1/me").json()["post_karma"] == -3
    assert _reconcile(migrator_engine) == []
