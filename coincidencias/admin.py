from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from coincidencias.models import Coincidencia


@admin.register(Coincidencia)
class CoincidenciaAdmin(admin.ModelAdmin):
    """
    Vista de solo lectura de las coincidencias detectadas.

    Las coincidencias las genera el sistema automaticamente; no se crean ni se
    editan a mano. El administrador las consulta para saber quien podria
    ayudar a quien, y luego cierra la solicitud o la oferta correspondiente.
    """

    list_display = (
        "id",
        "enlace_solicitud",
        "enlace_ayuda",
        "score",
        "ciudad_solicitud",
        "creado",
    )
    list_filter = ("score", "creado", "solicitud__ciudad", "solicitud__urgencia")
    search_fields = (
        "solicitud__ciudad",
        "solicitud__zona",
        "ayuda__ciudad",
        "ayuda__zona",
    )
    readonly_fields = ("solicitud", "ayuda", "score", "creado")
    date_hierarchy = "creado"
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("solicitud", "ayuda")

    @admin.display(description="Necesidad", ordering="solicitud__id")
    def enlace_solicitud(self, obj):
        url = reverse("admin:solicitudes_solicitudayuda_change", args=[obj.solicitud_id])
        return format_html(
            '<a href="{}">#{} {} · {}</a>',
            url,
            obj.solicitud_id,
            obj.solicitud.get_tipo_ayuda_display(),
            obj.solicitud.get_urgencia_display(),
        )

    @admin.display(description="Ayuda disponible", ordering="ayuda__id")
    def enlace_ayuda(self, obj):
        url = reverse("admin:ayudas_ofertaayuda_change", args=[obj.ayuda_id])
        return format_html(
            '<a href="{}">#{} {} · {}</a>',
            url,
            obj.ayuda_id,
            obj.ayuda.get_tipo_ayuda_display(),
            obj.ayuda.cantidad,
        )

    @admin.display(description="Ciudad", ordering="solicitud__ciudad")
    def ciudad_solicitud(self, obj):
        return obj.solicitud.ciudad
