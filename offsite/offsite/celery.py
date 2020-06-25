from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

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


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):

    from core.tasks import (
        gather_info_task,
        monitor_offsites_task,
        get_offsite_logs_task,
        monitor_backups_task,
        auto_offsite_task,
    )

    sender.add_periodic_task(60.0, gather_info_task.s())

    sender.add_periodic_task(45.0, monitor_offsites_task.s())

    sender.add_periodic_task(120.0, get_offsite_logs_task.s())

    sender.add_periodic_task(30.0, monitor_backups_task.s())

    sender.add_periodic_task(900.0, auto_offsite_task.s())
