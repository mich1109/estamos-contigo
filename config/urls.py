"""Rutas principales del proyecto ESTAMOS CONTIGO."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ESTAMOS CONTIGO - Administracion"
admin.site.site_title = "ESTAMOS CONTIGO"
admin.site.index_title = "Gestion de la plataforma"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Cambio de idioma. Django guarda la eleccion en la sesion y redirige de
    # vuelta a la pagina donde estaba la persona.
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("core.urls")),
    path("solicitudes/", include("solicitudes.urls")),
    path("ayudas/", include("ayudas.urls")),
    path("mapa/", include("mapa.urls")),
    path("puntos/", include("puntos.urls")),
    path("reportes/", include("reportes.urls")),
    path("informacion/", include("informacion.urls")),
    path("panel/", include("panel.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
