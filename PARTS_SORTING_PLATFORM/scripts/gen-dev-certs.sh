#!/usr/bin/env bash
# Generates a throwaway self-signed CA + server certificate for the local
# dev MQTT broker, plus a dev password file. Never use this output in
# production -- see mqtt-broker/certs/README.md.
set -euo pipefail

# On Git Bash for Windows (MSYS), a leading "/" in an argument like
# "/CN=..." gets auto-converted as if it were a filesystem path, which
# corrupts the openssl -subj value. This disables that conversion; it's a
# no-op on real Linux/macOS shells.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/mqtt-broker/certs"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "Generating dev CA..."
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout ca.key -out ca.crt \
  -subj "/CN=parts-sorting-dev-ca"

echo "Generating dev server key + CSR..."
openssl req -nodes -newkey rsa:2048 \
  -keyout server.key -out server.csr \
  -subj "/CN=mqtt-broker"

# A CN-only certificate (no Subject Alternative Name) is silently rejected
# by modern TLS clients during hostname verification -- OpenSSL 3.x on the
# mosquitto_pub/sub CLI and most MQTT client libraries included. Every
# hostname a dev client might connect through (the container's own name,
# localhost, host.docker.internal for containers reaching the host, and
# the loopback IP) needs to be in the SAN list. Written to a real temp
# file rather than process substitution (<()), which isn't reliable on
# Git Bash for Windows -- and referenced by a bare relative filename
# (we're already `cd`'d into $CERT_DIR), because the openssl.exe shipped
# with Git for Windows fails to fopen() an absolute MSYS-style path
# (/c/Users/...) passed as -extfile, even though the same path works fine
# for arguments MSYS itself path-converts.
echo "Signing dev server certificate with the dev CA (with SAN)..."
printf "subjectAltName=DNS:mqtt-broker,DNS:localhost,DNS:host.docker.internal,IP:127.0.0.1" > san.ext.tmp
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 \
  -extfile san.ext.tmp
rm -f san.ext.tmp

rm -f server.csr ca.srl

echo "Generating dev Mosquitto password file (classification-service / devpassword)..."
mkdir -p config
docker run --rm -v "$CERT_DIR/../config:/mosquitto/config" eclipse-mosquitto:2.0 \
  mosquitto_passwd -b -c /mosquitto/config/passwd classification-service devpassword

echo "Done. Files written to $CERT_DIR and $CERT_DIR/../config/passwd"
echo "This is dev-only material -- both directories are gitignored."
