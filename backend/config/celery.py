import os

from celery import Celery

# The worker process must know which Django settings to load.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("sport_diagnostika")
# All CELERY_* settings come from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")
# Discover tasks.py in every installed app (used from B7/B11/B12 onward).
app.autodiscover_tasks()


@app.task
def debug_task():
    return "ok"
