"""
Middleware de seguridad de ESTAMOS CONTIGO.

Django ya trae proteccion CSRF, escapado de plantillas y consultas
parametrizadas (que bloquean la inyeccion SQL). Aqui se agregan las capas que
Django no pone por defecto:

  - Cabeceras HTTP que instruyen al navegador a bloquear ataques comunes.
  - Content Security Policy: aunque alguien lograra inyectar un <script>,
    el navegador se negaria a ejecutarlo.
  - Limite de publicaciones por IP, para que un bot no inunde el sitio.
"""
import time
from collections import defaultdict, deque

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import render

from core.utils import obtener_ip


class CabecerasSeguridadMiddleware:
    """
    Agrega cabeceras de seguridad a todas las respuestas.

    Cada una le dice al navegador que bloquee una familia de ataques. Son
    baratas de aplicar y evitan clases enteras de problemas.
    """

    # Fuentes externas que el sitio necesita de verdad. Todo lo demas queda
    # bloqueado: si alguien inyecta un script apuntando a otro dominio, el
    # navegador no lo carga.
    CSP = "; ".join([
        "default-src 'self'",
        # unsafe-inline es necesario porque Leaflet y los popups del mapa
        # construyen estilos en linea. Se acota a estilos, nunca a scripts.
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com",
        "script-src 'self' https://cdn.jsdelivr.net https://unpkg.com",
        # Las teselas del mapa vienen de OpenStreetMap; las fotos, de este sitio.
        "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com",
        "font-src 'self' data: https://cdn.jsdelivr.net",
        "connect-src 'self'",
        # Nadie puede meter esta pagina dentro de un iframe (clickjacking).
        "frame-ancestors 'none'",
        # Los formularios solo pueden enviarse a este mismo sitio.
        "form-action 'self'",
        "base-uri 'self'",
        "object-src 'none'",
    ])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)

        respuesta["Content-Security-Policy"] = self.CSP
        # No enviar la URL completa a sitios externos: las URLs de detalle
        # pueden revelar que publicacion estaba viendo la persona.
        respuesta["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Nadie necesita la camara, el microfono ni los pagos desde este sitio.
        respuesta["Permissions-Policy"] = (
            "geolocation=(self), camera=(self), microphone=(), payment=(), usb=()"
        )
        respuesta["X-Content-Type-Options"] = "nosniff"
        respuesta["Cross-Origin-Opener-Policy"] = "same-origin"

        return respuesta


class LimitePublicacionesMiddleware:
    """
    Impide que una misma IP publique sin freno.

    Sin registro de usuarios, la IP es la unica senal disponible para frenar a
    un bot que quiera inundar el sitio. El limite es holgado a proposito: en
    una emergencia una persona puede publicar varias veces de forma legitima
    (por ella, por un vecino, por un familiar).

    Se guarda en memoria: es suficiente para un servidor unico y evita
    depender de Redis o de la base de datos en el camino critico.
    """

    # Rutas que crean contenido publico.
    RUTAS_VIGILADAS = (
        "/solicitudes/nueva/",
        "/ayudas/nueva/",
        "/puntos/nuevo/",
        "/reportes/nuevo/",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.historial = defaultdict(deque)

    def _limite(self):
        return getattr(settings, "MAX_PUBLICACIONES_POR_HORA", 15)

    def __call__(self, request):
        if request.method == "POST" and request.path in self.RUTAS_VIGILADAS:
            ip = obtener_ip(request) or "desconocida"
            ahora = time.monotonic()
            ventana = 3600

            envios = self.historial[ip]
            while envios and ahora - envios[0] > ventana:
                envios.popleft()

            if len(envios) >= self._limite():
                return render(
                    request,
                    "core/limite_alcanzado.html",
                    {"limite": self._limite()},
                    status=429,
                )

            envios.append(ahora)

            # Limpieza para que el diccionario no crezca sin control.
            if len(self.historial) > 5000:
                for clave in list(self.historial):
                    if not self.historial[clave]:
                        del self.historial[clave]

        return self.get_response(request)
