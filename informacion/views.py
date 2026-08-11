"""Vistas publicas del Modulo 7."""
from django.shortcuts import render

from informacion.models import CategoriaInformacion, InformacionOficial


def lista(request):
    """
    Listado de enlaces oficiales, agrupados por categoria.

    Solo se muestran las entradas marcadas como publicadas.
    """
    consulta = InformacionOficial.objects.filter(publicada=True)

    categoria = request.GET.get("categoria", "").strip()
    institucion = request.GET.get("institucion", "").strip()

    if categoria:
        consulta = consulta.filter(categoria=categoria)
    if institucion:
        consulta = consulta.filter(institucion__icontains=institucion)

    contexto = {
        "entradas": consulta,
        "total": consulta.count(),
        "categorias": CategoriaInformacion.choices,
        "filtros": {"categoria": categoria, "institucion": institucion},
    }
    return render(request, "informacion/lista.html", contexto)
