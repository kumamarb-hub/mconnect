#!/bin/sh
set -e

# Generate a self-signed cert for the server IP on first start (persisted in the 'certs' volume).
if [ ! -f /certs/server.crt ]; then
  HOST="${HTTPS_HOST:-10.14.0.42}"
  mkdir -p /certs
  echo "==> Generating self-signed cert for $HOST"
  openssl req -x509 -nodes -newkey rsa:2048 -days 825 -sha256 \
    -subj "/CN=$HOST" \
    -addext "subjectAltName=IP:$HOST,IP:127.0.0.1,DNS:localhost" \
    -keyout /certs/server.key -out /certs/server.crt
else
  echo "==> Existing cert found, keeping it"
fi

exec nginx -g 'daemon off;'