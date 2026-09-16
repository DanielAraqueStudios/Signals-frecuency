# api-gateway

The only service the phone app talks to directly. Verifies JWTs issued by
`auth-service` (RS256, locally — no per-request callback), accepts
authenticated photo uploads, forwards them to `classification-service`,
stores the image + result, and issues MQTT credentials to paired
ESP32-S3 devices.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/images` | Bearer JWT | multipart `image` file (+ optional `device_id` form field) -> classifies, stores, returns the result |
| GET | `/images` | Bearer JWT | the caller's own capture history, newest first |
| POST | `/devices/pair` | Bearer JWT | mints a new ESP32-S3 MQTT credential owned by the caller |
| GET | `/healthz` | none | liveness check |

`device_id` is optional on upload — a worker can classify a photo with no
paired device nearby; the result then just isn't echoed to any ESP32-S3
over MQTT. If given, it must be a device the *caller* owns (404 otherwise
— this is where user↔device ownership is actually enforced; see
`../../mqtt-broker/README.md` for why it's deliberately not in the MQTT
topic itself).

## Local setup

```bash
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/parts_sorting
export JWT_PUBLIC_KEY="$(cat /tmp/public.pem)"   # must match auth-service's keypair
export AUTH_SERVICE_URL=http://localhost:8001
export CLASSIFICATION_SERVICE_URL=http://localhost:8002
export S3_ENDPOINT_URL=http://localhost:9000     # e.g. a local MinIO container
export S3_ACCESS_KEY=minioadmin
export S3_SECRET_KEY=minioadmin
export MQTT_PASSWD_FILE_PATH=../../mqtt-broker/config/passwd  # same file mqtt-broker mounts

uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

9 tests, all passing. `auth-service`, `classification-service`, S3, and
the MQTT broker are all mocked/stubbed — these tests exercise this
service's own logic (auth enforcement, ownership checks, DB writes,
response shapes) in isolation, not a full integration path. The full
integration path (real Postgres + MinIO + the other two services + the
real broker) is what `docker-compose.yml` at the project root is for.

**Real bug found and fixed while building this:** `Header(...)` (FastAPI's
required-header shortcut) makes a *missing* `Authorization` header return
422 before any application code runs — so an unauthenticated request
never reached this service's own 401 logic. Fixed by making the header
`Header(default=None)` and checking for `None` explicitly in
`app/deps.py::verify_access_token`, so a missing header, a malformed one,
and an invalid token all consistently return 401.

**Real cross-service bug found and fixed after both services were
independently "done":** this service was posting the uploaded photo to
`classification-service` under multipart field name `image` and omitting
`topic` entirely when no device was paired — but `classification-service`
expected field name `file` and required `topic`, meaning every
no-device upload would have 422'd against a real classification-service
instance (invisible in this service's own tests, since they mock the
HTTP call). Fixed on both sides — see
`../classification-service/README.md` for the matching note — and caught
precisely because both services were re-tested together, not just in
isolation.

## MQTT credential provisioning — a real limitation, stated plainly

`app/mqtt_credentials.py` writes new device credentials straight into the
Mosquitto password file Mosquitto itself reads at startup. That format
(PBKDF2-HMAC-SHA512, `$7$101$<salt>$<hash>`) was verified against a real
Mosquitto 2.0.22 broker during development — a device paired this way
does authenticate correctly. **But** Mosquitto's file-based auth only
re-reads that file on restart/SIGHUP, so a freshly-paired device cannot
connect until `mqtt-broker` is restarted (`docker compose restart
mqtt-broker` in dev). This is documented, not hidden — see
`../../mqtt-broker/README.md` for the recommended production fix
(Mosquitto's dynamic-security plugin), which is not built here.
