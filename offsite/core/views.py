import psutil
import zlib
import base64
import json
import random
import string


from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone as djangotime
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Agent, Client, OffsiteJob, BackupJob
from .serializers import (
    AgentSerializer,
    ClientSerializer,
    OffsiteJobTableSerializer,
    BackupJobTableSerializer,
    BackupScheduleSerializer,
    OffsiteSettingsSerializer,
)
from .tasks import kill_local_rsync_task
from .helpers import bytes2human, notify_Error


@api_view()
def version(request):
    return Response(settings.APP_VER)


@api_view()
def agents(request):
    agents = Agent.objects.all()
    return Response(AgentSerializer(agents, many=True).data)


@api_view()
def clients(request):
    clients = Client.objects.all()
    return Response(ClientSerializer(clients, many=True).data)


@api_view()
def offsite_jobs(request):
    jobs = OffsiteJob.objects.all()
    return Response(OffsiteJobTableSerializer(jobs, many=True).data)


@api_view()
def backup_jobs(request):
    jobs = BackupJob.objects.all()
    return Response(BackupJobTableSerializer(jobs, many=True).data)


@api_view()
def view_offsite_output(request, pk):
    job = get_object_or_404(OffsiteJob, pk=pk)
    return Response(job.output)


@api_view(["POST"])
def start_backup(request):
    agent = get_object_or_404(Agent, pk=request.data["pk"])

    msg = {"cmd": "startbackup", "mode": request.data["mode"]}
    r = agent.send_pub(msg)

    if r == "error":
        return notify_Error("Unable to contact agent")

    if r["ret"] == "failed" or agent.backup_running:
        return notify_Error("Backup is already running!")

    job = BackupJob(
        agent=agent,
        pid=r["pid"],
        mode=request.data["mode"],
        proc_name=r["proc_name"],
        cmdline=r["cmdline"],
        started=djangotime.now(),
    )
    job.save()
    return Response(f"Backup started on {agent.hostname}")


@api_view()
def info(request):
    tank = psutil.disk_usage("/")

    used = bytes2human(tank.used)
    total = bytes2human(tank.total)

    agents = Agent.objects.count()
    clients = Client.objects.count()

    ret = {"used": used, "total": total, "agents": agents, "clients": clients}
    return Response(ret)


@api_view()
def view_progress(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    job = OffsiteJob.objects.filter(agent=agent).filter(status="running").last()

    if not job:
        return notify_Error("Job does not exist")

    r = agent.salt_api_cmd(
        timeout=9, func="tac_veeam.read_file", arg=[job.logfile_name]
    )

    if r == "error":
        return notify_Error("Unable to contact the agent")

    ret = r.json()["return"][0][agent.client.salt_id]

    resp = json.loads(zlib.decompress(base64.b64decode(ret)))

    return Response(resp)


@api_view()
def start_offsite(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    if agent.offsite_running:
        return notify_Error("An offsite job is already running.")

    r = agent.handle_archives()

    if r == "err":
        return notify_Error("Unable to contact the agent")

    source = agent.onsite_dir + "/"

    rand_name = "".join(random.choice(string.ascii_letters) for _ in range(20))
    log_name = f"/offsitelogs/{rand_name}.log"

    cmd = f"tacticaloffsite --source={source} --dest={agent.path} --limit={agent.rsync_bwlimit} --logfile={log_name}"

    r = agent.salt_api_cmd(
        timeout=10,
        func="cmd.run_bg",
        kwargs={"cmd": cmd, "runas": "tactical", "shell": "/bin/bash"},
    )

    if r == "error":
        return notify_Error("Unable to contact the agent")

    ret = r.json()["return"][0][agent.client.salt_id]

    if not isinstance(ret, dict):
        return notify_Error("Something went wrong")

    try:
        pid = ret["pid"]
    except KeyError:
        return notify_Error("Something went wrong")

    job = OffsiteJob(
        agent=agent,
        pid=pid,
        logfile_name=log_name,
        status="running",
        started=djangotime.now(),
    )
    job.save()

    return Response("Offsite job started!")


@api_view()
def cancel_offsite(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    job = OffsiteJob.objects.filter(agent=agent).filter(status="running").last()

    if not job:
        return notify_Error("Job does not exist")

    r = agent.salt_api_cmd(
        timeout=15,
        func="tac_veeam.kill_offsite_job",
        kwargs={"pid": job.pid, "log": job.logfile_name},
    )

    if r == "error":
        return notify_Error("Unable to contact the agent")

    ret = r.json()["return"][0][agent.client.salt_id]

    if not isinstance(ret, str):
        return notify_Error("Something went wrong")

    if not ret:
        return notify_Error("Job already cancelled")

    job.finished = djangotime.now()
    job.status = "cancelled"
    job.output = json.loads(zlib.decompress(base64.b64decode(ret)))
    job.save(update_fields=["finished", "status", "output"])

    kill_local_rsync_task.delay(agent.path)

    return Response("Job was cancelled!")


class GetBackupSchedule(APIView):
    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)

        if not agent.backup_schedule:
            ret = {
                "backup_schedule": {
                    "fri": [],
                    "mon": [],
                    "sat": [],
                    "sun": [],
                    "thu": [],
                    "tue": [],
                    "wed": [],
                }
            }
            return Response(ret)

        return Response(BackupScheduleSerializer(agent).data)


class AddEditBackupSchedule(APIView):
    def post(self, request):

        data = request.data

        agent = get_object_or_404(Agent, pk=data["pk"])

        mon, tue, wed, thu, fri, sat, sun = [], [], [], [], [], [], []

        if data["mondayTimes"]:
            mon.extend(data["mondayTimes"])

        if data["tuesdayTimes"]:
            tue.extend(data["tuesdayTimes"])

        if data["wednesdayTimes"]:
            wed.extend(data["wednesdayTimes"])

        if data["thursdayTimes"]:
            thu.extend(data["thursdayTimes"])

        if data["fridayTimes"]:
            fri.extend(data["fridayTimes"])

        if data["saturdayTimes"]:
            sat.extend(data["saturdayTimes"])

        if data["sundayTimes"]:
            sun.extend(data["sundayTimes"])

        agent.backup_schedule = {
            "mon": mon,
            "tue": tue,
            "wed": wed,
            "thu": thu,
            "fri": fri,
            "sat": sat,
            "sun": sun,
        }

        agent.save(update_fields=["backup_schedule"])

        return Response("ok")


@api_view(["PATCH"])
def toggle_backup(request):
    agent = get_object_or_404(Agent, pk=request.data["pk"])

    action = "enabled" if request.data["val"] else "disabled"

    agent.backups_enabled = request.data["val"]
    agent.save(update_fields=["backups_enabled"])

    return Response(f"Backups {action} for {agent.hostname}")


@api_view(["PATCH"])
def toggle_offsite(request):
    agent = get_object_or_404(Agent, pk=request.data["pk"])

    action = "enabled" if request.data["val"] else "disabled"

    agent.offsites_enabled = request.data["val"]
    agent.save(update_fields=["offsites_enabled"])

    return Response(f"Offsites {action} for {agent.hostname}")


@api_view()
def get_offsite_settings(request, pk):
    agent = get_object_or_404(Agent, pk=pk)

    return Response(OffsiteSettingsSerializer(agent).data)


@api_view(["PATCH"])
def edit_offsite_settings(request):
    agent = get_object_or_404(Agent, pk=request.data["pk"])

    start = request.data["day_hours"]["min"]
    end = request.data["day_hours"]["max"]

    agent.day_hours = [start, end]
    agent.day_bwlimit = request.data["day_bwlimit"]
    agent.night_bwlimit = request.data["night_bwlimit"]
    agent.limit_during_day = request.data["limit_during_day"]
    agent.limit_during_night = request.data["limit_during_night"]
    agent.offsite_managed = request.data["offsite_managed"]

    agent.save(
        update_fields=[
            "day_hours",
            "day_bwlimit",
            "night_bwlimit",
            "limit_during_day",
            "limit_during_night",
            "offsite_managed",
        ]
    )
    return Response("Setting were updated!")
