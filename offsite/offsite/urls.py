from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from knox import views as knox_views
from accounts.views import LoginView
from core import consumers

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("login/", LoginView.as_view()),
    path("logout/", knox_views.LogoutView.as_view()),
    path("logoutall/", knox_views.LogoutAllView.as_view()),
    path("core/", include("core.urls")),
]

ws_urlpatterns = [
    path("ws/nettop/", consumers.NetTop),
]
