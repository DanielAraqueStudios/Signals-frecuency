# Parts-Sorting IoT Platform

An ESP32-S3 + MQTT/TLS parts-identification system: a worker logs into a
mobile app, photographs a small hardware part (bolt, screw, nut, washer,
...) on a conveyor belt, and the photo is classified by a backend
microservice — the result is shown to the worker and echoed to their
paired ESP32-S3 over MQTT/TLS. Identification/logging only for now, no
physical sorting. See [`docs/architecture.md`](docs/architecture.md) for
the full data flow and the design trade-offs made along the way.

## Project structure

```
PARTS_SORTING_PLATFORM/
├── services/
│   ├── auth-service/              JWT auth (register/login/refresh, RS256)
│   ├── api-gateway/                Image upload, history, device pairing — the only service the phone app talks to
│   └── classification-service/     ONNX Runtime inference (honest stub mode until a real model exists) + MQTT publish
├── mqtt-broker/                    Mosquitto, TLS-only, per-device ACLs
├── firmware/esp32s3_result_display/  Arduino sketch: MQTTS subscriber, displays/logs results
├── mobile-app/                     Expo/React Native: login, capture, history
├── docs/                           architecture.md, deployment-railway.md
├── scripts/                        gen-dev-certs.sh, gen-dev-jwt-keys.sh
└── docker-compose.yml              full local dev stack
```

Each subfolder has its own README with exact endpoints, env vars, and
what was actually verified vs. not — this file is just the index and
quickstart.

## Quickstart (local dev)

```bash
cd PARTS_SORTING_PLATFORM
bash scripts/gen-dev-certs.sh      # TLS certs + classification-service's MQTT password
bash scripts/gen-dev-jwt-keys.sh   # RSA keypair for JWT signing/verification
docker compose up --build
```

Then, in another terminal:

```bash
# Register + log in
curl -X POST http://localhost:8001/register -H "Content-Type: application/json" \
  -d '{"email":"worker@example.com","password":"hunter22"}'
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8001/login -H "Content-Type: application/json" \
  -d '{"email":"worker@example.com","password":"hunter22"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Pair a device (mints MQTT credentials — see services/api-gateway/README.md
# for why mqtt-broker needs a restart before a *new* device can connect)
curl -X POST http://localhost:8000/devices/pair -H "Authorization: Bearer $ACCESS_TOKEN"
docker compose restart mqtt-broker

# Classify a photo
curl -X POST http://localhost:8000/images -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "image=@some_part.jpg;type=image/jpeg"
```

For the mobile app: `cd mobile-app && npm install && npx expo start` (see
its own README for env vars).

**This exact flow — register, login, pair, upload, classify (stub mode),
store, and MQTT delivery to the paired device over TLS — was run
end-to-end against the real docker-compose stack while building this**,
not just unit-tested in isolation. See each service's README for its own
test suite and what it covers.

## Current state, stated plainly

- **All five pieces (3 backend services, firmware, mobile app) are built,
  individually tested, and were also run together as one working system**
  (see above). 30 backend unit/integration tests total, all passing, plus
  the live end-to-end run.
- **No labeled parts dataset exists yet**, so `classification-service`
  runs in an explicit stub mode — every response says `"stub": true`
  rather than pretending to classify for real. See
  `services/classification-service/model/README.md` for exactly what
  training a real model needs from you.
- **Firmware is not compiled or flashed** — no Arduino IDE/arduino-cli or
  physical ESP32-S3 was available while building it. See
  `firmware/esp32s3_result_display/README.md`'s "What could not be
  verified" section.
- **Mobile app is type-checked and dependency-verified, not run on a
  device/simulator** — none was available either. See
  `mobile-app/README.md`'s "What was actually verified" section.
- **New device credentials need a broker restart** to take effect (a
  file-based-auth limitation, not a bug) — documented in
  `services/api-gateway/README.md`, with the production upgrade path
  (Mosquitto's dynamic-security plugin) noted but not built.
- **No physical sorting/actuation** — the `commands/<device>` MQTT topic
  is reserved for it in the broker's ACL, but nothing uses it yet; this
  was explicitly out of scope for this round.

## Deployment

See [`docs/deployment-railway.md`](docs/deployment-railway.md) for the
full per-service Railway setup (Postgres plugin, RSA keypair injection,
private networking, MQTT's TCP Proxy requirement, S3-compatible storage,
and the CPU-only "most powerful configuration" note for
`classification-service`, since Railway has no GPU tier).
