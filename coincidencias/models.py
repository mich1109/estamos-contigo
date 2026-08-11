"""Modulo 3 - Coincidencias entre necesidades y ayudas disponibles."""
from django.db import models


class Coincidencia(models.Model):
    """
    Sugerencia automatica de que una oferta podria cubrir una necesidad.

    Es solo una sugerencia: no compromete a nadie y no tiene ciclo de vida
    propio. El caso se cierra sobre la solicitud o la oferta, no aqui.
    """

    solicitud = models.ForeignKey(
        "solicitudes.SolicitudAyuda",
        on_delete=models.CASCADE,
        related_name="coincidencias",
        verbose_name="Solicitud",
    )
    ayuda = models.ForeignKey(
        "ayudas.OfertaAyuda",
        on_delete=models.CASCADE,
        related_name="coincidencias",
        verbose_name="Oferta de ayuda",
    )
    score = models.PositiveSmallIntegerField(
        "Nivel de coincidencia",
        default=70,
        help_text="100 si coinciden ciudad y zona; 70 si solo coincide la ciudad.",
    )
    creado = models.DateTimeField("Detectada el", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Coincidencia"
        verbose_name_plural = "Coincidencias"
        ordering = ["-score", "-creado"]
        constraints = [
            models.UniqueConstraint(
                fields=["solicitud", "ayuda"],
                name="coincidencia_unica_solicitud_ayuda",
            )
        ]
        indexes = [models.Index(fields=["score", "creado"])]

    def __str__(self):
        return f"Solicitud #{self.solicitud_id} ↔ Oferta #{self.ayuda_id} ({self.score}%)"

    @property
    def misma_zona(self):
        return self.score >= 100
