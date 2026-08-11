"""Vistas publicas del Modulo 2."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from ayudas.forms import OfertaAyudaForm
from ayudas.models import OfertaAyuda
from core.choices import TIPOS_OFERTA, Disponibilidad, Estado
from core.utils import obtener_ip


def lista(request):
    """Listado publico de ayudas disponibles con filtros."""
    consulta = OfertaAyuda.objects.visibles()

    ciudad = request.GET.get("ciudad", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    disponibilidad = request.GET.get("disponibilidad", "").strip()
    estado = request.GET.get("estado", "").strip()

    if ciudad:
        consulta = consulta.filter(ciudad__icontains=ciudad)
    if tipo:
        consulta = consulta.filter(tipo_ayuda=tipo)
    if disponibilidad:
        consulta = consulta.filter(disponibilidad=disponibilidad)
    if estado:
        consulta = consulta.filter(estado=estado)
    else:
        consulta = consulta.filter(estado=Estado.ACTIVA)

    paginador = Paginator(consulta, 12)
    pagina = paginador.get_page(request.GET.get("page"))

    contexto = {
        "pagina": pagina,
        "total": paginador.count,
        "tipos": TIPOS_OFERTA,
        "disponibilidades": Disponibilidad.choices,
        "estados": [
            (Estado.ACTIVA.value, "Disponibles"),
            (Estado.RESUELTA.value, "Ya entregadas"),
        ],
        "filtros": {
            "ciudad": ciudad,
            "tipo": tipo,
            "disponibilidad": disponibilidad,
            "estado": estado,
        },
    }
    return render(request, "ayudas/lista.html", contexto)


def detalle(request, pk):
    """Ficha completa de una oferta de ayuda."""
    oferta = get_object_or_404(OfertaAyuda.objects.visibles(), pk=pk)
    coincidencias = oferta.coincidencias.select_related("solicitud").filter(
        solicitud__estado=Estado.ACTIVA
    ).order_by("-score")

    return render(
        request,
        "ayudas/detalle.html",
        {"oferta": oferta, "coincidencias": coincidencias},
    )


def crear(request):
    """Formulario publico para registrar una oferta de ayuda."""
    if request.method == "POST":
        form = OfertaAyudaForm(request.POST, request.FILES)
        if form.is_valid():
            oferta = form.save(commit=False)
            oferta.ip_origen = obtener_ip(request)
            oferta.save()
            messages.success(request, "Tu oferta de ayuda fue registrada.")
            return redirect("ayudas:confirmacion", pk=oferta.pk)
        messages.error(request, "Revisa los campos marcados en rojo.")
    else:
        form = OfertaAyudaForm()

    return render(request, "ayudas/formulario.html", {"form": form})


def confirmacion(request, pk):
    """Pantalla posterior al envio, con las necesidades que podria cubrir."""
    oferta = get_object_or_404(OfertaAyuda.objects.visibles(), pk=pk)
    coincidencias = oferta.coincidencias.select_related("solicitud").filter(
        solicitud__estado=Estado.ACTIVA
    ).order_by("-score")
    return render(
        request,
        "ayudas/confirmacion.html",
        {"oferta": oferta, "coincidencias": coincidencias},
    )
