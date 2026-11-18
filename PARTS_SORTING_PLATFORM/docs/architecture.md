# Architecture

## Use case

A worker points their phone at a small hardware part (bolt, screw, nut,
washer, ...) and takes a photo through the mobile app. The photo is
classified by part type using **frequency-spectrum extraction** (2D FFT
of the image, no ML model -- see `../shared/spectrum_classifier.py`); the
result is shown to the worker and, if they have an ESP32 paired,
delivered to it. This is identification/logging only for now -- no
physical sorting/actuation.

## Two independent deployment modes

This platform ships **two separate ways to run it**, sharing only the
classifier module (`shared/spectrum_classifier.py`) and, loosely, the
mobile app:

- **`CLOUD_MODE/`** -- Railway-hosted, multi-user: JWT auth
  (`auth-service`), MQTT/TLS device delivery (`mqtt-broker`), image
  storage (S3-compatible bucket via `api-gateway`). See
  `../CLOUD_MODE/README.md` (root readme) and this doc's "Cloud mode data
  flow" below.
- **`LOCAL_MODE/`** -- a closed LAN, single-computer setup: the Android
  **phone creates a WiFi hotspot**, and the ESP32 and the "computer"
  (`local-server`) both join it as clients. No auth, no TLS, no MQTT --
  plain, explicitly unsecured HTTP, with an API surface of exactly **GET
  and PUT**. See `../LOCAL_MODE/local-server/README.md` and
  `../LOCAL_MODE/NETWORK_SETUP.md` for the hotspot/IP details.

Pick one mode per deployment; they don't talk to each other. Both run the
*same* frequency-spectrum classification code, just wrapped differently
(with auth+MQTT in cloud mode, with nothing in local mode).

## Cloud mode data flow

```
[Phone app] --HTTPS, Bearer JWT--> [api-gateway]
     |                                   |
     | register/login                    | 1. verifies JWT locally (RS256 public key)
     v                                   | 2. uploads image to S3-compatible storage
[auth-service]                           | 3. calls classification-service (internal HTTP)
     |                                   | 4. stores the result, returns it to the app
     | issues JWT (RS256)                v
     +-------------------------> [classification-service]
                                          |
                                          | frequency-spectrum classification
                                          | (shared/spectrum_classifier.py;
                                          | stub mode if no reference profiles
                                          | configured)
                                          v
                                  [mqtt-broker (TLS)]
                                     |            |
                            [ESP32-S3 firmware]  (a future live-view
                            subscribes to its     channel for the app,
                            own results/ topic,   not built yet)
                            displays/logs it
```

### Why images travel over HTTPS, not MQTT (cloud mode)

The original idea was "the image goes to the ESP32 through the MQTT
server." This implementation deliberately does not do that, for two
reasons:

1. **MQTT brokers aren't built for large binaries.** A JPEG photo is
   easily 100KB-2MB; MQTT message-size limits and typical broker tuning
   assume small, frequent messages.
2. **The ESP32-S3 doesn't need the image.** Classification runs on the
   backend; the device's only job is to receive and display the
   *result* -- a small JSON message, exactly what MQTT is good at.

MQTT still does real work here: it's the transport from
`classification-service` to the ESP32-S3, TLS-encrypted end-to-end (see
`../CLOUD_MODE/mqtt-broker/README.md`).

## Local mode data flow

```
[Phone]  --HTTP PUT /images/{id}-->  [local-server ("the computer")]
   ^                                        |
   | (immediate response, same call)        | frequency-spectrum classification
   |                                        | (shared/spectrum_classifier.py;
   |                                        | stub mode if no reference profiles
   |                                        | configured)
   |                                        v
   |                              in-memory result store
   |                                        ^
   +---- HTTP GET /images/{id} or /images/latest ----+
                                        ^
                        [ESP32 firmware polls GET /images/latest]
```

The **Android phone itself creates the WiFi hotspot**; local-server's
computer and the ESP32 both join that hotspot as ordinary clients -- there
is no separate router/access point in this mode. There is no auth, no
TLS, no MQTT broker -- this is intentional for a closed lab/demo network,
spelled out explicitly in `../LOCAL_MODE/local-server/README.md`, not a
shortcut to harden later. The API is deliberately just two HTTP methods:
**PUT** (phone uploads an image, gets the classification back
synchronously) and **GET** (ESP32 or phone reads the latest/a specific
result). There's no push mechanism, so the ESP32 polls on a timer.

A phone hotspot behaves differently from a normal router on two points
that matter here (see `../LOCAL_MODE/NETWORK_SETUP.md` for the full
detail): client IPs handed out by the phone's DHCP are usually not static
by default, which complicates giving the ESP32 a fixed address for
local-server; and most ESP32/ESP32-S3 boards only support 2.4GHz WiFi, so
the hotspot must be forced to 2.4GHz/compatibility mode if the phone
defaults to 5GHz or dual-band.

## Frequency-spectrum classification (shared/spectrum_classifier.py)

Both modes classify the same way, and there is no ML model anywhere in
this platform:

1. Grayscale the image.
2. 2D FFT (`np.fft.fft2` + `fftshift`) -> magnitude spectrum.
3. Sum magnitude into three radial frequency bands (low/mid/high,
   normalized to sum to 1) -> a `[low, mid, high]` feature vector.
4. Compare against per-class `reference_features` in a `labels_config.json`
   (one per deployment: `CLOUD_MODE/classification-service/model/` and
   `LOCAL_MODE/local-server/model/`) by nearest Euclidean distance.

With no reference profiles configured (the current, placeholder state in
both modes), classification always returns a documented stub response
(`"stub": true`) rather than a fabricated label -- see either service's
`model/README.md` for how to calibrate real profiles from a handful of
reference photos per part type. This replaced an earlier ONNX/CNN design;
see git history if you need the old ML-based approach.

## Authorization boundaries (cloud mode only; local mode has none, by design)

- **auth-service** is the only service that touches password hashes or
  issues tokens. Every other cloud-mode service verifies tokens with its
  RS256 public key alone.
- **api-gateway** is the only service with a notion of "which user owns
  which device." That ownership check happens in api-gateway's own
  database.
- **mqtt-broker**'s ACL scopes each device to read exactly one topic,
  matching its own MQTT username. `classification-service` is the only
  writer.
- **local-server has none of this.** No login, no per-device identity, no
  encryption -- anyone on the WiFi access point can PUT/GET. This is the
  explicit tradeoff of local mode; do not expose `local-server` beyond
  the closed LAN it's designed for.

## Known limitations (stated, not hidden)

- **No reference spectrum profiles calibrated yet**, in either mode --
  both run in stub mode until a handful of reference photos per part
  type are captured and averaged into `labels_config.json` (see the
  relevant `model/README.md`).
- **New device credentials need a broker restart to take effect** (cloud
  mode only; see `../CLOUD_MODE/api-gateway/README.md`'s MQTT
  provisioning section). A documented (not built) upgrade path is
  Mosquitto's dynamic-security plugin.
- **No physical sorting/actuation**, in either mode.
- **Local mode has no discovery mechanism** -- the ESP32 firmware needs
  `local-server`'s LAN IP hardcoded, and a phone hotspot generally can't
  do DHCP reservation the way a router's admin page can. See
  `../LOCAL_MODE/NETWORK_SETUP.md` for the practical options (manual
  static IP, reading the lease from the hotspot's connected-devices
  screen, or mDNS as a future improvement).
