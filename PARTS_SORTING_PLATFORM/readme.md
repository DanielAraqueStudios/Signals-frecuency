# Parts-Sorting Platform

A parts-identification system: a worker photographs a small hardware
part (bolt, screw, nut, washer, ...) and it's classified by type using
**frequency-spectrum extraction** (2D FFT of the image -- no ML model,
see [`shared/spectrum_classifier.py`](shared/spectrum_classifier.py)).
Identification/logging only for now, no physical sorting. See
[`docs/architecture.md`](docs/architecture.md) for the full data flow.

## Two independent deployment modes

This is not one architecture with an optional flag -- it's **two
separate, independently runnable deployments** that happen to share the
classifier module:

- **[`CLOUD_MODE/`](CLOUD_MODE/)** -- Railway-hosted: JWT auth
  (`auth-service`), image storage, and MQTT/TLS delivery to a paired
  ESP32-S3 (`mqtt-broker`). Multi-user, secured. See
  [`CLOUD_MODE/`](CLOUD_MODE/) for its own quickstart.
- **[`LOCAL_MODE/`](LOCAL_MODE/)** -- a closed WiFi LAN: phone, ESP32, and
  a "computer" (`local-server`) all join the same predefined access
  point. No auth, no TLS, no MQTT -- plain, **explicitly unsecured**
  HTTP with a GET/PUT-only API. Single-user, demo/lab use. See
  [`LOCAL_MODE/local-server/README.md`](LOCAL_MODE/local-server/README.md).

## Project structure

```
PARTS_SORTING_PLATFORM/
├── shared/spectrum_classifier.py   Frequency-spectrum classifier, used by BOTH modes
├── CLOUD_MODE/
│   ├── auth-service/                JWT auth (register/login/refresh, RS256)
│   ├── api-gateway/                  Image upload, history, device pairing
│   ├── classification-service/       Calls shared/ classifier + MQTT publish
│   ├── mqtt-broker/                  Mosquitto, TLS-only, per-device ACLs
│   ├── firmware/esp32s3_result_display/  MQTTS subscriber
│   ├── docker-compose.yml, scripts/, .dev-secrets/, deployment-railway.md
├── LOCAL_MODE/
│   ├── local-server/                 FastAPI: PUT/GET HTTP, calls shared/ classifier
│   └── firmware/esp32_local_http/    HTTP-polling ESP32 firmware
├── mobile-app/                       Expo/React Native: works with either mode
├── docs/architecture.md
└── readme.md                         (this file)
```

Each subfolder has its own README with exact endpoints, env vars, and
what was actually verified vs. not.

## Quickstart — cloud mode (local dev, before deploying to Railway)

```bash
cd PARTS_SORTING_PLATFORM/CLOUD_MODE
bash scripts/gen-dev-certs.sh      # TLS certs + classification-service's MQTT password
bash scripts/gen-dev-jwt-keys.sh   # RSA keypair for JWT signing/verification
docker compose up --build
```

See [`CLOUD_MODE/deployment-railway.md`](CLOUD_MODE/deployment-railway.md)
for the actual Railway setup.

## Quickstart — local mode

```bash
cd PARTS_SORTING_PLATFORM/LOCAL_MODE/local-server
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

```bash
# from another machine on the same WiFi access point:
curl -X PUT --data-binary @sample.jpg http://<local-server-ip>:8100/images/test1
curl http://<local-server-ip>:8100/images/latest
```

Flash `LOCAL_MODE/firmware/esp32_local_http/` to an ESP32 on the same
network (edit its `WIFI_SSID`/`WIFI_PASSWORD`/`LOCAL_SERVER_HOST`
constants first).

For the mobile app: `cd mobile-app && npm install && npx expo start` (see
its own README for env vars; it can target either mode's API).

## Current state, stated plainly

- **No reference spectrum profiles are calibrated yet, in either mode.**
  Both `CLOUD_MODE/classification-service` and `LOCAL_MODE/local-server`
  run in explicit stub mode (`"stub": true` in every response) until a
  handful of reference photos per part type are captured and averaged
  into each mode's `model/labels_config.json`. See either service's
  `model/README.md` for the (lightweight, non-ML) calibration process.
- **This replaced an earlier ONNX/CNN-based design.** There is no ML
  model, no training pipeline, and no labeled-dataset requirement in this
  version -- classification is a deterministic FFT feature extraction,
  matched against reference profiles. See git history for the old
  approach if needed.
- **Cloud mode's auth/MQTT pieces are unchanged from before** -- only
  `classification-service`'s internals (ONNX -> frequency-spectrum) and
  its folder location (`services/` -> `CLOUD_MODE/`) changed.
- **`LOCAL_MODE` is new** and was tested with `pytest` against the
  FastAPI app directly (`LOCAL_MODE/local-server/tests/`, all passing) --
  not yet run against real phone/ESP32 hardware on an actual access
  point.
- **Firmware (both sketches) is not compiled or flashed** -- no Arduino
  IDE/arduino-cli or physical ESP32 hardware was available. See each
  firmware README's "What could not be verified" section.
- **Mobile app is type-checked and dependency-verified, not run on a
  device/simulator.**
