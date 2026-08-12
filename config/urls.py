"""Rutas principales del proyecto ESTAMOS CONTIGO."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

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

# Fotos subidas por el publico.
#
# Django solo las sirve automaticamente con DEBUG=True. En produccion normal
# eso lo haria el servidor web (nginx), pero en Render la aplicacion es quien
# atiende todo, asi que hay que servirlas explicitamente o las imagenes se
# verian rotas.
#
# Es seguro: `serve` solo entrega archivos dentro de MEDIA_ROOT y bloquea
# rutas del tipo "../.." que intenten salir de esa carpeta.


def servir_foto(request, path):
    """
    Entrega una foto subida por el publico.

    La carpeta se consulta en cada peticion en lugar de fijarla al arrancar,
    para que respete la configuracion vigente (los tests la cambian, y en
    Render apunta al disco persistente).
    """
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", servir_foto),
]
