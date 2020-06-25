import asyncio
import psutil
import subprocess
from time import sleep
import random

from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from .helpers import any_backups_running


class NetTop(AsyncWebsocketConsumer):
    async def connect(self):

        user = self.scope["user"]

        if isinstance(user, AnonymousUser):
            await self.close()

        await self.accept()
        self.connected = True
        self.net = asyncio.create_task(self.send_net_top())

    async def disconnect(self, close_code):

        try:
            self.net.cancel()
        except:
            pass

        self.connected = False
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def send_net_top(self):

        while self.connected:

            if not any_backups_running():

                await self.send("0.00 Mb/s")
                await asyncio.sleep(5)

            else:
                pnic_before = psutil.net_io_counters(pernic=True)["ens18"]
                await asyncio.sleep(0.5)
                pnic_after = psutil.net_io_counters(pernic=True)["ens18"]

                bytes_in = (
                    (pnic_after.bytes_recv - pnic_before.bytes_recv) / 125_000 * 2
                )
                nice = "{:.2f}".format(bytes_in)
                await self.send(f"{nice} Mb/s")
