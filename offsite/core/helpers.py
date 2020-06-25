import psutil
from rest_framework import status
from rest_framework.response import Response


notify_Error = lambda msg: Response(msg, status=status.HTTP_400_BAD_REQUEST)


def bytes2human(n):
    symbols = ("KB", "MB", "GB", "TB", "PB", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return "%.1f%s" % (value, s)
    return "%sB" % n


def any_backups_running():
    matches = ["--server", "--partial-dir"]

    for p in psutil.process_iter():
        with p.oneshot():
            if p.name() == "rsync":
                if all(i in p.cmdline() for i in matches):
                    return True

    return False
