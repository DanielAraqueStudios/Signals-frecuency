# TLS certificates for the MQTT broker

**Nothing in this folder is committed except this README.** Real
certificates and private keys must never enter git history — even a
since-rotated one leaves a permanent trace.

## Local development

Run `../../scripts/gen-dev-certs.sh` from the repo root (or `scripts/` from
here). It generates a throwaway self-signed CA + server cert into this
folder (`ca.crt`, `server.crt`, `server.key`) and a dev `config/passwd`
Mosquitto password file — everything `docker-compose up` needs. This
folder is gitignored; regenerate it any time.

## Production (Railway)

Use a real CA-issued certificate (e.g. Let's Encrypt via a Railway-fronted
domain, or your own internal CA if devices are pre-provisioned with a
custom root). Supply it to the `mqtt-broker` Railway service as a mounted
volume or via the Railway CLI's file-upload-as-secret mechanism — not as
plain environment variables (PEM blobs are unwieldy as env vars and easy
to leak into logs). See `../../docs/deployment-railway.md` for the exact
steps once you have a Railway project.

## Password file

`config/passwd` is Mosquitto's own hashed-password format, generated with:

```bash
mosquitto_passwd -c /mosquitto/config/passwd classification-service
mosquitto_passwd /mosquitto/config/passwd device-<deviceId>   # one per paired ESP32-S3
```

`api-gateway`'s `POST /devices/pair` (see
`../../services/api-gateway/README.md`) is where device credentials are
actually minted for a real deployment — this manual command is for local
testing only.
