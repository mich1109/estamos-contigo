"""
Modulo 5 - Directorio nacional de puntos de ayuda.

La vista principal es un directorio filtrable: la persona elige su ciudad y
que necesita, y ve los lugares fisicos donde puede ir.
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.choices import Estado
from core.utils import normalizar, obtener_ip
from puntos.forms import PuntoAyudaForm
from puntos.models import (
    NECESIDADES,
    DisponibilidadPunto,
    EstadoVerificacion,
    PuntoAyuda,
    TipoPunto,
)

# Opciones del bloque "Quiero ayudar": que puede aportar alguien y donde.
FORMAS_DE_AYUDAR = [
    ("donar", "📦 Donar productos"),
    ("dinero", "💰 Donar dinero"),
    ("sangre", "🩸 Donar sangre"),
    ("comida", "🍲 Donar alimentos"),
    ("ropa", "👕 Donar ropa"),
    ("abrigo", "🛏️ Donar cobijas y colchonetas"),
    ("aseo", "🧼 Donar articulos de aseo"),
    ("bebes", "👶 Donar articulos para bebes"),
    ("animales", "🐶 Ayudar animales"),
]

# Opciones del bloque "Necesito ayuda", en el lenguaje de quien lo necesita.
QUE_NECESITO = [
    ("alojamiento", "🏠 No tengo donde dormir"),
    ("comida", "🍲 Necesito comida"),
    ("agua", "💧 Necesito agua"),
    ("medica", "🩺 Necesito atencion medica"),
    ("abrigo", "🛏️ Necesito cobijas o colchonetas"),
    ("aseo", "🧼 Necesito articulos de aseo"),
    ("bebes", "👶 Necesito panales o articulos de bebe"),
    ("animales", "🐶 Necesito ayuda para una mascota"),
    ("informacion", "📞 Necesito informacion"),
]

# Diccionario auxiliar: necesidad -> tipos de punto que la resuelven.
TIPOS_POR_NECESIDAD = {clave: tipos for clave, _, tipos in NECESIDADES}


def _buscar_texto(consulta, texto):
    """
    Busca en todo lo que describe un punto.

    Incluye los elementos que recibe, para que alguien que busca "panales"
    encuentre el centro de acopio que los esta recogiendo aunque la palabra no
    este en el nombre ni en la descripcion.
    """
    for palabra in texto.split():
        consulta = consulta.filter(
            Q(nombre__icontains=palabra)
            | Q(descripcion__icontains=palabra)
            | Q(ciudad__icontains=palabra)
            | Q(zona__icontains=palabra)
            | Q(direccion__icontains=palabra)
            | Q(elementos_recibidos__icontains=palabra)
            | Q(servicios__icontains=palabra)
            | Q(busqueda_lugar__icontains=normalizar(palabra))
        )
    return consulta


def lista(request):
    """
    Directorio de puntos de ayuda con filtros.

    Filtros aceptados:
      q           texto libre
      ciudad      nombre exacto de la ciudad
      necesidad   clave de NECESIDADES (alojamiento, comida, sangre...)
      tipo        codigo de TipoPunto
      estado      CONFIRMADO | POR_CONFIRMAR | CERRADO
      modo        'necesito' | 'ayudar'  (cambia los atajos que se muestran)
    """
    consulta = PuntoAyuda.objects.visibles().filter(estado=Estado.ACTIVA)

    busqueda = request.GET.get("q", "").strip()
    ciudad = request.GET.get("ciudad", "").strip()
    necesidad = request.GET.get("necesidad", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    verificacion = request.GET.get("estado", "").strip()
    modo = request.GET.get("modo", "").strip()

    if busqueda:
        consulta = _buscar_texto(consulta, busqueda)
    if ciudad:
        consulta = consulta.filter(ciudad__iexact=ciudad)
    if necesidad and necesidad in TIPOS_POR_NECESIDAD:
        consulta = consulta.filter(tipo__in=TIPOS_POR_NECESIDAD[necesidad])
    if tipo:
        consulta = consulta.filter(tipo=tipo)
    if verificacion in EstadoVerificacion.values:
        consulta = consulta.filter(verificacion=verificacion)

    # Municipios con puntos publicados, con su departamento y conteo, para el
    # desplegable. Se ordenan por departamento para que queden agrupados.
    ciudades = (
        PuntoAyuda.objects.visibles()
        .filter(estado=Estado.ACTIVA)
        .exclude(ciudad="")
        .values("ciudad", "departamento")
        .annotate(total=Count("id"))
        .order_by("departamento", "ciudad")
    )

    # Tipos que existen de verdad: no tiene sentido ofrecer un filtro vacio.
    tipos_disponibles = set(
        PuntoAyuda.objects.visibles()
        .filter(estado=Estado.ACTIVA)
        .values_list("tipo", flat=True)
    )
    tipos = [(c, e) for c, e in TipoPunto.choices if c in tipos_disponibles]

    # Los puntos se agrupan por ciudad: 24 tarjetas seguidas se leen como un
    # amontonamiento, y quien busca ayuda solo mira su ciudad.
    #
    # Si la persona ya eligio una ciudad no hace falta agrupar: se muestra la
    # lista plana de esa ciudad.
    consulta = consulta.order_by(
        "ciudad", "-prioritario", "-destacado", "-verificacion", "nombre"
    )

    if ciudad:
        grupos = []
        paginador = Paginator(consulta, 18)
        pagina = paginador.get_page(request.GET.get("page"))
        total = paginador.count
    else:
        pagina = None
        # Se agrupa por municipio, guardando su departamento para mostrarlo
        # como "Manizales — Caldas".
        agrupados = {}
        for punto in consulta:
            clave = (punto.ciudad, punto.departamento or "")
            agrupados.setdefault(clave, []).append(punto)

        # Orden: primero por departamento (para que los municipios del mismo
        # departamento queden juntos), luego los que tienen mas puntos.
        grupos = [
            {
                "ciudad": nombre,
                "departamento": depto,
                "lugar": f"{nombre} — {depto}" if depto else nombre,
                "puntos": lista_puntos,
                "total": len(lista_puntos),
                "confirmados": sum(1 for p in lista_puntos if p.esta_confirmado),
            }
            for (nombre, depto), lista_puntos in sorted(
                agrupados.items(),
                key=lambda par: (par[0][1] or "zz", -len(par[1]), par[0][0]),
            )
        ]
        total = sum(g["total"] for g in grupos)

    contexto = {
        "pagina": pagina,
        "grupos": grupos,
        "total": total,
        "ciudades": ciudades,
        "tipos": tipos,
        "estados": EstadoVerificacion.choices,
        "necesidades": QUE_NECESITO,
        "formas_ayudar": FORMAS_DE_AYUDAR,
        "modo": modo,
        "filtros": {
            "q": busqueda,
            "ciudad": ciudad,
            "necesidad": necesidad,
            "tipo": tipo,
            "estado": verificacion,
            "modo": modo,
        },
        "hay_filtros": bool(busqueda or ciudad or necesidad or tipo or verificacion),
        "total_confirmados": PuntoAyuda.objects.visibles()
        .filter(estado=Estado.ACTIVA, verificacion=EstadoVerificacion.CONFIRMADO)
        .count(),
    }
    return render(request, "puntos/lista.html", contexto)


def detalle(request, pk):
    """Ficha completa de un punto de ayuda."""
    punto = get_object_or_404(PuntoAyuda.objects.visibles(), pk=pk)

    # Otros puntos de la misma ciudad, para que la persona tenga alternativas
    # si este no le sirve o esta cerrado.
    cercanos = (
        PuntoAyuda.objects.visibles()
        .filter(estado=Estado.ACTIVA, ciudad=punto.ciudad)
        .exclude(pk=punto.pk)[:4]
    )

    return render(
        request,
        "puntos/detalle.html",
        {"punto": punto, "cercanos": cercanos},
    )


def crear(request):
    """Formulario publico para reportar un punto de ayuda."""
    if request.method == "POST":
        form = PuntoAyudaForm(request.POST, request.FILES)
        if form.is_valid():
            punto = form.save(commit=False)
            punto.ip_origen = obtener_ip(request)
            # Lo que reporta el publico SIEMPRE entra pendiente de verificar.
            # Solo la administracion puede marcarlo como confirmado.
            punto.verificacion = EstadoVerificacion.POR_CONFIRMAR
            punto.verificado = False
            punto.save()
            messages.success(
                request,
                "Gracias. El punto quedó registrado como PENDIENTE DE "
                "VERIFICACIÓN y será revisado antes de marcarse como confirmado.",
            )
            return redirect("puntos:detalle", pk=punto.pk)
        messages.error(request, "Revisa los campos marcados en rojo.")
    else:
        form = PuntoAyudaForm()

    return render(request, "puntos/formulario.html", {"form": form})
