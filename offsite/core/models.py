import os
import zmq
import pickle
from time import sleep
import requests
import json
import psutil
import datetime as dt
import pytz
import random
import string

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.utils import timezone as djangotime
from django.db.models import Q

from .helpers import bytes2human
from .decorators import handle_zmq

TANK_ROOT = "/tank/offsites"


class Client(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    folder = models.CharField(max_length=255, null=True, blank=True)
    salt_id = models.CharField(max_length=255, null=True, blank=True)
    sambashare = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def path(self):
        return os.path.join(TANK_ROOT, self.folder)


def get_default_day_hours():
    return [6, 18]


class Agent(models.Model):
    client = models.ForeignKey(
        Client, related_name="agents", null=True, blank=True, on_delete=models.PROTECT
    )
    hostname = models.CharField(max_length=255, null=True, blank=True)
    folder = models.CharField(max_length=255, null=True, blank=True)
    details = JSONField(null=True, blank=True)
    day_hours = ArrayField(
        models.IntegerField(blank=True), default=get_default_day_hours
    )
    day_bwlimit = models.PositiveIntegerField(default=200)
    night_bwlimit = models.PositiveIntegerField(default=800)
    limit_during_day = models.BooleanField(default=True)
    limit_during_night = models.BooleanField(default=True)
    agentid = models.CharField(max_length=255, null=True, blank=True)
    backup_schedule = JSONField(null=True, blank=True)
    offsite_managed = models.BooleanField(default=True)
    offsites_enabled = models.BooleanField(default=True)
    backups_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hostname} - {self.client}"

    @property
    def path(self):
        first = os.path.join(TANK_ROOT, self.client.folder)
        return os.path.join(first, f"veeam/backups/{self.folder}")

    @property
    def size(self):
        try:
            usage = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(self.path)
                for filename in filenames
            )
            return bytes2human(usage)
        except Exception:
            return "n/a"

    @property
    def rsync_bwlimit(self):
        la_tz = pytz.timezone("America/Los_Angeles")
        now = djangotime.now().astimezone(la_tz)

        start = self.day_hours[0]
        end = self.day_hours[1]

        if start < now.hour < end:
            # business hour
            if self.limit_during_day:
                return self.day_bwlimit
            else:
                return 99_999
        else:
            # after hours
            if self.limit_during_night:
                return self.night_bwlimit
            else:
                return 99_999

    @property
    def onsite_size(self):
        if not self.details:
            return "n/a"

        usage = sum(i["size"] for i in self.details["files"])
        return bytes2human(usage)

    @property
    def onsite_dir(self):
        return os.path.join("/tank/veeam/backups", self.folder)

    @property
    def offsite_running(self):
        if self.offsitejobs.exists() and self.offsitejobs.filter(status="running"):
            return True

        return False

    @property
    def backup_running(self):
        if self.backupjobs.exists():
            if self.backupjobs.filter(status="running"):
                return True

        return False

    @property
    def last_offsite_job(self):
        if self.offsitejobs.exists():

            if self.offsitejobs.filter(status="running"):
                return "inprogress"

            job = self.offsitejobs.filter(
                Q(status="completed") | Q(status="cancelled")
            ).last()

            if job:
                utc = job.finished.replace(tzinfo=pytz.utc)
                la_tz = pytz.timezone("America/Los_Angeles")
                la_time = utc.astimezone(la_tz)
                nice = dt.datetime.strftime(la_time, "%I:%M %p %A %b/%d/%Y")
                return f"Last synced: {nice}"

        else:
            return "Last synced: never"

    @handle_zmq
    def send_pub(self, msg, timeout=10):

        context = zmq.Context()

        # ports
        pub_port = 23954
        sub_port = 23955

        zmq_error = False
        # sub for replies from agent
        try:
            subscriber = context.socket(zmq.SUB)
            subscriber.bind("tcp://*:%s" % sub_port)
            subscriber.setsockopt_string(zmq.SUBSCRIBE, self.agentid)
        except Exception as e:
            zmq_error = True
            subscriber.close()

        # publisher
        try:
            publisher = context.socket(zmq.PUB)
            publisher.bind("tcp://*:%s" % pub_port)
        except Exception as e:
            zmq_error = True
            publisher.close()

        if zmq_error:
            context.term()
            return "inuse"

        # poller
        poller = zmq.Poller()
        poller.register(subscriber, zmq.POLLIN)

        # give time for subscribers to connect
        sleep(2)

        publisher.send_multipart([self.agentid.encode(), pickle.dumps(msg)])

        evts = poller.poll(timeout * 1000)

        error = False

        if not evts:
            error = True

        else:
            [topic, data] = subscriber.recv_multipart()

            if topic and topic.decode() == self.agentid:
                resp = pickle.loads(data)
            else:
                error = True

        # cleanup
        subscriber.close()
        publisher.close()
        context.term()

        if error:
            return "error"
        else:
            return resp

    def salt_api_cmd(self, **kwargs):

        try:
            timeout = kwargs["timeout"]
        except KeyError:
            timeout = 15

        salt_timeout = timeout + 2

        json = {
            "client": "local",
            "tgt": self.client.salt_id,
            "fun": kwargs["func"],
            "timeout": salt_timeout,
            "username": settings.SALT_USERNAME,
            "password": settings.SALT_PASSWORD,
            "eauth": "pam",
        }

        if "arg" in kwargs:
            json.update({"arg": kwargs["arg"]})
        if "kwargs" in kwargs:
            json.update({"kwarg": kwargs["kwargs"]})

        try:
            resp = requests.post(
                "http://" + settings.SALT_HOST + ":8123/run",
                json=[json],
                timeout=timeout,
            )
        except Exception:
            return "error"
        else:
            return resp


STATUS_CHOICES = [
    ("pending", "Pending"),
    ("running", "Running"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]


class OffsiteJob(models.Model):
    agent = models.ForeignKey(
        Agent, related_name="offsitejobs", on_delete=models.CASCADE,
    )
    pid = models.PositiveIntegerField(null=True, blank=True)
    logfile_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default="running",
    )
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.agent} - {self.status}"


BACKUP_MODES = [
    ("backup", "Incremental"),
    ("activefull", "Active Full"),
    ("standalone", "Standalone Full"),
]


class BackupJob(models.Model):
    agent = models.ForeignKey(
        Agent, related_name="backupjobs", on_delete=models.CASCADE,
    )
    pid = models.PositiveIntegerField(null=True, blank=True)
    mode = models.CharField(max_length=255, choices=BACKUP_MODES, default="backup")
    proc_name = models.CharField(max_length=255, null=True, blank=True)
    cmdline = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default="running",
    )
    started = models.DateTimeField(null=True, blank=True)
    finished = models.DateTimeField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.agent} - {self.status}"
