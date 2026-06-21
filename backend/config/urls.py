"""
SIBO ERP — Enrutador raíz (ROOT_URLCONF).

Bloque 0.2: además del admin de Django, expone una vista temporal en "/" para
verificar que Django responde de verdad (que nginx ya no dé 502). Esa vista se
reemplazará por la UI real en sprints posteriores.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def home(_request):
    """Vista temporal de verificación de arranque."""
    return HttpResponse("SIBO ERP - OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
]
