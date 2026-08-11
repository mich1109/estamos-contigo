"""
Convierte los registros de las distintas apps en marcadores para el mapa.

Cada funcion devuelve un diccionario plano y serializable. Los datos de
contacto se incluyen porque el sitio los muestra publicamente junto al aviso de
verificacion; los datos internos (IP de origen, notas del administrador) nunca
salen de aqui.
"""
from core.choices import ICONOS_TIPO


def _base(objeto, categoria):
    """Campos comunes a todo marcador."""
    foto = getattr(objeto, "foto", None)
    return {
        "id": objeto.pk,
        "categoria": categoria,
        "lat": float(objeto.latitud),
        "lng": float(objeto.longitud),
        "ciudad": objeto.ciudad,
        "zona": objeto.zona,
        "estado": objeto.estado,
        "estado_texto": objeto.get_estado_display(),
        "creado": objeto.creado.strftime("%d/%m/%Y %H:%M"),
        "foto": foto.url if foto else "",
    }


def serializar_solicitud(solicitud):
    datos = _base(solicitud, "solicitud")
    datos.update({
        "titulo": solicitud.get_tipo_ayuda_display(),
        "icono": ICONOS_TIPO.get(solicitud.tipo_ayuda, "📦"),
        "tipo": solicitud.tipo_ayuda,
        "tipo_texto": solicitud.get_tipo_ayuda_display(),
        "urgencia": solicitud.urgencia,
        "urgencia_texto": solicitud.get_urgencia_display(),
        "descripcion": solicitud.descripcion,
        "personas": solicitud.personas_afectadas,
        "alias": solicitud.alias,
        "telefono": solicitud.contacto_telefono,
        "email": solicitud.contacto_email,
        "url": solicitud.get_absolute_url(),
    })
    return datos


def serializar_ayuda(ayuda):
    datos = _base(ayuda, "ayuda")
    datos.update({
        "titulo": ayuda.get_tipo_ayuda_display(),
        "icono": ICONOS_TIPO.get(ayuda.tipo_ayuda, "📦"),
        "tipo": ayuda.tipo_ayuda,
        "tipo_texto": ayuda.get_tipo_ayuda_display(),
        "descripcion": ayuda.descripcion,
        "cantidad": ayuda.cantidad,
        "disponibilidad": ayuda.get_disponibilidad_display(),
        "alias": ayuda.alias,
        "telefono": ayuda.contacto_telefono,
        "email": ayuda.contacto_email,
        "url": ayuda.get_absolute_url(),
    })
    return datos


def serializar_punto(punto):
    datos = _base(punto, "punto")
    datos.update({
        "titulo": punto.nombre,
        # Cada tipo de punto lleva su propio emoji en el marcador: albergue,
        # acopio, medico, sangre, alimentacion, agua, informacion...
        "icono": punto.icono,
        "tipo": punto.tipo,
        "tipo_texto": punto.get_tipo_display(),
        "descripcion": punto.descripcion,
        "horario": punto.horario,
        "direccion": punto.direccion,
        "contacto": punto.contacto,
        "fuente": punto.fuente_informacion,
        "verificado": punto.verificado,
        "verificacion": punto.verificacion,
        "verificacion_texto": punto.get_verificacion_display(),
        "punto_verificacion": punto.punto_verificacion,
        "disponibilidad": punto.get_disponibilidad_display(),
        "url": punto.get_absolute_url(),
        "url_como_llegar": punto.url_como_llegar,
        "recibe": punto.lista_recibidos[:6],
        "url_fuente": punto.url_fuente,
        "departamento": punto.departamento,
    })
    return datos


def serializar_reporte(reporte):
    datos = _base(reporte, "reporte")
    datos.update({
        "titulo": reporte.get_tipo_reporte_display(),
        "icono": reporte.icono,
        "tipo": reporte.tipo_reporte,
        "tipo_texto": reporte.get_tipo_reporte_display(),
        "urgencia": reporte.urgencia,
        "urgencia_texto": reporte.get_urgencia_display(),
        "descripcion": reporte.descripcion,
        "reportado_por": reporte.reportado_por or "Anónimo",
        "estado_texto": reporte.estado_publico,
        "url": reporte.get_absolute_url(),
    })
    return datos
