#!/usr/bin/env bash
# Generates a throwaway RSA keypair for local dev JWT signing/verification.
# Never use this output in production -- generate a real keypair and inject
# it via Railway env vars instead (see docs/deployment-railway.md).
set -euo pipefail

export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

KEY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.dev-secrets"
mkdir -p "$KEY_DIR"
cd "$KEY_DIR"

echo "Generating dev RSA keypair for JWT signing..."
openssl genrsa -out jwt-private.pem 2048
openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem

echo "Done. Files written to $KEY_DIR (gitignored, dev-only material)."
echo "docker-compose.yml mounts these into auth-service and api-gateway automatically."
