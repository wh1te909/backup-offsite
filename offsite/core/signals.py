import random
import pytz
import json

from django.dispatch import receiver
from django.db.models.signals import pre_save

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from .models import Agent

days = {
    "sun": 0,
    "mon": 1,
    "tue": 2,
    "wed": 3,
    "thu": 4,
    "fri": 5,
    "sat": 6,
}


@receiver(pre_save, sender=Agent)
def handle_schedules(sender, instance: Agent, **kwargs):
    """
        Triggers everytime a backup or offsite schedule is created or changed
        If schedule already exists, first deletes the associated periodic tasks 
        then recreates based on new schedule
    """

    if instance.pk is not None:

        schedule = sender.objects.get(pk=instance.pk).backup_schedule

        if not schedule == instance.backup_schedule:
            # schedule has been changed

            tasks = PeriodicTask.objects.filter(
                name__startswith=f"{instance.hostname}-{instance.pk}-backup"
            )

            if tasks:
                tasks.delete()

            for day, times in instance.backup_schedule.items():
                day_of_week = days.get(day)
                hours = ",".join(str(x) for x in times)

                if hours:

                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=str(random.randint(0, 4)),
                        hour=hours,
                        day_of_week=day_of_week,
                        day_of_month="*",
                        month_of_year="*",
                        timezone=pytz.timezone("America/Los_Angeles"),
                    )

                    PeriodicTask.objects.create(
                        crontab=schedule,
                        name=f"{instance.hostname}-{instance.pk}-backup-day{day_of_week}",
                        task="core.tasks.incremental_backup_task",
                        enabled=instance.backups_enabled,
                        args=json.dumps([instance.pk]),
                    )

    if instance.pk is not None:

        backup_enabled = sender.objects.get(pk=instance.pk).backups_enabled

        if not backup_enabled == instance.backups_enabled:

            tasks = PeriodicTask.objects.filter(
                name__startswith=f"{instance.hostname}-{instance.pk}-backup"
            )

            for task in tasks:
                task.enabled = instance.backups_enabled
                task.save(update_fields=["enabled"])
