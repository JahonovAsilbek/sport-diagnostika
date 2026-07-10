"""Beat liveness heartbeat (DVPS-18). Celery Beat has no control API and the slim image has
no ps/pgrep, so a container healthcheck isn't possible — instead a scheduled task pings a
dead-man switch (e.g. Healthchecks.io). If it stops arriving, that service alerts. Opt-in:
no-op unless HEALTHCHECK_PING_URL is set.
"""

import logging
from urllib.request import urlopen

from celery import shared_task
from django.conf import settings

logger = logging.getLogger("apps.common")


@shared_task
def heartbeat():
    url = getattr(settings, "HEALTHCHECK_PING_URL", "")
    if not url:
        return "skipped"
    try:
        urlopen(url, timeout=10).close()
    except Exception:
        logger.warning("heartbeat ping failed", exc_info=True)
        return "failed"
    return "ok"
