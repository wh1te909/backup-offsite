from django.contrib import admin

from .models import Client, Agent, OffsiteJob, BackupJob

admin.site.register(Client)
admin.site.register(Agent)
admin.site.register(OffsiteJob)
admin.site.register(BackupJob)
