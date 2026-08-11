from django.contrib import admin
from django.utils.html import format_html

from core.admin import RegistroComunitarioAdmin
from puntos.models import DisponibilidadPunto, EstadoVerificacion, PuntoAyuda


@admin.action(description="🟢 Marcar como CONFIRMADO (fuente oficial)")
def marcar_confirmado(modeladmin, request, queryset):
    """
    Confirma que la informacion proviene de una fuente oficial y sigue vigente.

    Registra la fecha y hora del momento en que se confirma, que es lo que ve
    el publico como "verificado el ...".
    """
    from django.utils import timezone

    ahora = timezone.localtime()
    actualizados = queryset.update(
        verificacion=EstadoVerificacion.CONFIRMADO,
        verificado=True,
        fecha_verificacion=ahora.date(),
        hora_verificacion=ahora.time().replace(microsecond=0),
    )
    modeladmin.message_user(
        request, f"{actualizados} punto(s) confirmado(s) con fecha de hoy."
    )


@admin.action(description="🟡 Marcar como POR CONFIRMAR")
def marcar_por_confirmar(modeladmin, request, queryset):
    actualizados = queryset.update(
        verificacion=EstadoVerificacion.POR_CONFIRMAR, verificado=False
    )
    modeladmin.message_user(
        request, f"{actualizados} punto(s) pendiente(s) de confirmacion."
    )


@admin.action(description="🔴 Marcar como CERRADO o inactivo")
def marcar_cerrado(modeladmin, request, queryset):
    """El lugar dejo de operar: se avisa para que nadie se desplace en vano."""
    actualizados = queryset.update(
        verificacion=EstadoVerificacion.CERRADO,
        disponibilidad=DisponibilidadPunto.CERRADO,
        verificado=False,
    )
    modeladmin.message_user(request, f"{actualizados} punto(s) marcado(s) como cerrado(s).")


@admin.action(description="⭐ Destacar como punto recomendado")
def destacar(modeladmin, request, queryset):
    actualizados = queryset.update(destacado=True)
    modeladmin.message_user(request, f"{actualizados} punto(s) destacado(s).")


@admin.action(description="Quitar destacado")
def quitar_destacado(modeladmin, request, queryset):
    actualizados = queryset.update(destacado=False)
    modeladmin.message_user(request, f"{actualizados} punto(s) sin destacar.")


@admin.action(description="🚨 Marcar como atencion prioritaria")
def marcar_prioritario(modeladmin, request, queryset):
    actualizados = queryset.update(prioritario=True)
    modeladmin.message_user(request, f"{actualizados} punto(s) marcado(s) como prioritario(s).")


@admin.action(description="Quitar atencion prioritaria")
def quitar_prioritario(modeladmin, request, queryset):
    actualizados = queryset.update(prioritario=False)
    modeladmin.message_user(request, f"{actualizados} punto(s) sin prioridad.")


@admin.register(PuntoAyuda)
class PuntoAyudaAdmin(RegistroComunitarioAdmin):
    """Gestion del directorio de puntos de ayuda."""

    list_display = (
        "nombre",
        "señal",
        "tipo",
        "lugar_admin",
        "disponibilidad",
        "marcas",
        "fecha_verificacion",
    )
    list_filter = (
        "verificacion",
        "estado",
        "disponibilidad",
        "departamento",
        "tipo",
        "destacado",
        "prioritario",
        "ciudad",
    )
    search_fields = (
        "nombre", "ciudad", "departamento", "zona", "direccion",
        "descripcion", "contacto", "elementos_recibidos", "fuente_informacion",
    )
    list_editable = ("disponibilidad",)
    list_per_page = 50
    actions = RegistroComunitarioAdmin.actions + [
        marcar_confirmado,
        marcar_por_confirmar,
        marcar_cerrado,
        destacar,
        quitar_destacado,
        marcar_prioritario,
        quitar_prioritario,
    ]

    fieldsets = (
        ("Estado de la informacion", {
            "fields": (
                "verificacion", "fecha_verificacion", "hora_verificacion",
                "fuente_informacion", "url_fuente",
            ),
            "description": (
                "CONFIRMADO solo si la informacion proviene de una fuente "
                "oficial o de una organizacion reconocida, y comprobaste que "
                "sigue vigente. Actualiza la fecha cada vez que verifiques."
            ),
        }),
        ("Visibilidad", {
            "fields": ("estado", "disponibilidad", "destacado", "prioritario", "nota_admin"),
        }),
        ("Datos del punto", {
            "fields": ("nombre", "tipo", "horario", "descripcion", "contacto"),
        }),
        ("Que ofrece y que recibe", {
            "fields": ("servicios", "elementos_recibidos", "elementos_no_recibidos"),
            "description": "Un elemento por linea.",
        }),
        ("Ubicacion", {
            "fields": ("ciudad", "departamento", "zona", "direccion", "latitud", "longitud"),
        }),
        ("Foto", {
            "fields": ("foto", "vista_previa_foto"),
        }),
        ("Datos tecnicos", {
            "fields": ("creado", "actualizado", "ip_origen", "verificado"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("creado", "actualizado", "ip_origen", "vista_previa_foto")

    @admin.display(description="Estado", ordering="verificacion")
    def señal(self, obj):
        return f"{obj.punto_verificacion} {obj.get_verificacion_display()}"

    @admin.display(description="Municipio", ordering="departamento")
    def lugar_admin(self, obj):
        return obj.lugar

    @admin.display(description="Marcas")
    def marcas(self, obj):
        marcas = []
        if obj.prioritario:
            marcas.append("🚨")
        if obj.destacado:
            marcas.append("⭐")
        return " ".join(marcas) or "—"

    def save_model(self, request, obj, form, change):
        """
        Mantiene sincronizada la marca antigua `verificado`.

        El sitio usa `verificado` en algunos lugares heredados; sin esto,
        cambiar el estado nuevo dejaria la interfaz vieja desactualizada.
        """
        obj.verificado = obj.verificacion == EstadoVerificacion.CONFIRMADO
        super().save_model(request, obj, form, change)

    @admin.display(description="Vista previa de la foto")
    def vista_previa_foto(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="max-height:300px;border-radius:8px">', obj.foto.url
            )
        return "Sin foto"
