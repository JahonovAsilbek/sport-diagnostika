#!/bin/sh
# Disk-space alert (D7 / DVPS-18). Cron-friendly: warns when a filesystem crosses a usage
# threshold. Opt-in Telegram routing (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID); otherwise it
# just prints and exits non-zero so cron mails the output. Read-only — writes nothing.
#   DISK_ALERT_THRESHOLD=85 ./scripts/disk-alert.sh
set -eu

THRESHOLD="${DISK_ALERT_THRESHOLD:-85}"
CHECK_PATH="${DISK_ALERT_PATH:-/}"

USED=$(df -P "$CHECK_PATH" | awk 'NR==2 {gsub("%","",$5); print $5}')
HOST=$(hostname)

if [ "$USED" -lt "$THRESHOLD" ]; then
    echo "disk ok: ${USED}% of ${CHECK_PATH} used (< ${THRESHOLD}%)"
    exit 0
fi

MSG="[sport-diagnostika] disk alert on ${HOST}: ${CHECK_PATH} at ${USED}% (>= ${THRESHOLD}%)"
echo "$MSG"

if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    curl -fsS --max-time 10 \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        --data-urlencode text="$MSG" \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" >/dev/null \
        && echo "telegram alert sent"
fi

exit 1  # non-zero → cron mails the alert even without Telegram configured
