# classification-service

Classifies a photo of a part (bolt, screw, nut, washer, ...) by
**frequency-spectrum extraction** (`../../shared/spectrum_classifier.py`
-- 2D FFT of the grayscale image, radial energy-band features, nearest-
centroid match against reference profiles). No ML model. Publishes the
result as JSON to an MQTT/TLS topic so the owning ESP32-S3 sees it.
Called internally by `api-gateway`, not directly by the phone app -- see
`../../docs/architecture.md`. `LOCAL_MODE/local-server` uses the exact
same shared classifier module, without the MQTT/auth wrapping.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/healthz` | liveness check (used by Railway); also reports `stub_mode` |
| POST | `/classify` | multipart form: `file` (image), `topic` (MQTT topic string to publish the result to) -> classification JSON |

### `POST /classify` request/response

Request: `multipart/form-data` with fields `file` (the image) and `topic`
(e.g. `results/device-abc123`, matching `../../mqtt-broker/README.md`'s
topic scheme -- api-gateway passes this per-request; this service does
not need to know the userId or deviceId itself).

Response (same JSON is published to `topic`):

```json
{
  "label": "unclassified",
  "confidence": null,
  "stub": true,
  "reason": "no reference spectrum profiles configured",
  "features": null
}
```

Once real reference profiles are configured (see `model/README.md`),
`stub` is `false`, `confidence` is a heuristic `[0, 1]` distance-based
score, and `features` is the extracted `[low, mid, high]` radial-band
energy vector:

```json
{
  "label": "bolt",
  "confidence": 0.87,
  "stub": false,
  "reason": null,
  "features": [0.62, 0.28, 0.10]
}
```

If the MQTT publish fails (broker unreachable, bad credentials, etc.),
`/classify` still returns 200 with the classification result -- a
worker holding the phone should not see an error just because the
ESP32-S3 leg of the message failed. The failure is logged server-side.

## Stub mode

**No reference spectrum profiles exist yet.**
`shared/spectrum_classifier.SpectrumClassifier` checks
`model/labels_config.json` at startup; if no class has
`reference_features` (the current, placeholder state), every call to
`/classify` returns the stub response above -- never a fabricated label
dressed up as real. This mirrors the "pendiente" discipline this repo
already uses elsewhere (see `THEORY/` and `LAB_TESTING/LAB1/`) for
results that haven't actually been measured. Filling in real
`reference_features` per class turns stub mode off automatically, by
config content alone.

## Calibrating real reference profiles

See `model/README.md` for the full walkthrough: this is much lighter
than training an ML model -- a handful of reference photos per part
type, run through `shared.spectrum_classifier.extract_features()`,
averaged into a `[low, mid, high]` vector per class.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `LABELS_CONFIG_PATH` | `model/labels_config.json` | per-class reference spectrum profiles; stub mode if no class has `reference_features` |
| `MQTT_BROKER_HOST` | `localhost` | matches `../../mqtt-broker/` |
| `MQTT_BROKER_PORT` | `8883` | TLS listener |
| `MQTT_CA_CERT` | `../../mqtt-broker/certs/ca.crt` | file path, or the PEM contents directly (Railway env vars can't hold a file) |
| `MQTT_USERNAME` | `classification-service` | this service's own MQTT credential |
| `MQTT_PASSWORD` | *(empty)* | this service's own MQTT credential |

## Local setup

```bash
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Without `MQTT_PASSWORD`/a reachable broker set, `/classify` still works
in stub mode -- the MQTT publish failure is caught and logged, not raised
to the caller (see "Stub mode" above).

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

**5 tests, all passing**, run against stub mode (no reference profiles
configured in this environment) -- `test_api.py` exercises `POST
/classify` end-to-end through FastAPI's `TestClient` with a small JPEG
generated in-test via Pillow, with `app.main.publish_result` mocked so
the suite needs no real MQTT broker. One test also confirms `/classify`
still returns 200 when the (mocked) MQTT publish raises. The shared
classifier module's own feature-extraction correctness is tested
separately in `../../shared/tests/test_spectrum_classifier.py` (5 more
tests, deterministic synthetic images with known dominant spatial
frequencies).

**What was NOT verified in this environment:** real (non-stub)
classification against real part photos -- there are no reference
profiles calibrated yet, since no reference photos exist. A real MQTT
broker round-trip was not exercised from this service directly;
`../../mqtt-broker/README.md` documents that round-trip being verified
against the broker itself with `mosquitto_pub`/`mosquitto_sub`.

## Dockerfile / deploy

**Build context is the repo root** (`PARTS_SORTING_PLATFORM/`, i.e.
`..` from `CLOUD_MODE/`), not this folder -- see `../docker-compose.yml`
-- because the Dockerfile `COPY`s `shared/` (the module this service and
`LOCAL_MODE/local-server` both depend on) into the image alongside this
service's own `app/`. `CMD ["uvicorn", "app.main:app", "--host",
"0.0.0.0", "--port", "8000"]`, port `8000`. `railway.toml` points its
health check at `/healthz` and documents the required env vars (see
table above).
