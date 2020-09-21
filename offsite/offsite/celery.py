from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "offsite.settings")

app = Celery(
    "offsite",
    backend="redis://" + settings.REDIS_HOST,
    broker="redis://" + settings.REDIS_HOST,
)
app.broker_url = "redis://" + settings.REDIS_HOST + ":6379"
app.result_backend = "redis://" + settings.REDIS_HOST + ":6379"
app.accept_content = ["application/json"]
app.result_serializer = "json"
app.task_serializer = "json"
app.conf.task_track_started = True
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "gather-info": {
        "task": "core.tasks.gather_info_task",
        "schedule": crontab(minute="*/2"),
    },
    "monitor-offsites": {
        "task": "core.tasks.monitor_offsites_task",
        "schedule": crontab(minute="*"),
    },
    "monitor-backups": {
        "task": "core.tasks.monitor_backups_task",
        "schedule": crontab(minute="*"),
    },
    "get-offsite-logs": {
        "task": "core.tasks.get_offsite_logs_task",
        "schedule": crontab(minute="*/2"),
    },
    "auto-offsites": {
        "task": "core.tasks.auto_offsite_task",
        "schedule": crontab(minute="*/15"),
    },
}


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    pass
