"""Modulo 1 - Solicitudes de ayuda de personas afectadas."""
from django.db import models
from django.urls import reverse

from core.choices import TIPOS_SOLICITUD, Urgencia
from core.models import ContactoMixin, RegistroComunitario, UbicacionMixin


class SolicitudAyuda(RegistroComunitario, UbicacionMixin, ContactoMixin):
    """
    Una necesidad publicada por una persona afectada.

    Se publica sin registro y sin moderacion previa. Solo el administrador puede
    cerrarla cuando la ayuda ya llego, o bloquearla si el contenido es falso.
    """

    alias = models.CharField(
        "Nombre o alias",
        max_length=100,
        help_text="Puedes usar un apodo si prefieres no dar tu nombre real.",
    )
    personas_afectadas = models.PositiveIntegerField(
        "Numero de personas afectadas",
        default=1,
        help_text="Cuantas personas necesitan esta ayuda, contandote a ti.",
    )
    tipo_ayuda = models.CharField(
        "Tipo de ayuda necesaria",
        max_length=20,
        choices=TIPOS_SOLICITUD,
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
        "Descripcion",
        help_text="Explica con detalle que necesitas. Entre mas claro, mas facil sera ayudarte.",
    )
    foto = models.ImageField(
        "Foto (opcional)",
        upload_to="solicitudes/%Y/%m/",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Solicitud de ayuda"
        verbose_name_plural = "Solicitudes de ayuda"
        ordering = ["-creado"]
        indexes = [
            models.Index(fields=["estado", "urgencia"]),
            models.Index(fields=["ciudad", "tipo_ayuda"]),
            models.Index(fields=["latitud", "longitud"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_ayuda_display()} en {self.ciudad} ({self.get_urgencia_display()})"

    def get_absolute_url(self):
        return reverse("solicitudes:detalle", args=[self.pk])

    @property
    def coincidencias_activas(self):
        """Ofertas que podrian cubrir esta necesidad."""
        return self.coincidencias.select_related("ayuda").filter(
            ayuda__estado="ACTIVA"
        )

    @property
    def texto_para_compartir(self):
        """
        Mensaje que se envia al compartir la publicacion por WhatsApp.

        Se arma aqui y no en la plantilla para que sea legible y se pueda
        probar. El enlace lo agrega el parcial de compartir.
        """
        return (
            f"🆘 ESTAMOS CONTIGO · Necesitan {self.get_tipo_ayuda_display().lower()} "
            f"en {self.zona}, {self.ciudad}. "
            f"{self.personas_afectadas} persona(s) afectada(s). "
            f"Urgencia {self.get_urgencia_display().lower()}. "
            f"Publicado por la comunidad, sin verificar:"
        )
