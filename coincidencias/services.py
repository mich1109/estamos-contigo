"""
Motor de coincidencias de ESTAMOS CONTIGO.

La regla es deliberadamente simple y auditable: dos registros coinciden cuando
piden y ofrecen lo mismo, en la misma ciudad, y ambos siguen activos.

  - score 100 -> coinciden ciudad Y zona
  - score  70 -> coincide solo la ciudad

La comparacion de textos se hace normalizada (sin tildes, sin mayusculas, sin
espacios sobrantes) en Python, para no depender del collation de la base de
datos. Esto hace que "Armenia", "armenia" y "ARMENIA " se traten igual, tanto
en MySQL como en SQLite.
"""
from core.choices import Estado
from core.utils import normalizar

SCORE_CIUDAD = 70
SCORE_CIUDAD_Y_ZONA = 100


def calcular_score(solicitud, ayuda):
    """
    Devuelve el nivel de coincidencia entre una solicitud y una oferta.

    Devuelve 0 cuando no hay coincidencia alguna, lo que permite usar esta
    funcion tanto para crear coincidencias como para comprobarlas en tests.
    """
    if solicitud.tipo_ayuda != ayuda.tipo_ayuda:
        return 0

    ciudad_solicitud = normalizar(solicitud.ciudad)
    ciudad_ayuda = normalizar(ayuda.ciudad)
    if not ciudad_solicitud or ciudad_solicitud != ciudad_ayuda:
        return 0

    zona_solicitud = normalizar(solicitud.zona)
    zona_ayuda = normalizar(ayuda.zona)
    if zona_solicitud and zona_solicitud == zona_ayuda:
        return SCORE_CIUDAD_Y_ZONA

    return SCORE_CIUDAD


def _candidatas_para_solicitud(solicitud):
    """Ofertas activas del mismo tipo que podrian cubrir esta necesidad."""
    from ayudas.models import OfertaAyuda

    return OfertaAyuda.objects.filter(
        estado=Estado.ACTIVA,
        tipo_ayuda=solicitud.tipo_ayuda,
    ).only("id", "ciudad", "zona", "tipo_ayuda")


def _candidatas_para_ayuda(ayuda):
    """Solicitudes activas del mismo tipo que esta oferta podria cubrir."""
    from solicitudes.models import SolicitudAyuda

    return SolicitudAyuda.objects.filter(
        estado=Estado.ACTIVA,
        tipo_ayuda=ayuda.tipo_ayuda,
    ).only("id", "ciudad", "zona", "tipo_ayuda")


def _guardar(solicitud, ayuda, score):
    """
    Crea o actualiza una coincidencia.

    Usa update_or_create para que reprocesar un registro no duplique filas: la
    restriccion unica sobre (solicitud, ayuda) lo garantiza a nivel de base de
    datos, y esto lo maneja limpiamente a nivel de aplicacion.
    """
    from coincidencias.models import Coincidencia

    coincidencia, creada = Coincidencia.objects.update_or_create(
        solicitud=solicitud,
        ayuda=ayuda,
        defaults={"score": score},
    )
    return coincidencia, creada


def buscar_para_solicitud(solicitud):
    """
    Busca ofertas que puedan cubrir una necesidad y registra las coincidencias.

    Devuelve la lista de coincidencias detectadas, ordenadas de mayor a menor
    nivel de coincidencia.
    """
    if solicitud.estado != Estado.ACTIVA:
        return []

    encontradas = []
    for oferta in _candidatas_para_solicitud(solicitud):
        score = calcular_score(solicitud, oferta)
        if score:
            coincidencia, _ = _guardar(solicitud, oferta, score)
            encontradas.append(coincidencia)

    encontradas.sort(key=lambda c: c.score, reverse=True)
    return encontradas


def buscar_para_ayuda(ayuda):
    """
    Busca necesidades que esta oferta podria cubrir y registra las coincidencias.

    Devuelve la lista de coincidencias detectadas, ordenadas de mayor a menor
    nivel de coincidencia.
    """
    if ayuda.estado != Estado.ACTIVA:
        return []

    encontradas = []
    for solicitud in _candidatas_para_ayuda(ayuda):
        score = calcular_score(solicitud, ayuda)
        if score:
            coincidencia, _ = _guardar(solicitud, ayuda, score)
            encontradas.append(coincidencia)

    encontradas.sort(key=lambda c: c.score, reverse=True)
    return encontradas


def recalcular_todo():
    """
    Recalcula todas las coincidencias desde cero.

    Util despues de importar datos o si se sospecha que las coincidencias
    quedaron desactualizadas. Se expone como comando de gestion.
    """
    from coincidencias.models import Coincidencia
    from solicitudes.models import SolicitudAyuda

    Coincidencia.objects.all().delete()

    total = 0
    activas = SolicitudAyuda.objects.filter(estado=Estado.ACTIVA)
    for solicitud in activas:
        total += len(buscar_para_solicitud(solicitud))
    return total
