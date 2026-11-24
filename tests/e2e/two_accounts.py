#!/usr/bin/env python3
"""End-to-end check against a RUNNING server over real HTTP (no test client, no mocks).

  python3 tests/e2e/two_accounts.py seed   --base http://localhost:8000 --state /tmp/e2e.json
  (restart the server and/or database)
  python3 tests/e2e/two_accounts.py verify --base http://localhost:8000 --state /tmp/e2e.json

`seed` registers two independent accounts, creates a community, posts, comments, replies and
votes from both. `verify` logs both accounts in again and checks every effect persisted.
Accounts are clearly labelled e2e test accounts on the target server; do not run against a
public deployment. Standard library only so it runs on any machine with Python 3.10+."""

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.token: str | None = None

    def call(self, method: str, path: str, body=None, headers=None, expect=(200, 201, 204)):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "threadhall-e2e/1")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status, raw = resp.status, resp.read()
        except urllib.error.HTTPError as err:
            status, raw = err.code, err.read()
        payload = json.loads(raw) if raw else None
        if status not in expect:
            raise AssertionError(f"{method} {path} -> {status}: {raw[:300]!r}")
        return payload

    def login(self, handle: str, password: str):
        out = self.call("POST", "/v1/auth/login", {"handle": handle, "password": password})
        self.token = out["tokens"]["access_token"]
        return out["user"]


def check(cond: bool, msg: str):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        raise SystemExit(1)


def seed(base: str, state_path: str):
    tag = secrets.token_hex(3)
    pw = "e2e-" + secrets.token_urlsafe(12)
    alice, bob = Client(base), Client(base)
    ha, hb = f"e2e_alice_{tag}", f"e2e_bob_{tag}"
    alice.token = alice.call("POST", "/v1/auth/register", {"handle": ha, "password": pw})["tokens"]["access_token"]
    bob.token = bob.call("POST", "/v1/auth/register", {"handle": hb, "password": pw})["tokens"]["access_token"]
    slug = f"e2e_{tag}"
    alice.call("POST", "/v1/communities", {"slug": slug, "display_name": f"E2E {tag}", "description": "e2e test"})
    bob.call("PUT", f"/v1/communities/{slug}/membership")
    post = bob.call(
        "POST",
        "/v1/posts",
        {"community": slug, "title": f"Bob's first post {tag}", "body": "Hello from Bob"},
        headers={"Idempotency-Key": f"e2e-post-{tag}"},
    )
    # Retry the same request: must not create a second post.
    again = bob.call(
        "POST",
        "/v1/posts",
        {"community": slug, "title": f"Bob's first post {tag}", "body": "Hello from Bob"},
        headers={"Idempotency-Key": f"e2e-post-{tag}"},
    )
    check(again["id"] == post["id"], "idempotent retry returned the same post")
    top = alice.call("POST", f"/v1/posts/{post['id']}/comments", {"body": "Welcome Bob — Alice here"})
    reply = bob.call("POST", f"/v1/posts/{post['id']}/comments", {"body": "Thanks Alice!", "parent_id": top["id"]})
    alice.call("PUT", f"/v1/posts/{post['id']}/vote", {"value": 1})
    bob.call("PUT", f"/v1/comments/{top['id']}/vote", {"value": 1})
    home = alice.call("GET", "/v1/feed?scope=home&sort=new")
    check(any(p["id"] == post["id"] for p in home["items"]), "Bob's post appears in Alice's home feed")
    state = {"base": base, "password": pw, "alice": ha, "bob": hb, "slug": slug,
             "post": post["id"], "top": top["id"], "reply": reply["id"]}
    with open(state_path, "w") as fh:
        json.dump(state, fh)
    print(f"seeded state -> {state_path}")


def verify(base: str, state_path: str):
    with open(state_path) as fh:
        s = json.load(fh)
    alice, bob, anon = Client(base), Client(base), Client(base)
    ready = anon.call("GET", "/health/ready")
    check(ready["status"] == "ok", f"server ready: {ready['checks']}")
    ua = alice.login(s["alice"], s["password"])
    ub = bob.login(s["bob"], s["password"])
    check(ua["comment_karma"] == 1, f"Alice comment karma persisted (=1, got {ua['comment_karma']})")
    check(ub["post_karma"] == 1, f"Bob post karma persisted (=1, got {ub['post_karma']})")
    post = alice.call("GET", f"/v1/posts/{s['post']}")
    check(post["score"] == 1 and post["my_vote"] == 1, "post score and Alice's vote persisted")
    check(post["comment_count"] == 2, "comment count persisted")
    check(post["author"]["handle"] == s["bob"], "post author is Bob's local account")
    thread = bob.call("GET", f"/v1/posts/{s['post']}/comments")["items"]
    check(len(thread) == 1 and thread[0]["id"] == s["top"], "top-level comment persisted")
    check(thread[0]["replies"][0]["id"] == s["reply"], "nested reply persisted under the right parent")
    check(thread[0]["my_vote"] == 1, "Bob's comment vote persisted")
    subs = {c["slug"] for c in bob.call("GET", "/v1/me/communities")}
    check(s["slug"] in subs, "Bob's subscription persisted")
    allfeed = anon.call("GET", "/v1/feed?scope=all&sort=new&limit=100")
    check(any(p["id"] == s["post"] for p in allfeed["items"]), "anonymous All feed shows the post")
    print("verify: all checks passed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["seed", "verify"])
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--state", default="e2e_state.json")
    args = ap.parse_args()
    (seed if args.mode == "seed" else verify)(args.base, args.state)


if __name__ == "__main__":
    sys.exit(main())
