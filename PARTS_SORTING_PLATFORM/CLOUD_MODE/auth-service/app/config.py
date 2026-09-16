"""Environment-driven configuration for auth-service.

Every value has a sane local-dev default so `docker-compose up` works
without any .env file; production (Railway) overrides all of these via
environment variables. Never commit real secrets/keys into this repo --
see README.md for how RSA_PRIVATE_KEY/RSA_PUBLIC_KEY are generated and
injected in production.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/parts_sorting"

    # JWT signing (RS256): a private/public keypair so other services can
    # verify tokens with only the public key, never the private one.
    # Generate a dev pair with ../../scripts/gen-dev-jwt-keys.sh (or
    # manually: openssl genrsa -out private.pem 2048 &&
    # openssl rsa -in private.pem -pubout -out public.pem).
    #
    # Set the *_key fields directly (Railway: paste PEM contents into the
    # env var), or the *_key_file fields to a mounted file path (local
    # docker-compose: env vars can't cleanly hold multi-line PEM text, so
    # docker-compose.yml mounts the files instead and points these at
    # them). If both are set, the literal *_key value wins.
    jwt_private_key: str = ""
    jwt_private_key_file: str = ""
    jwt_public_key: str = ""
    jwt_public_key_file: str = ""
    jwt_issuer: str = "parts-sorting-auth-service"
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 30

    def model_post_init(self, __context: object) -> None:
        if not self.jwt_private_key and self.jwt_private_key_file:
            self.jwt_private_key = Path(self.jwt_private_key_file).read_text(encoding="utf-8")
        if not self.jwt_public_key and self.jwt_public_key_file:
            self.jwt_public_key = Path(self.jwt_public_key_file).read_text(encoding="utf-8")


settings = Settings()
