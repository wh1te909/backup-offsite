import os
import sys
import socket
import zmq
import subprocess
import msgpack
import psutil
import signal
import logging
from time import sleep


class BackupAgent:
    def __init__(self):
        self.agentid = self.get_agent_id()
        self.master = "offsite.tacticaltechs.com"
        self.zmq_conn = f"tcp://{self.master}:23956"
        self.veeam_exe = os.path.join(
            "C:\\Program Files\\Veeam\\Endpoint Backup", "Veeam.EndPoint.Manager.exe"
        )
        logging.basicConfig(
            filename=os.path.join(os.getcwd(), "backup.log"),
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def get_agent_id(self):
        cmd = ["wmic", "csproduct", "get", "uuid"]
        r = subprocess.run(cmd, capture_output=True)
        wmic = r.stdout.decode().splitlines()[2].strip()
        hostname = socket.gethostname()
        return f"{hostname}|{wmic}"

    def kill_proc(self, pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            children.append(parent)
            for p in children:
                p.send_signal(signal.SIGTERM)

            gone, alive = psutil.wait_procs(children, timeout=20, callback=None)
        except Exception:
            pass

    def start_backup(self, mode):
        cmd = [self.veeam_exe, mode]
        r = subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None, close_fds=True)
        self.logger.info(f"Backup started with pid {r.pid}")
        return r.pid

    def backups_running(self):

        pids = []

        for proc in psutil.process_iter():
            with proc.oneshot():
                if proc.name() == "Veeam.EndPoint.Manager.exe":
                    pids.append(proc.pid)

        return pids

    def get_procs(self):
        ret = []

        for proc in psutil.process_iter():
            i = {}
            try:
                with proc.oneshot():
                    if proc.name() == "Veeam.EndPoint.Manager.exe":
                        i["name"] = proc.name()
                        i["pid"] = proc.pid
                        i["ppid"] = proc.ppid()
                        i["cmdline"] = proc.cmdline()
                        ret.append(i)
            except Exception:
                continue

        return ret

    def run(self):
        self.logger.info("Backup agent starting")

        context = zmq.Context()

        sock = context.socket(zmq.DEALER)
        sock.setsockopt(zmq.LINGER, 0)
        sock.setsockopt(zmq.TCP_KEEPALIVE, 1)
        sock.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 300)
        sock.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 300)
        sock.setsockopt_string(zmq.IDENTITY, self.agentid)
        sock.connect(self.zmq_conn)

        poll = zmq.Poller()
        poll.register(sock, zmq.POLLIN)

        while 1:
            try:
                sockets = dict(poll.poll(1000))
                
                if sock in sockets:
                    msg = sock.recv()
                    data = msgpack.loads(msg)

                    if data and data["target"] == self.agentid:

                        if data["cmd"] == "startbackup":
                            # make sure backup is not already running
                            running = self.backups_running()

                            if running:
                                payload = {"ret": "failed"}
                            else:
                                pid = self.start_backup(data["mode"])

                                proc = psutil.Process(pid)

                                with proc.oneshot():
                                    name = proc.name()
                                    cmdline = proc.cmdline()

                                payload = {
                                    "ret": "success",
                                    "pid": pid,
                                    "proc_name": name,
                                    "cmdline": cmdline,
                                }

                            payload["id"] = self.agentid
                            sock.send(msgpack.dumps(payload))

                        elif data["cmd"] == "cancelbackup":

                            try:
                                proc = psutil.Process(data["pid"])
                            except psutil.NoSuchProcess:
                                payload = {"ret": "failed"}
                            else:
                                self.kill_proc(data["pid"])
                                self.logger.info(
                                    f"Cancelled backup with pid: {data['pid']}"
                                )
                                payload = {"ret": "success"}

                            payload["id"] = self.agentid
                            sock.send(msgpack.dumps(payload))

                        elif data["cmd"] == "info":
                            procs = self.get_procs()
                            payload = {"ret": "success", "procs": procs, "id": self.agentid}
                            sock.send(msgpack.dumps(payload))

                        elif data["cmd"] == "ping":
                            payload = {
                                "ret": "success",
                                "msg": f"{self.agentid} pong",
                                "id": self.agentid,
                            }
                            sock.send(msgpack.dumps(payload))

                        elif data["cmd"] == "halt":
                            payload = {"ret": "success", "id": self.agentid}
                            sock.send(msgpack.dumps(payload))
                            self.logger.info("Shutting down")
                            break

                        del msg
            except Exception as e:
                self.logger.error(e)
                break
        
        sock.close()
        context.term()


def main():
    agent = BackupAgent()
    agent.run()


if __name__ == "__main__":
    main()
