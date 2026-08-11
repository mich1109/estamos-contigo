"""
Prepara el sitio recien publicado: crea el administrador y carga el directorio.

Existe porque el plan gratuito de Render no da acceso a una terminal, y sin
ella no habria forma de ejecutar `createsuperuser` en el servidor.

El usuario y la contrasena se leen de variables de entorno que se configuran
en el panel de Render, nunca del codigo.

Es seguro ejecutarlo en cada despliegue:
  - Si el usuario ya existe, no lo toca ni cambia su contrasena.
  - Si los puntos ya estan cargados, no los duplica.

Uso:
    python manage.py preparar_sitio
"""
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea el administrador inicial y carga el directorio de puntos."

    def handle(self, *args, **opciones):
        Usuario = get_user_model()

        nombre = os.getenv("ADMIN_USUARIO", "").strip()
        clave = os.getenv("ADMIN_CLAVE", "").strip()
        correo = os.getenv("ADMIN_CORREO", "").strip()

        # --- Administrador ---
        if not nombre or not clave:
            self.stdout.write(
                "Sin ADMIN_USUARIO y ADMIN_CLAVE: no se crea administrador.\n"
                "Configuralas en Render > Environment si lo necesitas."
            )
        elif Usuario.objects.filter(username=nombre).exists():
            # No se sobreescribe: si el administrador ya cambio su contrasena,
            # un redespliegue no debe revertirla.
            self.stdout.write(f"El usuario '{nombre}' ya existe. No se modifica.")
        else:
            Usuario.objects.create_superuser(nombre, correo or "", clave)
            self.stdout.write(self.style.SUCCESS(f"Administrador '{nombre}' creado."))
            self.stdout.write(
                self.style.WARNING(
                    "IMPORTANTE: entra al sitio, cambia esta contrasena, y luego "
                    "borra ADMIN_CLAVE de las variables de entorno de Render."
                )
            )

        # --- Directorio de puntos de ayuda ---
        from puntos.models import PuntoAyuda

        if PuntoAyuda.objects.exists():
            total = PuntoAyuda.objects.count()
            self.stdout.write(f"Ya hay {total} punto(s) de ayuda. No se recargan.")
        else:
            self.stdout.write("Cargando el directorio de puntos de ayuda...")
            call_command("cargar_directorio")
