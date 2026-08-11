from django.apps import AppConfig


class CoincidenciasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "coincidencias"
    verbose_name = "Coincidencias"

    def ready(self):
        # Registra las senales que recalculan coincidencias al guardar
        # una solicitud o una oferta.
        from coincidencias import signals  # noqa: F401
