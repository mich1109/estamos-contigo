"""
Senales que mantienen las coincidencias al dia.

Cada vez que se guarda una solicitud o una oferta se recalculan sus
coincidencias. Como el volumen esperado es de cientos o pocos miles de
registros por ciudad, hacerlo de forma sincrona es suficiente y evita
introducir una cola de tareas.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from ayudas.models import OfertaAyuda
from coincidencias import services
from core.choices import Estado
from solicitudes.models import SolicitudAyuda


@receiver(post_save, sender=SolicitudAyuda, dispatch_uid="coincidencias_solicitud")
def al_guardar_solicitud(sender, instance, **kwargs):
    """Recalcula las coincidencias de una necesidad recien guardada."""
    if instance.estado == Estado.ACTIVA:
        services.buscar_para_solicitud(instance)


@receiver(post_save, sender=OfertaAyuda, dispatch_uid="coincidencias_oferta")
def al_guardar_oferta(sender, instance, **kwargs):
    """Recalcula las coincidencias de una oferta recien guardada."""
    if instance.estado == Estado.ACTIVA:
        services.buscar_para_ayuda(instance)
