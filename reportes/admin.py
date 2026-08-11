from django.contrib import admin
from django.utils.html import format_html

from core.admin import RegistroComunitarioAdmin
from reportes.models import ReporteComunitario


@admin.register(ReporteComunitario)
class ReporteComunitarioAdmin(RegistroComunitarioAdmin):
    list_display = (
        "id",
        "tipo_reporte",
        "urgencia",
        "ciudad",
        "zona",
        "estado_visible",
        "estado",
        "creado",
    )
    list_filter = ("estado", "urgencia", "tipo_reporte", "ciudad", "creado")
    search_fields = ("ciudad", "zona", "descripcion", "reportado_por")
    list_editable = ("estado",)
    readonly_fields = ("creado", "actualizado", "ip_origen", "vista_previa_foto")

    fieldsets = (
        ("Gestion del administrador", {
            "fields": ("estado", "nota_admin"),
            "description": (
                "ACTIVA se muestra como 'Reportado'. RESUELTA se muestra como "
                "'Cerrado'. BLOQUEADA lo retira del sitio publico."
            ),
        }),
        ("Contenido del reporte", {
            "fields": ("tipo_reporte", "urgencia", "descripcion", "foto", "vista_previa_foto"),
        }),
        ("Ubicacion", {
            "fields": ("ciudad", "zona", "latitud", "longitud"),
        }),
        ("Quien reporta", {
            "fields": ("reportado_por",),
        }),
        ("Datos tecnicos", {
            "fields": ("creado", "actualizado", "ip_origen"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Visible como")
    def estado_visible(self, obj):
        return f"{obj.punto_estado} {obj.estado_publico}"

    @admin.display(description="Vista previa de la foto")
    def vista_previa_foto(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height:300px;border-radius:8px">', obj.foto.url
            )
        return "Sin foto"
