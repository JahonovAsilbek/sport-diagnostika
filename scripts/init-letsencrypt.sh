#!/bin/sh
# One-time Let's Encrypt bootstrap for the TLS stack (D5 / DVPS-16). Idempotent.
#   1. drop a throwaway self-signed cert so nginx (which references the cert path) can boot,
#   2. bring nginx up (it serves the ACME HTTP-01 challenge on :80),
#   3. delete the dummy and request a real cert via certbot --webroot,
#   4. reload nginx.
# Run with STAGING=1 first (default — untrusted cert, no rate limits) to validate the flow,
# then re-run with STAGING=0 for a trusted cert. Requires DNS A (and AAAA if the VPS keeps
# `listen [::]`) for $DOMAIN + www → this host, and ports 80/443 open.
#
#   DOMAIN=sport-diagnostika.uz LETSENCRYPT_EMAIL=you@example.com STAGING=1 ./scripts/init-letsencrypt.sh
set -eu

cd "$(dirname "$0")/.."  # repo root
COMPOSE="docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml -f deploy/docker-compose.tls.yml"

DOMAIN="${DOMAIN:-sport-diagnostika.uz}"
EMAIL="${LETSENCRYPT_EMAIL:?set LETSENCRYPT_EMAIL=you@example.com}"
STAGING="${STAGING:-1}"
KEY_SIZE=4096
LIVE="/etc/letsencrypt/live/${DOMAIN}"
DOMAIN_ARGS="-d ${DOMAIN} -d www.${DOMAIN}"  # apex + www (www is 301'd to apex by nginx)

# The certbot service's entrypoint is a renew loop; `run` overrides command, not entrypoint —
# so every one-shot below MUST pass --entrypoint.

echo "### [1/4] temporary self-signed cert at ${LIVE} (so nginx can boot)…"
$COMPOSE run --rm --entrypoint sh certbot -c "\
  mkdir -p ${LIVE} && \
  openssl req -x509 -nodes -newkey rsa:${KEY_SIZE} -days 1 \
    -keyout ${LIVE}/privkey.pem -out ${LIVE}/fullchain.pem -subj '/CN=localhost'"

echo "### [2/4] starting nginx (+ web/db/redis) with the dummy cert…"
$COMPOSE up -d --force-recreate nginx

echo "### [3/4] deleting the dummy cert and requesting the real one…"
$COMPOSE run --rm --entrypoint sh certbot -c "\
  rm -rf ${LIVE} /etc/letsencrypt/archive/${DOMAIN} /etc/letsencrypt/renewal/${DOMAIN}.conf"

STAGING_FLAG=""
[ "$STAGING" = "0" ] || STAGING_FLAG="--staging"
echo "    (mode: ${STAGING_FLAG:-PRODUCTION})"

# shellcheck disable=SC2086  # intentional word-splitting on $STAGING_FLAG / $DOMAIN_ARGS
$COMPOSE run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  $STAGING_FLAG \
  $DOMAIN_ARGS \
  --email "$EMAIL" --rsa-key-size "$KEY_SIZE" \
  --agree-tos --no-eff-email --non-interactive

echo "### [4/4] reloading nginx with the issued cert…"
$COMPOSE exec nginx nginx -s reload

echo
if [ -n "$STAGING_FLAG" ]; then
    echo "STAGING cert installed (a browser warning is expected). Validate, then re-run with STAGING=0."
else
    echo "Production cert installed. Renewal runs automatically in the certbot container."
fi
