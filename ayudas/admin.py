from django.contrib import admin
from django.utils.html import format_html

from ayudas.models import OfertaAyuda
from core.admin import RegistroComunitarioAdmin


@admin.register(OfertaAyuda)
class OfertaAyudaAdmin(RegistroComunitarioAdmin):
    list_display = (
        "id",
        "alias",
        "tipo_ayuda",
        "cantidad",
        "ciudad",
        "zona",
        "disponibilidad",
        "estado",
        "creado",
    )
    list_filter = ("estado", "tipo_ayuda", "disponibilidad", "ciudad", "creado")
    search_fields = ("alias", "ciudad", "zona", "descripcion", "cantidad", "contacto_telefono")
    list_editable = ("estado",)

    fieldsets = (
        ("Gestion del administrador", {
            "fields": ("estado", "nota_admin"),
            "description": (
                "Marca RESUELTA cuando la ayuda ya fue entregada. "
                "Marca BLOQUEADA si el contenido es falso o inapropiado."
            ),
        }),
        ("Quien ofrece", {
            "fields": ("alias", "contacto_telefono", "contacto_email"),
        }),
        ("Que ofrece", {
            "fields": (
                "tipo_ayuda", "cantidad", "descripcion", "disponibilidad",
                "foto", "vista_previa_foto",
            ),
        }),
        ("Ubicacion", {
            "fields": ("ciudad", "zona", "latitud", "longitud"),
        }),
        ("Datos tecnicos", {
            "fields": ("creado", "actualizado", "ip_origen"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("creado", "actualizado", "ip_origen", "vista_previa_foto")

    @admin.display(description="Vista previa de la foto")
    def vista_previa_foto(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height:300px;border-radius:8px">', obj.foto.url
            )
        return "Sin foto"
