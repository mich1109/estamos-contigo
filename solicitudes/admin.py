from django.contrib import admin
from django.utils.html import format_html

from core.admin import RegistroComunitarioAdmin
from solicitudes.models import SolicitudAyuda


@admin.register(SolicitudAyuda)
class SolicitudAyudaAdmin(RegistroComunitarioAdmin):
    list_display = (
        "id",
        "alias",
        "tipo_ayuda",
        "urgencia",
        "ciudad",
        "zona",
        "personas_afectadas",
        "estado",
        "creado",
    )
    list_filter = ("estado", "urgencia", "tipo_ayuda", "ciudad", "creado")
    search_fields = ("alias", "ciudad", "zona", "descripcion", "contacto_telefono")
    list_editable = ("estado",)
    readonly_fields = ("creado", "actualizado", "ip_origen", "vista_previa_foto")

    fieldsets = (
        ("Gestion del administrador", {
            "fields": ("estado", "nota_admin"),
            "description": (
                "Marca RESUELTA cuando la ayuda ya llego. "
                "Marca BLOQUEADA si el contenido es falso o inapropiado."
            ),
        }),
        ("Quien solicita", {
            "fields": ("alias", "personas_afectadas", "contacto_telefono", "contacto_email"),
        }),
        ("Que necesita", {
            "fields": ("tipo_ayuda", "urgencia", "descripcion", "foto", "vista_previa_foto"),
        }),
        ("Ubicacion", {
            "fields": ("ciudad", "zona", "latitud", "longitud"),
        }),
        ("Datos tecnicos", {
            "fields": ("creado", "actualizado", "ip_origen"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Vista previa de la foto")
    def vista_previa_foto(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height:300px;border-radius:8px">', obj.foto.url
            )
        return "Sin foto"
