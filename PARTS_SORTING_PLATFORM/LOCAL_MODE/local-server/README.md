# local-server

The "computer" in local-mode: a single FastAPI process that runs on a
machine joined to the same predefined WiFi access point as the phone and
the ESP32. Classifies uploaded images by frequency-spectrum extraction
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
uvicorn app.main:app --host 0.0.0.0 --port 8100
```

`--host 0.0.0.0` matters: the ESP32 and phone reach this over the LAN, not
localhost. Pick (or reserve via DHCP) a static IP for this machine on the
access point and put it in `esp32_local_http.ino`'s `EDIT_THIS_*`
constants.

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
