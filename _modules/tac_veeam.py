from __future__ import absolute_import
import os
import glob
import psutil
import signal
import zlib
import base64
import json


def read_file(logfile):

    with open(logfile, "r") as f:
        contents = f.read()

    return base64.b64encode(
        zlib.compress(json.dumps(contents).encode("utf-8", errors="ignore"))
    )


def count_backups(onsite_dir):
    total, inc, full = 0, 0, 0
    files = []

    with os.scandir(onsite_dir) as it:
        for f in it:
            file = {}
            if not f.name.startswith(".") and f.is_file():
                total += 1

                if f.name.endswith(".vib"):
                    inc += 1
                elif f.name.endswith(".vbk"):
                    full += 1

                stats = f.stat()

                file["name"] = f.name
                file["size"] = stats.st_size
                file["mtime"] = stats.st_mtime

                files.append(file)

    return {"total": total, "full": full, "inc": inc, "files": files}


def kill_offsite_job(pid, log):
    try:

        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        children.append(parent)
        for p in children:
            p.send_signal(signal.SIGTERM)

        gone, alive = psutil.wait_procs(children, timeout=20, callback=None)
    except Exception as e:
        pass

    try:
        return read_file(log)
    except Exception:
        return False


def job_exists(pid):
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return False

    if proc.name() == "tacticaloffsite":
        return True

    return False
