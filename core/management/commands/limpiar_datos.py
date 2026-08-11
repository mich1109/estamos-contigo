"""
Deja la plataforma vacia, lista para recibir publicaciones reales.

Borra todas las solicitudes, ofertas, puntos, reportes y coincidencias, junto
con las fotos que se hayan subido. NO toca los usuarios ni los enlaces de
informacion oficial.

Uso:
    python manage.py limpiar_datos            (pide confirmacion)
    python manage.py limpiar_datos --si       (sin preguntar)
"""
from django.core.management.base import BaseCommand

from ayudas.models import OfertaAyuda
from coincidencias.models import Coincidencia
from puntos.models import PuntoAyuda
from reportes.models import ReporteComunitario
from solicitudes.models import SolicitudAyuda


class Command(BaseCommand):
    help = "Borra TODO el contenido publicado. Deja la plataforma vacia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si",
            action="store_true",
            help="No preguntar antes de borrar.",
        )

    def handle(self, *args, **opciones):
        conteos = {
            "solicitudes": SolicitudAyuda.objects.count(),
            "ofertas de ayuda": OfertaAyuda.objects.count(),
            "puntos de ayuda": PuntoAyuda.objects.count(),
            "reportes": ReporteComunitario.objects.count(),
            "coincidencias": Coincidencia.objects.count(),
        }
        total = sum(conteos.values())

        if total == 0:
            self.stdout.write(self.style.SUCCESS("La plataforma ya esta vacia."))
            return

        self.stdout.write("Se van a borrar:")
        for nombre, cantidad in conteos.items():
            if cantidad:
                self.stdout.write(f"  {cantidad} {nombre}")

        if not opciones["si"]:
            self.stdout.write(
                self.style.WARNING("\nEsta accion NO se puede deshacer.")
            )
            respuesta = input("Escribe BORRAR para confirmar: ").strip()
            if respuesta != "BORRAR":
                self.stdout.write("Cancelado. No se borro nada.")
                return

        # Borra tambien los archivos de imagen del disco: al eliminar la fila,
        # Django no borra el archivo asociado por si solo.
        #
        # Se recorre sin filtrar por foto="" porque el campo admite NULL y ese
        # filtro dejaria fuera justamente las filas con foto guardada.
        borradas = 0
        for modelo in (SolicitudAyuda, OfertaAyuda, PuntoAyuda, ReporteComunitario):
            for registro in modelo.objects.all():
                if registro.foto:
                    registro.foto.delete(save=False)
                    borradas += 1
        if borradas:
            self.stdout.write(f"  {borradas} foto(s) eliminada(s) del disco")

        Coincidencia.objects.all().delete()
        SolicitudAyuda.objects.all().delete()
        OfertaAyuda.objects.all().delete()
        PuntoAyuda.objects.all().delete()
        ReporteComunitario.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                "\nListo. La plataforma quedo vacia y lista para publicaciones reales."
            )
        )
        self.stdout.write(
            "Los usuarios y los enlaces de informacion oficial no se tocaron."
        )
