from django.contrib import admin
from django.utils.html import format_html

from informacion.models import InformacionOficial


@admin.register(InformacionOficial)
class InformacionOficialAdmin(admin.ModelAdmin):
    """
    Gestion de los enlaces oficiales.

    Recuerda: aqui solo van enlaces a informacion publicada por instituciones
    reales, con su URL de origen. No escribas comunicados propios ni cifras
    que no provengan de la fuente enlazada.
    """

    list_display = (
        "titulo",
        "institucion",
        "categoria",
        "fecha",
        "destacada",
        "publicada",
        "enlace",
    )
    list_filter = ("categoria", "publicada", "destacada", "institucion", "fecha")
    search_fields = ("titulo", "descripcion", "institucion", "url")
    list_editable = ("destacada", "publicada")
    date_hierarchy = "fecha"
    readonly_fields = ("creado", "actualizado")

    fieldsets = (
        ("Contenido", {
            "fields": ("titulo", "descripcion", "categoria"),
        }),
        ("Fuente oficial", {
            "fields": ("institucion", "url", "fecha"),
            "description": (
                "La URL es obligatoria. Si no puedes enlazar la fuente oficial, "
                "no publiques la entrada."
            ),
        }),
        ("Visibilidad", {
            "fields": ("publicada", "destacada"),
        }),
        ("Datos tecnicos", {
            "fields": ("creado", "actualizado"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Abrir")
    def enlace(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">Ver fuente ↗</a>', obj.url
        )
