FROM eclipse-mosquitto:2.0

COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY acl.conf /mosquitto/config/acl.conf

# certs/ and the password file are NOT baked into the image -- they're
# provided at deploy time (Railway volume/secret in production, a bind
# mount from scripts/gen-dev-certs.sh in local dev). See certs/README.md.

EXPOSE 8883 8884
