# classification-service

Classifies a photo of a part (bolt, screw, nut, washer, ...) using ONNX
Runtime, and publishes the result as JSON to an MQTT/TLS topic so the
owning ESP32-S3 sees it. Called internally by `api-gateway`, not directly
by the phone app -- see `../../docs/architecture.md`.

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
  "reason": "no trained model present"
}
```

Once a real model is deployed (see `model/README.md`), `stub` is `false`
and `confidence` is a float in `[0, 1]`:

```json
{
  "label": "bolt",
  "confidence": 0.94,
  "stub": false,
  "reason": null
}
```

If the MQTT publish fails (broker unreachable, bad credentials, etc.),
`/classify` still returns 200 with the classification result -- a
worker holding the phone should not see an error just because the
ESP32-S3 leg of the message failed. The failure is logged server-side.

## Stub mode

**No labeled image dataset exists yet.** `app/infer.py` checks for
`model/weights/model.onnx` at startup; if it's absent (the current
state), every call to `/classify` returns the stub response above --
never a fabricated label dressed up as real. This mirrors the "pendiente"
discipline this repo already uses elsewhere (see `THEORY/` and
`LAB_TESTING/LAB1/`) for results that haven't actually been measured.
Deploying a real `model/weights/model.onnx` turns stub mode off
automatically, by file presence alone.

## Training a real model

See `model/README.md` for the full walkthrough: collect
`data/<class_name>/*.jpg`, run `model/train.py` (MobileNetV2 transfer
learning), then `model/export_onnx.py` (export + INT8 quantize). That
directory documents the two-environment split below and honestly states
what was/wasn't run in this environment.

**Two environments, on purpose:** this service's `requirements.txt` (used
by `Dockerfile`, the serving image) installs `onnxruntime` only -- no
PyTorch/TF graph runs in the serving path, matching "most powerful
configuration" = the largest Railway CPU/RAM plan (no GPU tier on
Railway) running an INT8-quantized ONNX Runtime model. `model/train.py`
and `model/export_onnx.py` need `torch`/`torchvision`/`onnx` installed
separately (`pip install torch==2.4.1 torchvision==0.19.1 onnx==1.16.2`)
-- not part of the slim serving image.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `model/weights/model.onnx` | ONNX model file; stub mode if absent |
| `LABELS_PATH` | `model/labels.json` | class list + expected input size |
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
pytest tests/ -v
```

**5 tests, all passing.** All run against stub mode, since no trained
model exists in this environment (see "Stub mode" above and
`model/README.md`'s honesty note) -- `test_infer.py` exercises the
`Classifier` class directly (no model file, and separately no labels
file either), `test_api.py` exercises `POST /classify` end-to-end through
FastAPI's `TestClient` with a small JPEG generated in-test via Pillow (no
external fixture file), with `app.main.publish_result` mocked so the
suite needs no real MQTT broker. One test also confirms `/classify`
still returns 200 when the (mocked) MQTT publish raises.

**What was NOT verified in this environment:** real (non-stub) inference
-- there is no trained `model.onnx` to test against, since no labeled
dataset exists yet. `model/train.py` and `model/export_onnx.py` were not
run end-to-end (see `model/README.md`). A real MQTT broker round-trip
was not exercised from this service directly; `../../mqtt-broker/README.md`
documents that round-trip being verified against the broker itself with
`mosquitto_pub`/`mosquitto_sub`, which is what `app/mqtt_publisher.py`'s
connect/publish/disconnect logic mirrors.

**Real bug fixed during verification:** `pydantic-settings` reserves the
`model_` prefix for its own internal config by default, which collided
with this service's `model_path`/`model_config` field names in
`app/config.py` and raised a `UserWarning` on every startup. Fixed with
`protected_namespaces=()` in `Settings.model_config` -- no functional
change, just silences a name-collision warning that would otherwise show
up in every deploy's logs.

**Real cross-service integration bug found and fixed (during
`docker-compose`/root-doc integration, after this service was otherwise
done):** `api-gateway` was posting the image under multipart field name
`image` and only including `topic` when a device was paired, but this
service's `POST /classify` expected the field name `file` and required
`topic`. Fixed on both sides: `api-gateway` now always sends field name
`file` and `topic=""` when there's no paired device; `topic` here changed
from `Form(...)` (required) to `Form(default="")`, and `/classify` now
skips the MQTT publish entirely when `topic` is empty rather than trying
to publish to a blank topic string. Two new tests
(`test_classify_with_no_topic_skips_publish`,
`test_classify_with_omitted_topic_field_also_skips_publish`) cover this;
all 7 tests (up from 5) still pass.

## Dockerfile / deploy

Serving image only (`Dockerfile` uses `requirements.txt`, not the
training dependencies). `CMD ["uvicorn", "app.main:app", "--host",
"0.0.0.0", "--port", "8000"]`, port `8000`. `railway.toml` points its
health check at `/healthz` and documents the required env vars (see
table above).
