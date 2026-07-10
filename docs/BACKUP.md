# Backup & restore

Automated backups of the two stateful things — the **Postgres database** and the **media
volume** (uploaded imports + generated reports). A backup you can't restore is useless, so the
restore is a script and the **restore drill** below is part of the runbook. See `docs/DEPLOY.md`
for the surrounding deploy.

## What runs

`scripts/backup.sh` produces two timestamped artifacts in `./backups/` (git-ignored):

- `db-<ts>.dump` — `pg_dump -Fc` (compressed custom format) run **inside the db container**, so
  its `pg_dump` matches the server version.
- `media-<ts>.tgz` — the `media` volume tarred via a throwaway alpine container.

Then it prunes artifacts older than the retention window and, if configured, mirrors off-server.

```sh
./scripts/backup.sh
```

| Env | Default | Meaning |
|---|---|---|
| `BACKUP_DIR` | `./backups` | where artifacts are written |
| `BACKUP_RETENTION_DAYS` | `14` | delete `db-*`/`media-*` older than this |
| `BACKUP_RSYNC_TARGET` | *(unset)* | if set, `rsync -az --delete "$BACKUP_DIR/"` to it (off-server) |
| `MEDIA_VOLUME` | `sport-diagnostika_media` | the `<project>_media` named volume |

## Schedule (host cron)

Run nightly on the VPS as the deploy user. `crontab -e`:

```cron
# Nightly DB + media backup at 02:30, logged.
30 2 * * * cd /home/deploy/sport && BACKUP_RSYNC_TARGET=user@backup-host:/srv/sport-backups \
  ./scripts/backup.sh >> /home/deploy/sport/backups/backup.log 2>&1
```

(The schedule could instead live in Celery Beat / DVPS-7, but that needs a version-matched
`pg_dump` in the worker image — host cron with the db container's own `pg_dump` avoids that.)

## Off-server copy

**Never keep the only copy on the app server.** Set `BACKUP_RSYNC_TARGET` to a remote you control
(another host over SSH, or a NAS). For object storage instead of rsync, swap the rsync line for an
upload (e.g. `rclone copy "$BACKUP_DIR" remote:sport-backups`) — the artifacts are plain files.

## Restore

`scripts/restore.sh` is **destructive** — it overwrites the target database (and media if given).
It copies the dump into the db container and runs `pg_restore --clean --if-exists`.

```sh
./scripts/restore.sh backups/db-<ts>.dump backups/media-<ts>.tgz
# prompts for confirmation (type YES); FORCE=1 skips it (automation)
```

| Env | Meaning |
|---|---|
| `RESTORE_DB` | restore into this DB instead of the live `$POSTGRES_DB` (used for the drill) |
| `FORCE=1` | skip the confirmation prompt |

## Restore drill — test your backups

Prove a backup restores **without touching the live database** — restore into a throwaway DB,
check it, drop it. Run this after any change to the backup setup:

```sh
DUMP=$(ls -t backups/db-*.dump | head -1)
C="docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml"

# 1. throwaway db
$C exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" createdb -U "$POSTGRES_USER" sport_restore_test'
# 2. restore into it via the real script
RESTORE_DB=sport_restore_test FORCE=1 ./scripts/restore.sh "$DUMP"
# 3. verify (table + row counts should match the source)
$C exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" psql -tAU "$POSTGRES_USER" -d sport_restore_test \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='"'"'public'"'"'"'
# 4. drop it
$C exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" dropdb -U "$POSTGRES_USER" sport_restore_test'
```

A media archive is validated the same way it's restored — `tar tzf backups/media-<ts>.tgz` lists
its contents; `restore.sh … <media-tgz>` untars it back into the volume.

## Real disaster recovery (rebuild from scratch)

1. Provision + deploy per `docs/DEPLOY.md` (stack up, but empty DB).
2. `./scripts/restore.sh <db-dump> <media-tgz>` (against the live DB — type `YES`).
3. Restart web so it picks up the restored schema: `docker compose … restart web`.
