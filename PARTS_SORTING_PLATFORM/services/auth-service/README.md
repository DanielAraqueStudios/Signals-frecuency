# auth-service

Owns user accounts and issues JWTs (RS256). Other services verify tokens
with the public key from `GET /public-key` — they never touch the users
table or the private key.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | none | `{email, password}` -> 201 + user (no token yet — log in after) |
| POST | `/login` | none | `{email, password}` -> access + refresh JWT pair |
| POST | `/refresh` | none | `{refresh_token}` -> a new access + refresh pair |
| GET | `/public-key` | none | RS256 public key, for other services to verify tokens locally |
| GET | `/healthz` | none | liveness check (used by Railway) |

Access tokens expire in 15 minutes, refresh tokens in 30 days (both
configurable via `JWT_ACCESS_TOKEN_MINUTES` / `JWT_REFRESH_TOKEN_DAYS`).

## Local setup

```bash
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

# Generate a dev RSA keypair (never commit the private key):
openssl genrsa -out /tmp/private.pem 2048
openssl rsa -in /tmp/private.pem -pubout -out /tmp/public.pem

# Point the service at Postgres (or leave DATABASE_URL unset in
# docker-compose, which provides one) and the keypair:
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/parts_sorting
export JWT_PRIVATE_KEY="$(cat /tmp/private.pem)"
export JWT_PUBLIC_KEY="$(cat /tmp/public.pem)"

uvicorn app.main:app --reload
```

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

7 tests, all passing — register/login/refresh round-trip and the failure
paths (duplicate email, wrong password, unknown email, refresh-token-only
enforcement on `/refresh`). Tests use an in-memory SQLite DB and a
freshly-generated RSA keypair per test session, so they need no external
Postgres and never touch real secrets.

**Known dependency pin:** `passlib==1.7.4` is incompatible with `bcrypt`
5.x (missing `bcrypt.__about__`, breaks every password hash/verify call
with a hidden `ValueError`) — `bcrypt` is pinned to `4.0.1` in
`requirements.txt` to avoid this; don't bump it without re-testing.
