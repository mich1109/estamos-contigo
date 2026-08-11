"""Vistas publicas del Modulo 1."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.choices import TIPOS_SOLICITUD, Estado, Urgencia
from core.utils import obtener_ip
from solicitudes.forms import SolicitudAyudaForm
from solicitudes.models import SolicitudAyuda


def lista(request):
    """
    Listado publico de necesidades con filtros.

    Los registros bloqueados nunca se muestran. Los resueltos se muestran solo
    si el visitante los pide expresamente con el filtro de estado.
    """
    consulta = SolicitudAyuda.objects.visibles()

    ciudad = request.GET.get("ciudad", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    urgencia = request.GET.get("urgencia", "").strip()
    estado = request.GET.get("estado", "").strip()
    texto = request.GET.get("q", "").strip()

    if ciudad:
        consulta = consulta.filter(ciudad__icontains=ciudad)
    if tipo:
        consulta = consulta.filter(tipo_ayuda=tipo)
    if urgencia:
        consulta = consulta.filter(urgencia=urgencia)
    if estado:
        consulta = consulta.filter(estado=estado)
    else:
        consulta = consulta.filter(estado=Estado.ACTIVA)
    if texto:
        consulta = consulta.filter(descripcion__icontains=texto)

    paginador = Paginator(consulta, 12)
    pagina = paginador.get_page(request.GET.get("page"))

    contexto = {
        "pagina": pagina,
        "total": paginador.count,
        "tipos": TIPOS_SOLICITUD,
        "urgencias": Urgencia.choices,
        "estados": [
            (Estado.ACTIVA.value, "Activas"),
            (Estado.RESUELTA.value, "Resueltas"),
        ],
        "filtros": {
            "ciudad": ciudad,
            "tipo": tipo,
            "urgencia": urgencia,
            "estado": estado,
            "q": texto,
        },
    }
    return render(request, "solicitudes/lista.html", contexto)


def detalle(request, pk):
    """
    Ficha completa de una necesidad.

    Un registro bloqueado no es accesible ni por URL directa.
    """
    solicitud = get_object_or_404(
        SolicitudAyuda.objects.visibles(), pk=pk
    )
    coincidencias = solicitud.coincidencias.select_related("ayuda").filter(
        ayuda__estado=Estado.ACTIVA
    ).order_by("-score")

    return render(
        request,
        "solicitudes/detalle.html",
        {"solicitud": solicitud, "coincidencias": coincidencias},
    )


def crear(request):
    """
    Formulario publico para registrar una necesidad.

    Se publica de inmediato: no hay revision previa ni cuenta de usuario.
    """
    if request.method == "POST":
        form = SolicitudAyudaForm(request.POST, request.FILES)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.ip_origen = obtener_ip(request)
            solicitud.save()
            messages.success(
                request,
                "Tu solicitud fue registrada correctamente y ya está publicada.",
            )
            return redirect("solicitudes:confirmacion", pk=solicitud.pk)
        messages.error(request, "Revisa los campos marcados en rojo.")
    else:
        form = SolicitudAyudaForm()

    return render(request, "solicitudes/formulario.html", {"form": form})


def confirmacion(request, pk):
    """Pantalla posterior al envio, con lo que sigue y las coincidencias halladas."""
    solicitud = get_object_or_404(SolicitudAyuda.objects.visibles(), pk=pk)
    coincidencias = solicitud.coincidencias.select_related("ayuda").filter(
        ayuda__estado=Estado.ACTIVA
    ).order_by("-score")
    return render(
        request,
        "solicitudes/confirmacion.html",
        {"solicitud": solicitud, "coincidencias": coincidencias},
    )
