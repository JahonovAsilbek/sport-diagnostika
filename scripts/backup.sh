#!/bin/sh
# Automated backup of the Postgres DB + media volume (D6 / DVPS-17). Idempotent, cron-friendly.
#   - pg_dump runs INSIDE the db container, so its pg_dump matches the server version (16);
#   - the media named volume is tarred via a throwaway alpine container;
#   - old backups past BACKUP_RETENTION_DAYS are pruned;
#   - if BACKUP_RSYNC_TARGET is set, the backup dir is mirrored off-server.
# Both artifacts stream to the host over stdout — the files are owned by the invoking user, and
# nothing extra is written inside the containers. See docs/BACKUP.md.
#
#   ./scripts/backup.sh            # → ./backups/db-<ts>.dump + media-<ts>.tgz
set -eu

cd "$(dirname "$0")/.."  # repo root
COMPOSE="docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml"

BACKUP_DIR="${BACKUP_DIR:-$(pwd)/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
# <project>_media — the project name is fixed in the base compose (`name: sport-diagnostika`).
MEDIA_VOLUME="${MEDIA_VOLUME:-sport-diagnostika_media}"
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

DB_FILE="$BACKUP_DIR/db-$TS.dump"
MEDIA_FILE="$BACKUP_DIR/media-$TS.tgz"

echo "### pg_dump (custom format) → $DB_FILE"
# -Fc = compressed custom format, restorable with pg_restore --clean. Creds from the db env.
# shellcheck disable=SC2016  # $POSTGRES_* are expanded inside the db container, not on the host
$COMPOSE exec -T db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$DB_FILE"

echo "### media volume ($MEDIA_VOLUME) → $MEDIA_FILE"
docker run --rm -i -v "$MEDIA_VOLUME":/media:ro alpine \
  sh -c 'tar czf - -C /media .' > "$MEDIA_FILE"

echo "### retention: pruning backups older than ${RETENTION_DAYS}d"
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'db-*.dump' -o -name 'media-*.tgz' \) \
  -mtime +"$RETENTION_DAYS" -print -delete || true

if [ -n "${BACKUP_RSYNC_TARGET:-}" ]; then
    echo "### off-server copy → $BACKUP_RSYNC_TARGET"
    rsync -az --delete "$BACKUP_DIR/" "$BACKUP_RSYNC_TARGET"
else
    echo "### off-server copy skipped (set BACKUP_RSYNC_TARGET to enable — see docs/BACKUP.md)"
fi

echo "Done: $(basename "$DB_FILE"), $(basename "$MEDIA_FILE")"
