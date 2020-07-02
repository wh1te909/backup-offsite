import datetime as dt
import pytz

from django.conf import settings

from .helpers import bytes2human

from rest_framework.serializers import (
    ModelSerializer,
    ReadOnlyField,
    SerializerMethodField,
)

from .models import Agent, Client, OffsiteJob, BackupJob


class BackupScheduleSerializer(ModelSerializer):
    class Meta:
        model = Agent
        fields = ["backup_schedule"]


class OffsiteJobSerializer(ModelSerializer):
    class Meta:
        model = OffsiteJob
        exclude = ["output"]


class OffsiteJobTableSerializer(ModelSerializer):

    hostname = ReadOnlyField(source="agent.hostname")
    client = ReadOnlyField(source="agent.client.name")
    started = SerializerMethodField()
    finished = SerializerMethodField()

    def get_started(self, obj):
        utc = obj.started.replace(tzinfo=pytz.utc)
        la_tz = pytz.timezone("America/Los_Angeles")
        la_time = utc.astimezone(la_tz)
        return dt.datetime.strftime(la_time, "%I:%M %p %A %b/%d/%Y")

    def get_finished(self, obj):
        try:
            utc = obj.finished.replace(tzinfo=pytz.utc)
            la_tz = pytz.timezone("America/Los_Angeles")
            la_time = utc.astimezone(la_tz)
            return dt.datetime.strftime(la_time, "%I:%M %p %A %b/%d/%Y")
        except Exception:
            return "n/a"

    class Meta:
        model = OffsiteJob
        exclude = ["output"]


class BackupJobTableSerializer(ModelSerializer):

    hostname = ReadOnlyField(source="agent.hostname")
    client = ReadOnlyField(source="agent.client.name")
    started = SerializerMethodField()
    finished = SerializerMethodField()

    def get_started(self, obj):
        utc = obj.started.replace(tzinfo=pytz.utc)
        la_tz = pytz.timezone("America/Los_Angeles")
        la_time = utc.astimezone(la_tz)
        return dt.datetime.strftime(la_time, "%I:%M %p %A %b/%d/%Y")

    def get_finished(self, obj):
        try:
            utc = obj.finished.replace(tzinfo=pytz.utc)
            la_tz = pytz.timezone("America/Los_Angeles")
            la_time = utc.astimezone(la_tz)
            return dt.datetime.strftime(la_time, "%I:%M %p %A %b/%d/%Y")
        except Exception:
            return "n/a"

    class Meta:
        model = BackupJob
        exclude = ["output"]


class AgentSerializer(ModelSerializer):

    path = ReadOnlyField()
    size = ReadOnlyField()
    onsite_dir = ReadOnlyField()
    onsite_size = ReadOnlyField()
    raw_size = ReadOnlyField()
    raw_onsite_size = ReadOnlyField()
    offsite_running = ReadOnlyField()
    backup_running = ReadOnlyField()
    offsitejobs = OffsiteJobSerializer(read_only=True, many=True)
    last_offsite_job = ReadOnlyField()
    client_name = ReadOnlyField(source="client.name")
    details = SerializerMethodField()

    def get_details(self, obj):
        if not obj.details:
            return {}

        files = obj.details["files"]
        ret = []
        for file in files:

            if not file["name"].endswith(".vbm"):
                i = {}

                i["name"] = file["name"]
                i["size"] = bytes2human(file["size"])
                i["mtime"] = file["mtime"]

                if file["name"].endswith(".vib"):
                    i["type"] = "inc"
                elif file["name"].endswith(".vbk"):
                    i["type"] = "full"

                ret.append(i)

        return {"inc": obj.details["inc"], "full": obj.details["full"], "files": ret}

    class Meta:
        model = Agent
        fields = "__all__"


class ClientSerializer(ModelSerializer):

    agents = AgentSerializer(read_only=True, many=True)

    class Meta:
        model = Client
        fields = "__all__"


class OffsiteSettingsSerializer(ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            "id",
            "offsite_managed",
            "day_bwlimit",
            "night_bwlimit",
            "day_hours",
            "limit_during_day",
            "limit_during_night",
        ]
