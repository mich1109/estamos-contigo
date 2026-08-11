"""Modulo 2 - Ofertas de ayuda de personas que quieren colaborar."""
from django.db import models
from django.urls import reverse

from core.choices import TIPOS_OFERTA, Disponibilidad
from core.models import ContactoMixin, RegistroComunitario, UbicacionMixin


class OfertaAyuda(RegistroComunitario, UbicacionMixin, ContactoMixin):
    """
    Una ayuda que alguien pone a disposicion de la comunidad.

    Comparte el catalogo de tipos con SolicitudAyuda: es lo que permite
    emparejarlas automaticamente.
    """

    alias = models.CharField(
        "Nombre o alias",
        max_length=100,
        help_text="Puedes usar un apodo, o el nombre de tu organizacion.",
    )
    tipo_ayuda = models.CharField(
        "Tipo de ayuda disponible",
        max_length=20,
        choices=TIPOS_OFERTA,
        db_index=True,
    )
    cantidad = models.CharField(
        "Cantidad disponible",
        max_length=150,
        help_text="Ej: 5 mercados, 2 habitaciones, 20 litros de agua, 1 camioneta.",
    )
    descripcion = models.TextField(
        "Descripcion",
        help_text="Detalla que ofreces y cualquier condicion (horarios, si entregas a domicilio, etc).",
    )
    disponibilidad = models.CharField(
        "Disponibilidad",
        max_length=15,
        choices=Disponibilidad.choices,
        default=Disponibilidad.INMEDIATA,
        db_index=True,
    )
    foto = models.ImageField(
        "Foto (opcional)",
        upload_to="ayudas/%Y/%m/",
        blank=True,
        null=True,
        help_text="Una foto de lo que ofreces ayuda a que las personas confien.",
    )

    class Meta:
        verbose_name = "Oferta de ayuda"
        verbose_name_plural = "Ofertas de ayuda"
        ordering = ["-creado"]
        indexes = [
            models.Index(fields=["estado", "disponibilidad"]),
            models.Index(fields=["ciudad", "tipo_ayuda"]),
            models.Index(fields=["latitud", "longitud"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_ayuda_display()} en {self.ciudad} ({self.cantidad})"

    def get_absolute_url(self):
        return reverse("ayudas:detalle", args=[self.pk])

    @property
    def texto_para_compartir(self):
        """Mensaje que se envia al compartir la publicacion por WhatsApp."""
        return (
            f"🤝 ESTAMOS CONTIGO · Hay {self.get_tipo_ayuda_display().lower()} "
            f"disponible en {self.zona}, {self.ciudad}: {self.cantidad}. "
            f"Disponibilidad: {self.get_disponibilidad_display().lower()}. "
            f"Publicado por la comunidad, sin verificar:"
        )
