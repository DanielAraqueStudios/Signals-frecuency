# Deploying to Railway

Five things get deployed as separate Railway services from this one
repo, each pointed at its own subfolder as the build root (Railway
project settings -> service -> Settings -> "Root Directory"):

| Service | Root directory | Builder |
|---|---|---|
| auth-service | `PARTS_SORTING_PLATFORM/services/auth-service` | Dockerfile |
| api-gateway | `PARTS_SORTING_PLATFORM/services/api-gateway` | Dockerfile |
| classification-service | `PARTS_SORTING_PLATFORM/services/classification-service` | Dockerfile |
| mqtt-broker | `PARTS_SORTING_PLATFORM/mqtt-broker` | Dockerfile |
| (mobile-app is not deployed to Railway — it's distributed via Expo/app stores, or run with `expo start` for dev) |

Each already has a `railway.toml` documenting its own required env vars —
this doc is the cross-service wiring.

## 1. Postgres

Add Railway's Postgres plugin once, shared by `auth-service` and
`api-gateway` (each with its own schema/tables — no table name
collisions, see their `app/models.py`). Railway injects `DATABASE_URL`
automatically into any service you attach the plugin to.

## 2. RSA keypair for JWT (auth-service <-> everyone else)

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
```

Set `JWT_PRIVATE_KEY` (full PEM contents) on `auth-service` only. Set
`JWT_PUBLIC_KEY` (the public PEM) on `api-gateway` — or leave it unset
there and let it fetch `GET {AUTH_SERVICE_URL}/public-key` at startup
instead (see `api-gateway/app/main.py`); either works, setting it
directly avoids a startup-order dependency.

## 3. Private networking between services

Railway gives every service a private `*.railway.internal` hostname
reachable from other services in the same project, with no public
internet hop. Set:
- `api-gateway`'s `AUTH_SERVICE_URL` -> auth-service's internal URL
- `api-gateway`'s `CLASSIFICATION_SERVICE_URL` -> classification-service's internal URL
- `api-gateway`'s `MQTT_BROKER_HOST` -> mqtt-broker's internal hostname
- `classification-service`'s `MQTT_BROKER_HOST` -> same

## 4. mqtt-broker: TLS is not HTTP

Railway's default public domain is HTTP(S)-only. MQTT needs a **TCP
Proxy** instead: service Settings -> Networking -> "TCP Proxy", pointed
at container port 8883. Railway gives you a `<host>:<port>` pair — that's
what the ESP32-S3 firmware's `MQTT_HOST`/`MQTT_PORT` should point at, and
what a real (not self-signed) TLS certificate needs to be issued for.

**Certs and the password file**: `mqtt-broker` needs `certs/ca.crt`,
`certs/server.crt`, `certs/server.key`, and `config/passwd` present at
`/mosquitto/certs` and `/mosquitto/config` respectively. Provision a
Railway **Volume** mounted at `/mosquitto`, and populate it once (e.g.
`railway run` a shell against the service, or upload via `railway
volume`) with real certs — never self-signed dev ones — obtained from a
real CA (Let's Encrypt via a domain you control, or your own internal CA
if every ESP32-S3 is provisioned with a matching custom root).

`api-gateway` needs write access to that same `config/passwd` file (see
its `MQTT_PASSWD_FILE_PATH`) to provision new devices — mount the same
Railway Volume on `api-gateway` too, at a path matching that env var.
Remember the stated limitation: `mqtt-broker` needs restarting after new
credentials are written (see `services/api-gateway/README.md`).

## 5. S3-compatible storage for images

Railway has no built-in object storage. Use any S3-compatible provider
(Cloudflare R2 and Backblaze B2 are the cheapest for this workload) and
set `api-gateway`'s `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`,
`S3_BUCKET`.

## 6. classification-service compute tier

No GPU tier on Railway — pick the largest CPU/RAM plan you're willing to
pay for; the ONNX Runtime + INT8-quantized model this service runs is
built for CPU inference (see its README). If you outgrow that, the
documented (not built) upgrade path is swapping this service's compute
backend for a GPU host (Modal, RunPod, Cloud Run+GPU) behind the same
`POST /classify` contract — `api-gateway` doesn't need to change either
way.

## 7. Health checks

Every Python service exposes `GET /healthz` — already wired into each
`railway.toml`. `mqtt-broker` has no HTTP health check (it's a raw TCP
service); Railway's TCP Proxy handles liveness by connection success.
