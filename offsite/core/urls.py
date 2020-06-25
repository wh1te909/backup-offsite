from django.urls import path
from . import views

urlpatterns = [
    path("info/", views.info),
    path("version/", views.version),
    path("agents/", views.agents),
    path("clients/", views.clients),
    path("offsitejobs/", views.offsite_jobs),
    path("backupjobs/", views.backup_jobs),
    path("<int:pk>/start/", views.start_offsite),
    path("<int:pk>/viewprogress/", views.view_progress),
    path("<int:pk>/cancel/", views.cancel_offsite),
    path("startbackup/", views.start_backup),
    path("<int:pk>/viewoffsiteoutput/", views.view_offsite_output),
    path("backupschedule/", views.AddEditBackupSchedule.as_view()),
    path("<int:pk>/backupschedule/", views.GetBackupSchedule.as_view()),
    path("togglebackup", views.toggle_backup),
    path("toggleoffsite", views.toggle_offsite),
    path("<int:pk>/offsitesettings/", views.get_offsite_settings),
    path("offsitesettings/", views.edit_offsite_settings),
]
