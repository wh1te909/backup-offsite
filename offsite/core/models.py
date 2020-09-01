import os
import shutil
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
import msgpack
from loguru import logger

from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone as djangotime
from django.db.models import Q

from .helpers import bytes2human
from .decorators import handle_zmq

TANK_ROOT = "/oldvm/tank/offsites"
ARCHIVE_ROOT = "/oldvm/tank/archives"

logger.configure(**settings.LOG_CONFIG)


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
    details = models.JSONField(null=True, blank=True)
    day_hours = ArrayField(
        models.IntegerField(blank=True), default=get_default_day_hours
    )
    day_bwlimit = models.PositiveIntegerField(default=200)
    night_bwlimit = models.PositiveIntegerField(default=800)
    limit_during_day = models.BooleanField(default=True)
    limit_during_night = models.BooleanField(default=True)
    agentid = models.CharField(max_length=255, null=True, blank=True)
    backup_schedule = models.JSONField(null=True, blank=True)
    offsite_managed = models.BooleanField(default=True)
    offsites_enabled = models.BooleanField(default=True)
    backups_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.hostname} - {self.client}"

    @property
    def path(self):
        return os.path.join(self.client.path, f"veeam/backups/{self.folder}")

    @property
    def archive_path(self):
        return os.path.join(ARCHIVE_ROOT, self.client.folder, self.folder)

    @property
    def raw_size(self):
        try:
            usage = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(self.path)
                for filename in filenames
            )
            return usage
        except Exception:
            return "n/a"

    @property
    def size(self):
        try:
            return bytes2human(self.raw_size)
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
    def raw_onsite_size(self):
        if not self.details:
            return "n/a"

        return sum(i["size"] for i in self.details["files"])

    @property
    def onsite_size(self):
        try:
            return bytes2human(self.raw_onsite_size)
        except Exception:
            return "n/a"

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

    def send_pub(self, msg, timeout=5):

        msg["target"] = self.agentid

        context = zmq.Context()

        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt_string(zmq.IDENTITY, self.agentid)
        socket.connect("tcp://127.0.0.1:23957")

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        socket.send(msgpack.dumps(msg))

        socks = dict(poller.poll(timeout * 1000))

        if socket in socks:
            try:
                message = socket.recv()
                return msgpack.loads(message)
            except IOError:
                return "error"
        else:
            return "error"

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

    def handle_archives(self):
        r = self.salt_api_cmd(
            func="tac_veeam.count_backups", timeout=10, arg=[self.onsite_dir]
        )

        if r == "error":
            return "err"

        ret = r.json()["return"][0][self.client.salt_id]

        if not isinstance(ret, dict):
            return "err"

        try:
            current = [
                i["name"] for i in ret["files"] if not i["name"].endswith(".vbm")
            ]
        except Exception as e:
            logger.error(e)
            return "err"

        if not os.path.exists(self.archive_path):
            os.makedirs(self.archive_path, exist_ok=True)

        with os.scandir(self.path) as it:
            for f in it:
                if (
                    not f.name.startswith(".")
                    and f.is_file()
                    and not f.name.endswith(".vbm")
                ):
                    if f.name not in current:
                        src = os.path.join(self.path, f.name)
                        try:
                            shutil.move(src, self.archive_path)
                            logger.info(f"Moving {src} TO {self.archive_path}")
                        except Exception as e:
                            logger.error(e)

        return "ok"


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
