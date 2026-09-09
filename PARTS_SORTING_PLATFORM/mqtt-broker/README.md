# mqtt-broker

Eclipse Mosquitto, TLS-only (no plaintext listener), with per-device ACLs.
This is the message bus between `classification-service` (publisher) and
each paired ESP32-S3 (subscriber, one topic each) — see
`../docs/architecture.md`.

## Topic scheme

- `results/<deviceMqttUsername>` — one classification result (JSON),
  published by `classification-service`, read-only for the one device
  whose MQTT username equals that segment. Device usernames are minted by
  `api-gateway`'s `POST /devices/pair` as `device-<deviceId>`.
- `commands/<deviceMqttUsername>` — reserved for a future actuation
  feature (not built yet — see the root `readme.md`'s scope notes).

Note `userId` does **not** appear in any topic. Which user owns which
device is tracked in `api-gateway`'s own database; the topic string is
just the device's own login name, which keeps the ACL a single pattern
rule per device instead of needing per-user topic namespacing.

## Local dev

```bash
# From the repo root:
bash PARTS_SORTING_PLATFORM/scripts/gen-dev-certs.sh
docker run -d --rm --name mqtt-broker \
  -p 8883:8883 -p 8884:8884 \
  -v "$(pwd)/mosquitto.conf:/mosquitto/config/mosquitto.conf" \
  -v "$(pwd)/acl.conf:/mosquitto/config/acl.conf" \
  -v "$(pwd)/config/passwd:/mosquitto/config/passwd" \
  -v "$(pwd)/certs:/mosquitto/certs" \
  eclipse-mosquitto:2.0
```

(This is exactly what `docker-compose.yml`, at the repo root of this
project, wires up for you — see `../readme.md`.)

**On Windows/Git Bash**, prefix docker/openssl commands that pass
absolute POSIX-style paths (`/c/Users/...`) with
`MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*"`, or MSYS will silently mangle
them into Windows paths — `gen-dev-certs.sh` already does this itself.

Add a test device credential and confirm the round trip:

```bash
docker run --rm -v "$(pwd)/config:/mosquitto/config" eclipse-mosquitto:2.0 \
  mosquitto_passwd -b /mosquitto/config/passwd device-deviceABC devpassword2

# subscribe (in one terminal):
docker run --rm -v "$(pwd)/certs:/certs" eclipse-mosquitto:2.0 \
  mosquitto_sub -h localhost -p 8883 --cafile /certs/ca.crt \
  -u device-deviceABC -P devpassword2 -t "results/device-deviceABC"

# publish (in another):
docker run --rm -v "$(pwd)/certs:/certs" eclipse-mosquitto:2.0 \
  mosquitto_pub -h localhost -p 8883 --cafile /certs/ca.crt \
  -u classification-service -P devpassword \
  -t "results/device-deviceABC" -m '{"label":"bolt","stub":true}'
```

Verified locally (see this project's build notes): the TLS handshake, the
authenticated publish from `classification-service`, and the scoped read
by a device all round-trip correctly; a device subscribing to a topic
that isn't its own receives nothing, per the ACL.

## Two bugs this config had to work around (both fixed here already)

1. **SAN-less dev certs get silently rejected.** A CN-only certificate
   (no `subjectAltName`) fails TLS hostname verification on modern
   OpenSSL/mosquitto clients with an opaque `tlsv1 alert internal error`
   — no mention of the real cause. `gen-dev-certs.sh` issues the dev
   server cert with a SAN covering `mqtt-broker`, `localhost`,
   `host.docker.internal`, and `127.0.0.1`.
2. **The ACL can't scope by userId via `%u`.** `%u` in a Mosquitto ACL
   `pattern` rule expands to the connecting **username**, not any
   application-level user ID — so a topic scheme like
   `results/{userId}/{deviceId}` can never match a `pattern read
   results/%u/#` rule unless the device's MQTT username literally *is*
   the userId (which breaks down the moment one user has 2+ devices).
   Fixed by dropping userId from the topic entirely (see "Topic scheme"
   above) and enforcing user↔device ownership in `api-gateway`'s database
   instead of in the MQTT ACL.
