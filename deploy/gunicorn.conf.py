# deploy/gunicorn.conf.py — gunicorn runtime config for the prod `web` service. Mounted at
# /gunicorn.conf.py by docker-compose.prod.yml (referenced with `gunicorn -c`).
import multiprocessing
import os

bind = "0.0.0.0:8000"

# Size workers to the host's cores — gunicorn's (2 * cores) + 1 rule of thumb — unless the
# operator pins it with WEB_CONCURRENCY. Defaulting to cores (not gunicorn's bare default of 1)
# means a VPS that forgot to set WEB_CONCURRENCY still runs a sane number of workers.
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))

accesslog = "-"  # stdout — captured by the container runtime
