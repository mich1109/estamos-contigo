"""
Recalcula todas las coincidencias desde cero.

Uso:
    python manage.py recalcular_coincidencias
"""
from django.core.management.base import BaseCommand

from coincidencias import services


class Command(BaseCommand):
    help = "Borra y vuelve a calcular todas las coincidencias entre necesidades y ayudas."

    def handle(self, *args, **opciones):
        self.stdout.write("Recalculando coincidencias...")
        total = services.recalcular_todo()
        self.stdout.write(
            self.style.SUCCESS(f"Listo. Se detectaron {total} coincidencia(s).")
        )
