"""
Panel de administracion de ESTAMOS CONTIGO.

Solo accesible para el superusuario. Su funcion principal es cerrar casos que
ya fueron resueltos y retirar contenido falso; el resto de la edicion detallada
se hace desde el admin de Django.
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ayudas.models import OfertaAyuda
from coincidencias.models import Coincidencia
from core.choices import Estado
from informacion.models import InformacionOficial
from puntos.models import PuntoAyuda
from reportes.models import ReporteComunitario
from solicitudes.models import SolicitudAyuda

# Mapa de nombre publico -> modelo, usado por las acciones de estado.
MODELOS = {
    "solicitud": SolicitudAyuda,
    "ayuda": OfertaAyuda,
    "punto": PuntoAyuda,
    "reporte": ReporteComunitario,
}


@staff_member_required
def dashboard(request):
    """Vista principal del panel con metricas y graficos."""
    hace_una_semana = timezone.now() - timedelta(days=7)

    # --- Metricas principales ---
    metricas = {
        "solicitudes_activas": SolicitudAyuda.objects.filter(estado=Estado.ACTIVA).count(),
        "ayudas_activas": OfertaAyuda.objects.filter(estado=Estado.ACTIVA).count(),
        "puntos_activos": PuntoAyuda.objects.filter(estado=Estado.ACTIVA).count(),
        "reportes_abiertos": ReporteComunitario.objects.filter(estado=Estado.ACTIVA).count(),
        "casos_resueltos": (
            SolicitudAyuda.objects.filter(estado=Estado.RESUELTA).count()
            + OfertaAyuda.objects.filter(estado=Estado.RESUELTA).count()
        ),
        "coincidencias": Coincidencia.objects.count(),
        "bloqueados": (
            SolicitudAyuda.objects.filter(estado=Estado.BLOQUEADA).count()
            + OfertaAyuda.objects.filter(estado=Estado.BLOQUEADA).count()
            + PuntoAyuda.objects.filter(estado=Estado.BLOQUEADA).count()
            + ReporteComunitario.objects.filter(estado=Estado.BLOQUEADA).count()
        ),
        "enlaces_oficiales": InformacionOficial.objects.filter(publicada=True).count(),
    }

    # --- Datos para los graficos ---
    por_tipo = list(
        SolicitudAyuda.objects.filter(estado=Estado.ACTIVA)
        .values("tipo_ayuda")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    etiquetas_tipo = dict(SolicitudAyuda._meta.get_field("tipo_ayuda").choices)
    grafico_tipos = {
        "etiquetas": [str(etiquetas_tipo.get(f["tipo_ayuda"], f["tipo_ayuda"])) for f in por_tipo],
        "valores": [f["total"] for f in por_tipo],
    }

    por_urgencia = list(
        SolicitudAyuda.objects.filter(estado=Estado.ACTIVA)
        .values("urgencia")
        .annotate(total=Count("id"))
    )
    orden_urgencia = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    por_urgencia.sort(key=lambda f: orden_urgencia.get(f["urgencia"], 9))
    nombres_urgencia = {"ALTA": "Alta", "MEDIA": "Media", "BAJA": "Baja"}
    grafico_urgencia = {
        "etiquetas": [nombres_urgencia.get(f["urgencia"], f["urgencia"]) for f in por_urgencia],
        "valores": [f["total"] for f in por_urgencia],
    }

    # Publicaciones por dia en los ultimos 7 dias.
    dias = []
    solicitudes_dia = []
    ayudas_dia = []
    for desplazamiento in range(6, -1, -1):
        dia = (timezone.now() - timedelta(days=desplazamiento)).date()
        dias.append(dia.strftime("%d/%m"))
        solicitudes_dia.append(
            SolicitudAyuda.objects.filter(creado__date=dia).count()
        )
        ayudas_dia.append(OfertaAyuda.objects.filter(creado__date=dia).count())

    grafico_actividad = {
        "etiquetas": dias,
        "solicitudes": solicitudes_dia,
        "ayudas": ayudas_dia,
    }

    # --- Listas de trabajo ---
    contexto = {
        "metricas": metricas,
        "grafico_tipos": grafico_tipos,
        "grafico_urgencia": grafico_urgencia,
        "grafico_actividad": grafico_actividad,
        "solicitudes_urgentes": (
            SolicitudAyuda.objects.filter(estado=Estado.ACTIVA, urgencia="ALTA")
            .order_by("-creado")[:8]
        ),
        "solicitudes_recientes": (
            SolicitudAyuda.objects.filter(estado=Estado.ACTIVA).order_by("-creado")[:8]
        ),
        "ayudas_recientes": (
            OfertaAyuda.objects.filter(estado=Estado.ACTIVA).order_by("-creado")[:8]
        ),
        "reportes_recientes": (
            ReporteComunitario.objects.filter(estado=Estado.ACTIVA).order_by("-creado")[:8]
        ),
        "puntos_sin_verificar": (
            PuntoAyuda.objects.filter(estado=Estado.ACTIVA, verificado=False)
            .order_by("-creado")[:8]
        ),
        "coincidencias_recientes": (
            Coincidencia.objects.select_related("solicitud", "ayuda")
            .filter(solicitud__estado=Estado.ACTIVA, ayuda__estado=Estado.ACTIVA)
            .order_by("-score", "-creado")[:10]
        ),
        "nuevos_esta_semana": SolicitudAyuda.objects.filter(
            creado__gte=hace_una_semana
        ).count(),
    }
    return render(request, "panel/dashboard.html", contexto)


@staff_member_required
@require_POST
def cambiar_estado(request, modelo, pk):
    """
    Cierra, bloquea o reactiva un registro.

    Es la accion central del panel: marcar como resuelto lo que ya recibio
    ayuda. Va por POST con CSRF para que no pueda dispararse desde un enlace.
    """
    clase = MODELOS.get(modelo)
    if clase is None:
        messages.error(request, "Tipo de registro desconocido.")
        return redirect("panel:dashboard")

    objeto = get_object_or_404(clase, pk=pk)
    nuevo_estado = request.POST.get("estado", "").strip()

    if nuevo_estado not in Estado.values:
        messages.error(request, "Estado no válido.")
        return redirect(request.POST.get("volver") or "panel:dashboard")

    objeto.estado = nuevo_estado
    objeto.save(update_fields=["estado", "actualizado"])

    textos = {
        Estado.RESUELTA: "Caso cerrado correctamente.",
        Estado.BLOQUEADA: "Registro bloqueado y retirado del sitio público.",
        Estado.ACTIVA: "Registro reactivado y visible de nuevo.",
    }
    messages.success(request, textos.get(nuevo_estado, "Estado actualizado."))

    return redirect(request.POST.get("volver") or "panel:dashboard")


@staff_member_required
@require_POST
def verificar_punto(request, pk):
    """Marca o desmarca un punto de ayuda como verificado."""
    punto = get_object_or_404(PuntoAyuda, pk=pk)
    punto.verificado = request.POST.get("verificado") == "1"
    punto.save(update_fields=["verificado", "actualizado"])

    if punto.verificado:
        messages.success(request, f"'{punto.nombre}' quedó marcado como verificado.")
    else:
        messages.success(request, f"Se quitó la verificación de '{punto.nombre}'.")

    return redirect(request.POST.get("volver") or "panel:dashboard")


@staff_member_required
def moderacion(request):
    """
    Bandeja de moderacion: todo el contenido activo en un solo lugar.

    Permite cerrar o bloquear sin entrar al admin de Django.
    """
    tipo = request.GET.get("tipo", "solicitud")
    estado = request.GET.get("estado", Estado.ACTIVA)
    busqueda = request.GET.get("q", "").strip()

    clase = MODELOS.get(tipo, SolicitudAyuda)
    consulta = clase.objects.all()

    if estado in Estado.values:
        consulta = consulta.filter(estado=estado)

    if busqueda:
        consulta = consulta.filter(ciudad__icontains=busqueda)

    contexto = {
        "registros": consulta.order_by("-creado")[:100],
        "tipo": tipo,
        "estado": estado,
        "busqueda": busqueda,
        "tipos": [
            ("solicitud", "🆘 Necesidades"),
            ("ayuda", "🤝 Ayudas"),
            ("punto", "📍 Puntos de ayuda"),
            ("reporte", "📢 Reportes"),
        ],
        "estados": Estado.choices,
    }
    return render(request, "panel/moderacion.html", contexto)
