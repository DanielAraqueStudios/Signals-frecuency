# Architecture

## Use case

A worker on a conveyor belt line points their phone at a small hardware
part (bolt, screw, nut, washer, ...) and takes a photo through the mobile
app. The photo is classified by part type; the result is shown to the
worker and, if they have an ESP32-S3 paired, echoed to it over MQTT so it
can display/log it. This is identification/logging only for now — no
physical sorting/actuation.

## Data flow

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
                                          | ONNX Runtime inference
                                          | (stub mode if no trained model present)
                                          v
                                  [mqtt-broker (TLS)]
                                     |            |
                            [ESP32-S3 firmware]  (a future live-view
                            subscribes to its     channel for the app,
                            own results/ topic,   not built yet)
                            displays/logs it
```

## Why images travel over HTTPS, not MQTT

The original idea was "the image goes to the ESP32 through the MQTT
server." This implementation deliberately does not do that, for two
reasons:

1. **MQTT brokers aren't built for large binaries.** A JPEG photo is
   easily 100KB-2MB; MQTT message-size limits and typical broker tuning
   assume small, frequent messages (this broker's default config doesn't
   even raise the limit for it).
2. **The ESP32-S3 doesn't need the image.** It was confirmed during
   design that classification runs on the backend (the most powerful
   compute available), and the device's only job is to receive and
   display the *result* — a small JSON message, exactly what MQTT is
   good at.

MQTT still does real work here: it's the transport from
`classification-service` to the ESP32-S3, and it's TLS-encrypted
end-to-end (see `../mqtt-broker/README.md`).

## Why classification runs in a backend service, not on the ESP32-S3

"Run it at the most powerful configuration" was the explicit requirement.
An ESP32-S3, even with its AI-oriented instruction extensions, is not
that — a Railway-hosted service is. See
`../services/classification-service/README.md` for the model itself
(MobileNetV2 transfer learning, ONNX Runtime + INT8 quantization for
CPU-tier inference, since Railway has no first-party GPU plan).

## Authorization boundaries

- **auth-service** is the only service that touches password hashes or
  issues tokens. Every other service verifies tokens with its RS256
  public key alone.
- **api-gateway** is the only service with a notion of "which user owns
  which device." That ownership check happens in api-gateway's own
  database — deliberately *not* encoded in the MQTT topic string, which
  is a weak place to enforce it (see `../mqtt-broker/README.md`).
- **mqtt-broker**'s ACL scopes each device to read exactly one topic,
  matching its own MQTT username. `classification-service` is the only
  writer.

## Known limitations (stated, not hidden)

- **No labeled dataset exists yet.** `classification-service` runs in an
  explicit stub mode (`"stub": true` in every response) until a real
  model is trained and its ONNX weights are placed in
  `services/classification-service/model/weights/`. See that service's
  README for exactly what's needed.
- **New device credentials need a broker restart to take effect** (see
  `../services/api-gateway/README.md`'s MQTT provisioning section). A
  documented (not built) upgrade path is Mosquitto's dynamic-security
  plugin.
- **No physical sorting/actuation.** The `commands/<device>` MQTT topic
  is reserved in the broker's ACL for this, but nothing publishes to it
  yet — this was explicitly out of scope for this round.
