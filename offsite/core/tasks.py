import os
import signal
import psutil
from time import sleep
import zlib
import base64
import json
import random
import string
from loguru import logger

from django.db.models import Q
from django.utils import timezone as djangotime
from django.conf import settings

from offsite.celery import app

from .models import Agent, OffsiteJob, BackupJob

logger.configure(**settings.LOG_CONFIG)


@app.task
def get_offsite_logs_task():
    jobs = OffsiteJob.objects.filter(status="running")

    for job in jobs:
        r = job.agent.salt_api_cmd(
            timeout=10, func="tac_veeam.read_file", arg=[job.logfile_name]
        )

        if r == "error":
            continue

        raw = r.json()["return"][0][job.agent.client.salt_id]

        output = json.loads(zlib.decompress(base64.b64decode(raw)))

        job.output = output
        job.save(update_fields=["output"])

    return "ok"


@app.task
def gather_info_task():
    agents = Agent.objects.all()

    for agent in agents:

        r = agent.salt_api_cmd(
            func="tac_veeam.count_backups", timeout=10, arg=[agent.onsite_dir]
        )

        if r == "error":
            continue

        ret = r.json()["return"][0][agent.client.salt_id]

        if not isinstance(ret, dict):
            logger.error(f"{agent.hostname}: return type is not json")
            continue

        agent.details = ret
        agent.save(update_fields=["details"])

    return "ok"


@app.task
def monitor_offsites_task():

    jobs = OffsiteJob.objects.filter(~Q(status="completed"), ~Q(status="cancelled"))

    if jobs:
        for job in jobs:
            r = job.agent.salt_api_cmd(
                timeout=10, func="tac_veeam.job_exists", arg=[job.pid]
            )

            if r == "error":
                continue

            ret = r.json()["return"][0][job.agent.client.salt_id]

            if not isinstance(ret, bool):
                logger.error(f"{job.agent.hostname}: return type is not bool")
                continue

            if ret:
                continue
            else:
                job.status = "completed"
                job.finished = djangotime.now()
                job.save(update_fields=["status", "finished"])
                logger.info(f"{job.agent.hostname} offsite job completed")
                sleep(1)

                r = job.agent.salt_api_cmd(
                    timeout=10, func="tac_veeam.read_file", arg=[job.logfile_name]
                )

                if r == "error":
                    job.output = "error getting output"

                raw = r.json()["return"][0][job.agent.client.salt_id]

                output = json.loads(zlib.decompress(base64.b64decode(raw)))

                job.output = output
                job.save(update_fields=["output"])

    return "ok"


@app.task
def kill_local_rsync_task(path):

    pids = []

    matches = ["--server", "--partial-dir", path]

    for proc in psutil.process_iter():
        with proc.oneshot():
            if proc.name() == "rsync":
                if all(i in proc.cmdline() for i in matches):
                    pids.append(proc.pid)

    if pids:
        this_proc = os.getpid()
        for pid in pids:
            if pid == this_proc:
                continue

            try:
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                children.append(parent)
                for p in children:
                    p.send_signal(signal.SIGTERM)

                gone, alive = psutil.wait_procs(children, timeout=10, callback=None)
            except Exception:
                pass


@app.task
def monitor_backups_task():
    jobs = BackupJob.objects.filter(status="running")

    for job in jobs:
        agent = job.agent
        r = agent.send_pub({"cmd": "info"}, 7)

        if r == "error":
            continue

        if r["procs"]:
            for proc in r["procs"]:
                if proc["pid"] == job.pid and proc["name"] == job.proc_name:
                    continue
        else:
            logger.info(f"{agent.hostname} backup job completed")
            job.finished = djangotime.now()
            job.status = "completed"
            job.save(update_fields=["finished", "status"])

        sleep(0.5)


@app.task
def incremental_backup_task(pk):

    sleep(random.randint(1, 15))

    agent = Agent.objects.get(pk=pk)
    mode = "backup"

    msg = {"cmd": "startbackup", "mode": mode}

    attempts = 0
    while 1:

        r = agent.send_pub(msg, 7)

        if r == "error":
            attempts += 1
            logger.error(
                f"Unable to contact {agent.hostname} for scheduled incremental backup: attempt {attempts}"
            )

            sleep(1)

        elif r["ret"] == "failed" or agent.backup_running:
            logger.warning(
                f"A backup job on {agent.hostname} is already running. Skipping"
            )
            return

        else:
            attempts = 0

        if attempts == 0 or attempts > 15:
            break

    job = BackupJob(
        agent=agent,
        pid=r["pid"],
        mode=mode,
        proc_name=r["proc_name"],
        cmdline=r["cmdline"],
        started=djangotime.now(),
    )
    job.save()

    logger.info(f"Backup started on {agent.hostname}")
    return "ok"


@app.task
def auto_offsite_task():
    agents = Agent.objects.filter(offsite_managed=True).filter(offsites_enabled=True)

    for agent in agents:
        if agent.offsite_running:
            continue

        r = agent.handle_archives()

        if r == "err":
            continue

        if agent.raw_size == agent.raw_onsite_size:
            continue

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
            continue

        ret = r.json()["return"][0][agent.client.salt_id]

        if not isinstance(ret, dict):
            continue

        try:
            pid = ret["pid"]
        except KeyError:
            continue

        job = OffsiteJob(
            agent=agent,
            pid=pid,
            logfile_name=log_name,
            status="running",
            started=djangotime.now(),
        )
        job.save()

    return "ok"
