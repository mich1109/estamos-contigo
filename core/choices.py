"""
Opciones compartidas por todas las apps de ESTAMOS CONTIGO.

Se centralizan aqui para que el motor de coincidencias pueda comparar
solicitudes y ofertas usando exactamente los mismos codigos.
"""
from django.db import models


class Estado(models.TextChoices):
    """
    Ciclo de vida de todo registro publico.

    El publico solo genera registros ACTIVA. El administrador es el unico que
    puede pasarlos a RESUELTA (cuando ya llego la ayuda) o BLOQUEADA (cuando el
    contenido es falso o inapropiado).
    """

    ACTIVA = "ACTIVA", "Activa"
    RESUELTA = "RESUELTA", "Resuelta"
    BLOQUEADA = "BLOQUEADA", "Bloqueada"


class Urgencia(models.TextChoices):
    ALTA = "ALTA", "Alta"
    MEDIA = "MEDIA", "Media"
    BAJA = "BAJA", "Baja"


class TipoAyuda(models.TextChoices):
    """
    Catalogo unico de tipos de ayuda.

    Las solicitudes y las ofertas comparten este catalogo: es lo que permite
    emparejarlas. Los tipos DONACIONES y MANO_DE_OBRA solo tienen sentido en una
    oferta, pero se dejan en el catalogo comun para no duplicar codigo.
    """

    ALIMENTOS = "ALIMENTOS", "Alimentos"
    AGUA = "AGUA", "Agua"
    ALOJAMIENTO = "ALOJAMIENTO", "Alojamiento"
    ROPA = "ROPA", "Ropa"
    TRANSPORTE = "TRANSPORTE", "Transporte"
    MEDICAMENTOS = "MEDICAMENTOS", "Medicamentos e insumos basicos"
    ELECTRICIDAD = "ELECTRICIDAD", "Carga de celular / electricidad"
    MASCOTAS = "MASCOTAS", "Ayuda para mascotas"
    DONACIONES = "DONACIONES", "Donaciones"
    MANO_DE_OBRA = "MANO_DE_OBRA", "Mano de obra"
    OTRO = "OTRO", "Otro"


# Subconjuntos para los formularios: una persona afectada no "necesita
# donaciones" ni "necesita mano de obra" en el sentido del catalogo.
TIPOS_SOLICITUD = [
    (c.value, c.label)
    for c in TipoAyuda
    if c not in (TipoAyuda.DONACIONES, TipoAyuda.MANO_DE_OBRA)
]

TIPOS_OFERTA = [(c.value, c.label) for c in TipoAyuda]


class Disponibilidad(models.TextChoices):
    INMEDIATA = "INMEDIATA", "Inmediata"
    HOY = "HOY", "Hoy"
    PROXIMOS_DIAS = "PROXIMOS_DIAS", "Proximos dias"


# Iconos por tipo de ayuda, usados en tarjetas y en los popups del mapa.
ICONOS_TIPO = {
    TipoAyuda.ALIMENTOS: "🍚",
    TipoAyuda.AGUA: "💧",
    TipoAyuda.ALOJAMIENTO: "🏠",
    TipoAyuda.ROPA: "👕",
    TipoAyuda.TRANSPORTE: "🚗",
    TipoAyuda.MEDICAMENTOS: "💊",
    TipoAyuda.ELECTRICIDAD: "🔌",
    TipoAyuda.MASCOTAS: "🐾",
    TipoAyuda.DONACIONES: "🎁",
    TipoAyuda.MANO_DE_OBRA: "🛠️",
    TipoAyuda.OTRO: "📦",
}
