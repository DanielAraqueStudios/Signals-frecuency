# local-server

The "computer" in local-mode: a single FastAPI process that runs on a
machine joined to the Android phone's own WiFi hotspot, the same hotspot
the ESP32 also joins (see `../NETWORK_SETUP.md` for the hotspot/IP
details). Classifies uploaded images by frequency-spectrum extraction
(`../../shared/spectrum_classifier.py`) -- no ML model, same algorithm
`CLOUD_MODE/classification-service` uses.

**Explicitly unsecured, LAN-only.** No auth, no TLS, no MQTT -- plain
HTTP. Do not expose this to the public internet; it has no protection
against arbitrary uploads or abuse. This is intentional for a closed
lab/demo network, not a shortcut to fix later.

## API (GET/PUT only)

- `PUT /images/{sample_id}` -- body is the raw image bytes
  (any `Content-Type`; the classifier reads bytes directly). Runs the
  spectrum classifier synchronously and stores the result under
  `sample_id`. Returns the same classification JSON immediately.
- `GET /images/{sample_id}` -- re-read a previously stored result. If
  `sample_id` was never submitted, returns a documented stub response
  (200, not 404) rather than an error, so ESP32 firmware doesn't need
  special-case error handling.
- `GET /images/latest` -- the most recently PUT result, with no id
  needed -- this is what the ESP32 firmware polls (see
  `../firmware/esp32_local_http/`), since it has no way to learn a
  dynamically-generated sample id without MQTT/push.
- `GET /healthz` -- `{"status": "ok", "stub_mode": bool}`.
- `POST /band/pause` -- stands in for the ESP32's VL53L0X distance sensor
  while it isn't working reliably. A second device (phone, fixed IP on
  this LAN) calls this on each volume-up/down press; no body needed.
  Sets a one-shot "pause requested" flag (see `app/pause_trigger.py`).
- `GET /band/pause-status` -- `{"pause_requested": bool}`. Polled by the
  ESP32 firmware (`../firmware/esp32_local_http/`) alongside
  `/images/latest`; reading it resets the flag, so one button press maps
  to exactly one band pause.

## Stub mode

Until `model/labels_config.json` has real `reference_features` entries
per class (see that file's `_comment` and
`../../CLOUD_MODE/classification-service/model/README.md` for the
calibration process, which is identical), every classification returns
`{"label": "unclassified", "stub": true, "reason": "no reference
spectrum profiles configured", "features": null}` -- never a fabricated
label.

## Running locally

```bash
cd LOCAL_MODE/local-server
pip install -r requirements.txt
# PYTHONPATH must include PARTS_SORTING_PLATFORM/ (the repo folder two
# levels up) -- app/main.py imports shared.spectrum_classifier, which
# lives in PARTS_SORTING_PLATFORM/shared/, not under local-server/.
# On Windows PowerShell:
$env:PYTHONPATH = (Resolve-Path ../..).Path
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

`--host 0.0.0.0` matters: the ESP32 and phone reach this over the LAN, not
localhost. This machine joins the phone's hotspot as a client; see
`../NETWORK_SETUP.md` for how to get it a stable, known IP (a phone
hotspot usually can't do DHCP reservation like a router) and put that
address in `esp32_local_http.ino`'s `EDIT_THIS_*` constants.

```bash
# From another machine on the same network:
curl -X PUT --data-binary @sample.jpg http://<this-machine-ip>:8100/images/test1
curl http://<this-machine-ip>:8100/images/latest
```

## What was actually verified

`pytest` (`tests/test_local_server.py`) was run against this exact
FastAPI app in this environment -- all passing, all exercising stub mode
(no reference profiles configured here). Not verified: real phone/ESP32
hardware on an actual access point, and classification against real part
photos (needs the reference-profile calibration step above first).
