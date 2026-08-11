"""Filtros de plantilla de ESTAMOS CONTIGO."""
import re
from urllib.parse import quote

from django import template

from core.choices import ICONOS_TIPO, Estado, Urgencia

register = template.Library()


@register.filter
def whatsapp(numero):
    """
    Convierte un telefono escrito por el usuario en el formato que espera wa.me.

    Las personas escriben "300 123 4567", "+57 300-123-4567" o "(300) 1234567".
    wa.me necesita solo digitos con indicativo de pais. Si el numero ya trae el
    57 al inicio se respeta; si es un celular colombiano de 10 digitos se le
    antepone. Devuelve cadena vacia si no parece un numero utilizable, para que
    la plantilla pueda ocultar el boton.
    """
    if not numero:
        return ""

    digitos = re.sub(r"\D", "", str(numero))

    if not digitos:
        return ""

    # Ya viene con indicativo de Colombia.
    if digitos.startswith("57") and len(digitos) >= 12:
        return digitos

    # Celular colombiano: 10 digitos empezando por 3.
    if len(digitos) == 10 and digitos.startswith("3"):
        return "57" + digitos

    # Fijo con indicativo de ciudad, o cualquier otro formato razonable.
    if 7 <= len(digitos) <= 15:
        return digitos if len(digitos) > 10 else "57" + digitos

    return ""


@register.filter
def urlcodificar(texto):
    """Codifica un texto para meterlo en una URL sin romperla."""
    return quote(str(texto or ""), safe="")


@register.filter
def icono_tipo(codigo):
    """Devuelve el emoji correspondiente a un tipo de ayuda."""
    return ICONOS_TIPO.get(codigo, "📦")


@register.filter
def clase_urgencia(codigo):
    """Clase CSS segun el nivel de urgencia."""
    return {
        Urgencia.ALTA: "urgencia-alta",
        Urgencia.MEDIA: "urgencia-media",
        Urgencia.BAJA: "urgencia-baja",
    }.get(codigo, "urgencia-media")


@register.filter
def punto_urgencia(codigo):
    """Circulo de color segun el nivel de urgencia."""
    return {
        Urgencia.ALTA: "🔴",
        Urgencia.MEDIA: "🟠",
        Urgencia.BAJA: "🟢",
    }.get(codigo, "🟠")


@register.filter
def clase_estado(codigo):
    """Clase CSS de la insignia de estado."""
    return {
        Estado.ACTIVA: "estado-activa",
        Estado.RESUELTA: "estado-resuelta",
        Estado.BLOQUEADA: "estado-bloqueada",
    }.get(codigo, "estado-activa")


@register.simple_tag
def query_actual(request, **kwargs):
    """
    Reconstruye la query string cambiando solo los parametros indicados.

    Sirve para que la paginacion conserve los filtros activos.
    """
    parametros = request.GET.copy()
    for clave, valor in kwargs.items():
        if valor is None or valor == "":
            parametros.pop(clave, None)
        else:
            parametros[clave] = valor
    return parametros.urlencode()
