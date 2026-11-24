# Operations manual — private pilot

This runs a **private pilot**: one server you control, a few invited people. It is not a public
deployment (no TLS termination, backups, monitoring or published policies yet — see STATUS.md).

## 1. Start the server (any machine with Docker)
```bash
git clone <this repo> && cd Project-abyss
cp infra/.env.example infra/.env          # edit: set three long random passwords
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
curl http://localhost:8000/health/ready   # {"status":"ok","checks":{"database":"ok","schema":"ok"},...}
```
Services: `db` (PostgreSQL 18.7, data in the `threadhall_dbdata` volume), `migrate` (applies
migrations then exits), `api` (port 8000). The API waits for migrations to succeed.

On a network that intercepts TLS (corporate proxy), build with the proxy's CA bundle:
`docker build --secret id=extra_ca,src=/path/ca-bundle.crt -t threadhall-server:dev server/`, then
`docker compose ... up -d --no-build`. The CA is used for the pip step only and is not stored in the image.

## 2. Connect a phone
1. Find the server machine's LAN address (e.g. `192.168.1.20`). Allow inbound TCP 8000 in its firewall.
2. Install the pilot APK (see §5). On first launch enter `http://192.168.1.20:8000` and tap Connect.
3. The red banner means the connection is unencrypted. Use this only on a network you trust.
   For anything beyond your home network, put the API behind HTTPS (e.g. Caddy with a real domain,
   or a private tunnel) and enter the `https://` address instead.
4. Profile → Sign in or create account. Accounts exist only on your server.

Emulator: use `http://10.0.2.2:8000`.

## 3. Day-to-day
| Task | Command |
|---|---|
| Status | `docker compose -f infra/docker-compose.yml --env-file infra/.env ps` |
| Logs (JSON lines) | `... logs -f api` |
| Restart | `... restart api` (state is in PostgreSQL; restarts are safe) |
| Stop (keep data) | `... down` |
| **Delete all data** | `... down -v` (irreversible) |
| Upgrade | `git pull && ... up -d --build` (migrations run automatically first) |
| Manual backup | `docker exec threadhall-db-1 pg_dump -U postgres -Fc threadhall > backup-$(date +%F).dump` |
| Restore (empty DB) | `docker exec -i threadhall-db-1 pg_restore -U postgres -d threadhall --clean --if-exists < backup.dump` |

Backups above are manual and unencrypted; automated encrypted backups with a tested restore drill are
a Phase 6 gate (T22). Keep dumps somewhere private — they contain password hashes and all content.

## 4. Verify a deployment end to end
```bash
python3 tests/e2e/two_accounts.py seed   --base http://localhost:8000 --state /tmp/e2e.json
docker compose -f infra/docker-compose.yml --env-file infra/.env restart db api
python3 tests/e2e/two_accounts.py verify --base http://localhost:8000 --state /tmp/e2e.json
```
This creates two clearly named `e2e_*` test accounts and a community on the target server; run it on
a pilot or staging server, not on a public one.

## 5. Android builds
Requirements: JDK 17+ (21 tested), Android SDK with platform `android-37.2` and build-tools 37.0.0.
```bash
cd android
./gradlew :app:assembleDebug        # pilot APK: app/build/outputs/apk/debug/app-debug.apk
sha256sum app/build/outputs/apk/debug/app-debug.apk
LIVE_BASE_URL=http://localhost:8000 ./gradlew :core:test :app:testDebugUnitTest   # incl. live tests
```
Install: `adb install -r app-debug.apk`, or copy the file to the phone and open it (allow "install
unknown apps" for your file manager). Pilot builds from any machine share the pilot key, so they
update each other in place.

**Release build (owner only):** create a private key once and keep it outside the repository:
```bash
keytool -genkeypair -keystore ~/threadhall-release.jks -alias release -keyalg RSA -keysize 4096 -validity 10000
THREADHALL_KEYSTORE=~/threadhall-release.jks THREADHALL_KEYSTORE_PASSWORD=... \
THREADHALL_KEY_ALIAS=release THREADHALL_KEY_PASSWORD=... ./gradlew :app:assembleRelease
```
Release builds are HTTPS-only. Losing the release key means users cannot receive updates.

## 6. Configuration (environment variables for `api`)
| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | set by compose | runtime role (DML only) |
| `ACCESS_TOKEN_TTL_SECONDS` | 900 | access token lifetime |
| `REFRESH_TOKEN_TTL_SECONDS` | 2592000 | refresh token lifetime (30 days) |
| `AUTH_RATE_LIMIT_PER_MINUTE` | 20 | login/register per IP and per handle |
| `WRITE_RATE_LIMIT_PER_MINUTE` | 60 | posts/comments/joins per account (votes: 3×) |
| `COMMUNITY_CREATE_PER_HOUR` | 5 | new communities per account |
| `TRUST_PROXY_HEADERS` | false | set true only behind your own reverse proxy |
| `LOG_LEVEL` | INFO | |

## 7. Recovery
- API unhealthy: `logs api`; `/health/ready` reports `database` and `schema` separately.
- Schema mismatch after an upgrade: `... run --rm migrate`, then `restart api`.
- Lost admin access: there is no admin UI yet; database access is the recovery path.
- Phone shows "Your session ended": the session was revoked or expired; sign in again.
