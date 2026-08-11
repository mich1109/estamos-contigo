"""Vistas de la app core: pagina de inicio y aviso legal."""
from django.db.models import Q
from django.shortcuts import render

from ayudas.models import OfertaAyuda
from coincidencias.models import Coincidencia
from core.choices import TIPOS_OFERTA, TIPOS_SOLICITUD, Estado
from core.utils import normalizar
from puntos.models import PuntoAyuda, TipoPunto
from reportes.models import ReporteComunitario, TipoReporte
from solicitudes.models import SolicitudAyuda

# Cuantas publicaciones se muestran en cada pestana de la portada antes de
# mandar al listado completo.
POR_PESTANA = 9

# Cuantas entradas tiene el muro de actividad reciente.
ACTIVIDAD = 12


def _actividad_reciente():
    """
    Une las publicaciones de las cuatro secciones en una sola lista ordenada.

    Es el "muro" de la portada: deja ver de un vistazo todo lo que la comunidad
    esta registrando, sin importar en que modulo lo hizo.
    """
    solicitudes = SolicitudAyuda.objects.activas().order_by("-creado")[:ACTIVIDAD]
    ofertas = OfertaAyuda.objects.activas().order_by("-creado")[:ACTIVIDAD]
    puntos = PuntoAyuda.objects.activas().order_by("-creado")[:ACTIVIDAD]
    reportes = ReporteComunitario.objects.activas().order_by("-creado")[:ACTIVIDAD]

    entradas = []

    for s in solicitudes:
        entradas.append({
            "tipo": "solicitud",
            "etiqueta": "Necesita ayuda",
            "icono": "🆘",
            "titulo": s.get_tipo_ayuda_display(),
            "detalle": f"{s.personas_afectadas} persona(s) · urgencia {s.get_urgencia_display().lower()}",
            "quien": s.alias,
            "ciudad": s.ciudad,
            "zona": s.zona,
            "creado": s.creado,
            "url": s.get_absolute_url(),
            "foto": s.foto if s.foto else None,
        })

    for o in ofertas:
        entradas.append({
            "tipo": "ayuda",
            "etiqueta": "Ofrece ayuda",
            "icono": "🤝",
            "titulo": o.get_tipo_ayuda_display(),
            "detalle": o.cantidad,
            "quien": o.alias,
            "ciudad": o.ciudad,
            "zona": o.zona,
            "creado": o.creado,
            "url": o.get_absolute_url(),
            "foto": o.foto if o.foto else None,
        })

    for p in puntos:
        entradas.append({
            "tipo": "punto",
            "etiqueta": "Punto de ayuda",
            "icono": "📍",
            "titulo": p.nombre,
            "detalle": p.get_tipo_display(),
            "quien": "",
            "ciudad": p.ciudad,
            "zona": p.zona,
            "creado": p.creado,
            "url": p.get_absolute_url(),
            "foto": p.foto if p.foto else None,
        })

    for r in reportes:
        entradas.append({
            "tipo": "reporte",
            "etiqueta": "Reporte comunitario",
            "icono": r.icono,
            "titulo": r.get_tipo_reporte_display(),
            "detalle": f"Urgencia {r.get_urgencia_display().lower()}",
            "quien": r.reportado_por or "Anónimo",
            "ciudad": r.ciudad,
            "zona": r.zona,
            "creado": r.creado,
            "url": r.get_absolute_url(),
            "foto": r.foto if r.foto else None,
        })

    entradas.sort(key=lambda e: e["creado"], reverse=True)
    return entradas[:ACTIVIDAD]


def _codigos_que_coinciden(palabra, opciones):
    """
    Traduce lo que escribe la persona al codigo interno del catalogo.

    Alguien busca "alojamiento", pero en la base de datos el campo guarda
    "ALOJAMIENTO" como codigo y el texto visible vive solo en las opciones del
    modelo. Sin esta traduccion, buscar por tipo de ayuda no encontraria nada.
    """
    palabra = normalizar(palabra)
    return [
        codigo
        for codigo, etiqueta in opciones
        if palabra in normalizar(etiqueta) or palabra in normalizar(codigo)
    ]


def _buscar(consulta, texto, campos, campo_tipo=None, opciones_tipo=None):
    """
    Busca un texto libre en varios campos a la vez.

    Cada palabra debe aparecer en alguno de los campos, asi "mercado armenia"
    encuentra lo que menciona mercado Y esta en Armenia, sin importar el orden
    en que se escriban.

    Si se indica `campo_tipo`, la palabra tambien se compara contra el catalogo
    de tipos: buscar "alojamiento" encuentra las publicaciones de ese tipo
    aunque la palabra no aparezca en la descripcion.
    """
    for palabra in texto.split():
        alternativas = Q()
        for campo in campos:
            alternativas |= Q(**{f"{campo}__icontains": palabra})

        # Busqueda de lugar sin tildes: quien escribe "medellin" en el celular
        # debe encontrar "Medellín".
        alternativas |= Q(busqueda_lugar__icontains=normalizar(palabra))

        if campo_tipo and opciones_tipo:
            codigos = _codigos_que_coinciden(palabra, opciones_tipo)
            if codigos:
                alternativas |= Q(**{f"{campo_tipo}__in": codigos})

        consulta = consulta.filter(alternativas)
    return consulta


def inicio(request):
    """
    Portada de la plataforma.

    Muestra de entrada las dos pestanas que importan (quien necesita ayuda y
    quien la ofrece) con sus publicaciones ya visibles, mas un muro con todo lo
    que la comunidad esta registrando en las otras secciones.

    Acepta busqueda por texto libre y filtros por ciudad y tipo de ayuda, para
    que alguien pueda encontrar lo suyo sin salir de la portada.
    """
    busqueda = request.GET.get("q", "").strip()
    ciudad = request.GET.get("ciudad", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    # Que pestana viene abierta. Se conserva al filtrar.
    pestana = request.GET.get("ver", "necesidades")
    if pestana not in ("necesidades", "ayudas"):
        pestana = "necesidades"

    solicitudes = SolicitudAyuda.objects.activas()
    ofertas = OfertaAyuda.objects.activas()

    if ciudad:
        solicitudes = solicitudes.filter(ciudad__icontains=ciudad)
        ofertas = ofertas.filter(ciudad__icontains=ciudad)
    if tipo:
        solicitudes = solicitudes.filter(tipo_ayuda=tipo)
        ofertas = ofertas.filter(tipo_ayuda=tipo)
    if busqueda:
        solicitudes = _buscar(
            solicitudes,
            busqueda,
            ["descripcion", "ciudad", "zona", "alias"],
            campo_tipo="tipo_ayuda",
            opciones_tipo=TIPOS_SOLICITUD,
        )
        ofertas = _buscar(
            ofertas,
            busqueda,
            ["descripcion", "ciudad", "zona", "alias", "cantidad"],
            campo_tipo="tipo_ayuda",
            opciones_tipo=TIPOS_OFERTA,
        )

    # Las urgentes primero: en una emergencia el orden importa.
    orden_urgencia = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    solicitudes_lista = sorted(
        solicitudes.order_by("-creado")[:60],
        key=lambda s: (orden_urgencia.get(s.urgencia, 9), -s.creado.timestamp()),
    )[:POR_PESTANA]

    ofertas_lista = list(ofertas.order_by("-creado")[:POR_PESTANA])

    # Ciudades con actividad, para el desplegable del filtro.
    ciudades = sorted(
        set(
            list(SolicitudAyuda.objects.activas().exclude(ciudad="")
                 .values_list("ciudad", flat=True))
            + list(OfertaAyuda.objects.activas().exclude(ciudad="")
                   .values_list("ciudad", flat=True))
        )
    )

    # Cuando alguien busca, tambien se le muestran los puntos y reportes que
    # coinciden: si busca "agua en Armenia" le sirve saber que hay un punto de
    # agua alli, no solo quien la pide.
    puntos_encontrados = []
    reportes_encontrados = []
    if busqueda:
        puntos_encontrados = list(
            _buscar(
                PuntoAyuda.objects.activas(),
                busqueda,
                ["nombre", "descripcion", "ciudad", "zona", "direccion"],
                campo_tipo="tipo",
                opciones_tipo=TipoPunto.choices,
            ).order_by("-verificado", "-creado")[:6]
        )
        reportes_encontrados = list(
            _buscar(
                ReporteComunitario.objects.activas(),
                busqueda,
                ["descripcion", "ciudad", "zona"],
                campo_tipo="tipo_reporte",
                opciones_tipo=TipoReporte.choices,
            ).order_by("-creado")[:6]
        )

    total_solicitudes = solicitudes.count()
    total_ofertas = ofertas.count()

    contexto = {
        "pestana": pestana,
        "solicitudes": solicitudes_lista,
        "ofertas": ofertas_lista,
        "total_solicitudes": total_solicitudes,
        "total_ofertas": total_ofertas,
        "hay_mas_solicitudes": total_solicitudes > POR_PESTANA,
        "hay_mas_ofertas": total_ofertas > POR_PESTANA,
        "puntos_encontrados": puntos_encontrados,
        "reportes_encontrados": reportes_encontrados,
        "resultados_busqueda": (
            total_solicitudes + total_ofertas
            + len(puntos_encontrados) + len(reportes_encontrados)
        ),
        "actividad": _actividad_reciente(),
        # --- Panel publico de resumen ---
        "resumen": {
            "solicitudes": SolicitudAyuda.objects.activas().count(),
            "ofertas": OfertaAyuda.objects.activas().count(),
            "puntos": PuntoAyuda.objects.activas().count(),
            "reportes": ReporteComunitario.objects.activas().count(),
            "coincidencias": Coincidencia.objects.filter(
                solicitud__estado=Estado.ACTIVA, ayuda__estado=Estado.ACTIVA
            ).count(),
            "entregadas": (
                SolicitudAyuda.objects.filter(estado=Estado.RESUELTA).count()
                + OfertaAyuda.objects.filter(estado=Estado.RESUELTA).count()
            ),
        },
        "total_puntos": PuntoAyuda.objects.activas().count(),
        "total_reportes": ReporteComunitario.objects.activas().count(),
        "ayudas_entregadas": (
            SolicitudAyuda.objects.filter(estado=Estado.RESUELTA).count()
            + OfertaAyuda.objects.filter(estado=Estado.RESUELTA).count()
        ),
        "ciudades": ciudades,
        "tipos": TIPOS_OFERTA,
        "filtros": {"q": busqueda, "ciudad": ciudad, "tipo": tipo},
        "hay_filtros": bool(busqueda or ciudad or tipo),
        "busqueda": busqueda,
    }
    return render(request, "core/inicio.html", contexto)


def aviso_legal(request):
    """Explica que es y que no es esta plataforma."""
    return render(request, "core/aviso_legal.html")
