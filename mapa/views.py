"""
Modulo 4 - Mapa comunitario.

Expone una vista con el mapa y un endpoint JSON con los marcadores filtrables.
Solo se serializan registros visibles (nunca los bloqueados) y con coordenadas.
"""
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from ayudas.models import OfertaAyuda
from core.choices import TIPOS_OFERTA, Estado, Urgencia
from core.utils import normalizar
from mapa import serializers
from puntos.models import PuntoAyuda, TipoPunto
from reportes.models import ReporteComunitario, TipoReporte
from solicitudes.models import SolicitudAyuda

# Centro aproximado de Colombia, usado cuando no hay marcadores que encuadrar.
CENTRO_COLOMBIA = {"lat": 4.5709, "lng": -74.2973, "zoom": 6}

# Zonas donde se concentra la actividad de la plataforma.
#
# IMPORTANTE: estas coordenadas solo sirven para centrar el mapa rapido en cada
# ciudad. La plataforma NO afirma nada sobre danos, victimas ni gravedad: lo
# unico que se muestra en el mapa es lo que las personas publican. Cualquier
# dato oficial sobre la emergencia debe consultarse en las fuentes oficiales.
ZONAS = [
    # `alias` recoge como escribe la gente su ubicacion: quien vive en Quibdo
    # escribe "Quibdo", no "Choco". Sin esto la zona marcaria cero aunque
    # tenga publicaciones.
    {"nombre": "Chocó", "lat": 5.6947, "lng": -76.6611, "zoom": 9,
     "referencia": "Quibdó y alrededores",
     "alias": ["choco", "chocó", "quibdo", "quibdó", "istmina", "condoto"]},
    {"nombre": "Cali", "lat": 3.4516, "lng": -76.5320, "zoom": 12,
     "referencia": "Valle del Cauca",
     "alias": ["cali", "santiago de cali", "valle del cauca", "yumbo", "jamundi"]},
    {"nombre": "Pereira", "lat": 4.8133, "lng": -75.6961, "zoom": 13,
     "referencia": "Risaralda",
     "alias": ["pereira", "risaralda", "dosquebradas", "la virginia"]},
    {"nombre": "Manizales", "lat": 5.0689, "lng": -75.5174, "zoom": 13,
     "referencia": "Caldas",
     "alias": ["manizales", "caldas", "villamaria", "chinchina"]},
    {"nombre": "Armenia", "lat": 4.5339, "lng": -75.6811, "zoom": 13,
     "referencia": "Quindío",
     "alias": ["armenia", "quindio", "quindío", "calarca", "montenegro", "circasia"]},
]


def mapa(request):
    """Pagina del mapa. Los datos los carga el JavaScript desde el endpoint."""
    ciudades = sorted(
        set(
            list(
                SolicitudAyuda.objects.activas()
                .exclude(ciudad="")
                .values_list("ciudad", flat=True)
                .distinct()
            )
            + list(
                OfertaAyuda.objects.activas()
                .exclude(ciudad="")
                .values_list("ciudad", flat=True)
                .distinct()
            )
            + list(
                PuntoAyuda.objects.activas()
                .exclude(ciudad="")
                .values_list("ciudad", flat=True)
                .distinct()
            )
            + list(
                ReporteComunitario.objects.activas()
                .exclude(ciudad="")
                .values_list("ciudad", flat=True)
                .distinct()
            )
        )
    )

    # Cuantas publicaciones tiene cada zona. Es un conteo real de lo que la
    # comunidad registro, no una estimacion de danos.
    #
    # Se cuenta en Python y no con un filtro de base de datos porque hay que
    # comparar sin tildes ("Quibdo" y "Quibdó" son lo mismo) y contra varios
    # alias por zona. El volumen de ciudades distintas es pequeno.
    ciudades_publicadas = []
    for modelo in (SolicitudAyuda, OfertaAyuda, PuntoAyuda, ReporteComunitario):
        ciudades_publicadas += list(
            modelo.objects.activas().exclude(ciudad="").values_list("ciudad", flat=True)
        )
    ciudades_normalizadas = [normalizar(c) for c in ciudades_publicadas]

    zonas = []
    for zona in ZONAS:
        alias = [normalizar(a) for a in zona["alias"]]
        total = sum(
            1
            for ciudad in ciudades_normalizadas
            if any(a in ciudad or ciudad in a for a in alias)
        )
        zonas.append(dict(zona, publicaciones=total))

    contexto = {
        "centro": CENTRO_COLOMBIA,
        "zonas": zonas,
        "ciudades": ciudades,
        "tipos": TIPOS_OFERTA,
        "urgencias": Urgencia.choices,
        "tipos_punto": TipoPunto.choices,
        "tipos_reporte": TipoReporte.choices,
    }
    return render(request, "mapa/mapa.html", contexto)


def _filtro_comun(consulta, request):
    """Aplica los filtros de ciudad/zona y estado, comunes a las categorias."""
    ciudad = request.GET.get("ciudad", "").strip()
    estado = request.GET.get("estado", "").strip()
    zona = request.GET.get("zona", "").strip()

    # El boton de una zona filtra por todos sus municipios, no solo por su
    # nombre: al pulsar "Choco" deben salir tambien los de Quibdo.
    if zona:
        definicion = next(
            (z for z in ZONAS if normalizar(z["nombre"]) == normalizar(zona)), None
        )
        if definicion:
            filtro = Q()
            for alias in definicion["alias"]:
                filtro |= Q(ciudad__icontains=alias)
            consulta = consulta.filter(filtro)
    elif ciudad:
        consulta = consulta.filter(ciudad__icontains=ciudad)

    if estado in (Estado.ACTIVA, Estado.RESUELTA):
        consulta = consulta.filter(estado=estado)
    else:
        # Por defecto el mapa muestra solo lo vigente.
        consulta = consulta.filter(estado=Estado.ACTIVA)

    # Sin coordenadas no hay marcador que dibujar.
    return consulta.exclude(latitud__isnull=True).exclude(longitud__isnull=True)


def marcadores(request):
    """
    Devuelve los marcadores del mapa en JSON.

    Parametros aceptados (todos opcionales):
      categorias  lista separada por comas: solicitud,ayuda,punto,reporte
      ciudad      texto parcial
      urgencia    ALTA | MEDIA | BAJA (aplica a solicitudes y reportes)
      tipo        codigo de tipo de ayuda (aplica a solicitudes y ayudas)
      estado      ACTIVA | RESUELTA
    """
    pedidas = request.GET.get("categorias", "")
    categorias = {c.strip() for c in pedidas.split(",") if c.strip()}
    if not categorias:
        categorias = {"solicitud", "ayuda", "punto", "reporte"}

    urgencia = request.GET.get("urgencia", "").strip()
    tipo = request.GET.get("tipo", "").strip()

    resultado = []

    if "solicitud" in categorias:
        consulta = _filtro_comun(SolicitudAyuda.objects.visibles(), request)
        if urgencia:
            consulta = consulta.filter(urgencia=urgencia)
        if tipo:
            consulta = consulta.filter(tipo_ayuda=tipo)
        resultado += [serializers.serializar_solicitud(s) for s in consulta]

    if "ayuda" in categorias:
        consulta = _filtro_comun(OfertaAyuda.objects.visibles(), request)
        if tipo:
            consulta = consulta.filter(tipo_ayuda=tipo)
        resultado += [serializers.serializar_ayuda(a) for a in consulta]

    if "punto" in categorias:
        consulta = _filtro_comun(PuntoAyuda.objects.visibles(), request)
        resultado += [serializers.serializar_punto(p) for p in consulta]

    if "reporte" in categorias:
        consulta = _filtro_comun(ReporteComunitario.objects.visibles(), request)
        if urgencia:
            consulta = consulta.filter(urgencia=urgencia)
        resultado += [serializers.serializar_reporte(r) for r in consulta]

    return JsonResponse(
        {"total": len(resultado), "marcadores": resultado},
        json_dumps_params={"ensure_ascii": False},
    )
