#!/bin/sh
# Restore the Postgres DB (and optionally the media volume) from a backup made by
# scripts/backup.sh (D6 / DVPS-17). DESTRUCTIVE — it overwrites the target database.
#
#   ./scripts/restore.sh backups/db-<ts>.dump [backups/media-<ts>.tgz]
#
# Env:
#   RESTORE_DB=<name>   restore into this database instead of $POSTGRES_DB (used for the
#                       tested-restore drill — restore into a throwaway db, verify, drop it).
#   FORCE=1             skip the interactive confirmation (for the drill / automation).
set -eu

cd "$(dirname "$0")/.."  # repo root
COMPOSE="docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml"
MEDIA_VOLUME="${MEDIA_VOLUME:-sport-diagnostika_media}"

DB_DUMP="${1:?usage: restore.sh <db-dump> [media-tgz]}"
MEDIA_TGZ="${2:-}"
[ -f "$DB_DUMP" ] || { echo "no such dump: $DB_DUMP" >&2; exit 1; }
DEST="${RESTORE_DB:-}"

if [ "${FORCE:-0}" != "1" ]; then
    printf 'This OVERWRITES database "%s"%s. Type YES to proceed: ' \
        "${DEST:-\$POSTGRES_DB (the live DB)}" \
        "$([ -n "$MEDIA_TGZ" ] && echo ' and the media volume')"
    read -r ans
    [ "$ans" = "YES" ] || { echo "aborted."; exit 1; }
fi

echo "### copying dump into the db container"
$COMPOSE cp "$DB_DUMP" db:/tmp/restore.dump

echo "### pg_restore (--clean --if-exists) → ${DEST:-\$POSTGRES_DB}"
# DEST empty → the container falls back to its own $POSTGRES_DB. --no-owner so objects are owned
# by the restoring role; --clean --if-exists drops existing objects first (idempotent re-restore).
# shellcheck disable=SC2016  # host $DEST is spliced in via the quote-break; $POSTGRES_* expand in-container
$COMPOSE exec -T db sh -c '
    DEST="'"$DEST"'"
    [ -n "$DEST" ] || DEST="$POSTGRES_DB"
    PGPASSWORD="$POSTGRES_PASSWORD" pg_restore --clean --if-exists --no-owner \
        -U "$POSTGRES_USER" -d "$DEST" /tmp/restore.dump
'
$COMPOSE exec -T db rm -f /tmp/restore.dump

if [ -n "$MEDIA_TGZ" ]; then
    [ -f "$MEDIA_TGZ" ] || { echo "no such media archive: $MEDIA_TGZ" >&2; exit 1; }
    echo "### restoring media volume ($MEDIA_VOLUME)"
    docker run --rm -i -v "$MEDIA_VOLUME":/media alpine \
        sh -c 'rm -rf /media/* /media/..?* /media/.[!.]* 2>/dev/null; tar xzf - -C /media' < "$MEDIA_TGZ"
fi

echo "Done."
