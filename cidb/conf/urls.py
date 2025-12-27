from django.contrib import admin
from django.urls import include, path

from cidb.src.incidents.api.router import api as incidents_api

urlpatterns = [
    path("core/", include("cidb.src.core.urls")),
    path("api/v1/", incidents_api.urls),
    path("admin/", admin.site.urls),
]
