"""Vistas publicas del Modulo 6."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.choices import Estado, Urgencia
from core.utils import obtener_ip
from reportes.forms import ReporteComunitarioForm
from reportes.models import ReporteComunitario, TipoReporte


def lista(request):
    """Listado publico de reportes comunitarios con filtros."""
    consulta = ReporteComunitario.objects.visibles()

    ciudad = request.GET.get("ciudad", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    urgencia = request.GET.get("urgencia", "").strip()
    estado = request.GET.get("estado", "").strip()

    if ciudad:
        consulta = consulta.filter(ciudad__icontains=ciudad)
    if tipo:
        consulta = consulta.filter(tipo_reporte=tipo)
    if urgencia:
        consulta = consulta.filter(urgencia=urgencia)
    if estado:
        consulta = consulta.filter(estado=estado)
    else:
        consulta = consulta.filter(estado=Estado.ACTIVA)

    paginador = Paginator(consulta, 12)
    pagina = paginador.get_page(request.GET.get("page"))

    contexto = {
        "pagina": pagina,
        "total": paginador.count,
        "tipos": TipoReporte.choices,
        "urgencias": Urgencia.choices,
        "estados": [
            (Estado.ACTIVA.value, "🟡 Reportados"),
            (Estado.RESUELTA.value, "⚫ Cerrados"),
        ],
        "filtros": {
            "ciudad": ciudad,
            "tipo": tipo,
            "urgencia": urgencia,
            "estado": estado,
        },
    }
    return render(request, "reportes/lista.html", contexto)


def detalle(request, pk):
    """Ficha completa de un reporte comunitario."""
    reporte = get_object_or_404(ReporteComunitario.objects.visibles(), pk=pk)
    return render(request, "reportes/detalle.html", {"reporte": reporte})


def crear(request):
    """Formulario publico para reportar una situacion."""
    if request.method == "POST":
        form = ReporteComunitarioForm(request.POST, request.FILES)
        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.ip_origen = obtener_ip(request)
            reporte.save()
            messages.success(
                request,
                "Tu reporte fue registrado y ya está publicado.",
            )
            return redirect("reportes:detalle", pk=reporte.pk)
        messages.error(request, "Revisa los campos marcados en rojo.")
    else:
        form = ReporteComunitarioForm()

    return render(request, "reportes/formulario.html", {"form": form})
