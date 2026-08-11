"""Modulo 6 - Reportes comunitarios de situaciones."""
from django.db import models
from django.urls import reverse

from core.choices import Urgencia
from core.models import RegistroComunitario, UbicacionMixin


class TipoReporte(models.TextChoices):
    DANOS = "DANOS", "Danos visibles en estructuras"
    VIA_BLOQUEADA = "VIA_BLOQUEADA", "Via bloqueada"
    FALTA_AGUA = "FALTA_AGUA", "Falta de agua"
    FALTA_ALIMENTOS = "FALTA_ALIMENTOS", "Falta de alimentos"
    ALOJAMIENTO = "ALOJAMIENTO", "Personas que necesitan alojamiento"
    SERVICIOS = "SERVICIOS", "Sin luz, gas o comunicaciones"
    OTRA = "OTRA", "Otra situacion"


ICONOS_REPORTE = {
    TipoReporte.DANOS: "🏚️",
    TipoReporte.VIA_BLOQUEADA: "🚧",
    TipoReporte.FALTA_AGUA: "💧",
    TipoReporte.FALTA_ALIMENTOS: "🍚",
    TipoReporte.ALOJAMIENTO: "🏠",
    TipoReporte.SERVICIOS: "🔌",
    TipoReporte.OTRA: "⚠️",
}


class ReporteComunitario(RegistroComunitario, UbicacionMixin):
    """
    Una situacion reportada por una persona de la comunidad.

    A diferencia de las solicitudes, un reporte no pide ayuda para alguien en
    concreto: describe una situacion del territorio. Se muestra siempre con la
    leyenda de que fue reportado por un usuario y no esta verificado.

    Los estados que ve el publico son "Reportado" (ACTIVA) y "Cerrado"
    (RESUELTA), gestionados desde el panel del administrador.
    """

    tipo_reporte = models.CharField(
        "Tipo de reporte",
        max_length=20,
        choices=TipoReporte.choices,
        db_index=True,
    )
    urgencia = models.CharField(
        "Nivel de urgencia",
        max_length=10,
        choices=Urgencia.choices,
        default=Urgencia.MEDIA,
        db_index=True,
    )
    descripcion = models.TextField(
        "Descripcion de la situacion",
        help_text="Describe que viste, donde y cuando. Se lo mas concreto posible.",
    )
    foto = models.ImageField(
        "Foto (opcional)",
        upload_to="reportes/%Y/%m/",
        blank=True,
        null=True,
    )
    reportado_por = models.CharField(
        "Nombre o alias de quien reporta",
        max_length=100,
        blank=True,
        help_text="Opcional. Puedes reportar de forma anonima.",
    )

    class Meta:
        verbose_name = "Reporte comunitario"
        verbose_name_plural = "Reportes comunitarios"
        ordering = ["-creado"]
        indexes = [
            models.Index(fields=["estado", "urgencia"]),
            models.Index(fields=["ciudad", "tipo_reporte"]),
            models.Index(fields=["latitud", "longitud"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_reporte_display()} en {self.ciudad}"

    def get_absolute_url(self):
        return reverse("reportes:detalle", args=[self.pk])

    @property
    def icono(self):
        return ICONOS_REPORTE.get(self.tipo_reporte, "⚠️")

    @property
    def estado_publico(self):
        """Etiqueta que ve el publico: Reportado o Cerrado."""
        return "Cerrado" if self.estado == "RESUELTA" else "Reportado"

    @property
    def punto_estado(self):
        return "⚫" if self.estado == "RESUELTA" else "🟡"

    @property
    def texto_para_compartir(self):
        """Mensaje que se envia al compartir el reporte por WhatsApp."""
        return (
            f"📢 ESTAMOS CONTIGO · {self.get_tipo_reporte_display()} "
            f"en {self.zona}, {self.ciudad}. "
            f"Urgencia {self.get_urgencia_display().lower()}. "
            f"Reporte de un usuario de la comunidad, sin verificar:"
        )
