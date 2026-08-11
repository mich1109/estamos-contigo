"""
Utilidades de administracion compartidas.

La app core no registra modelos propios (todos sus modelos son abstractos),
pero define las acciones de cerrar y bloquear que reutilizan las demas apps.
"""
from django.contrib import admin

from core.choices import Estado


@admin.action(description="Cerrar caso (marcar como RESUELTA)")
def accion_cerrar(modeladmin, request, queryset):
    """Cierra los registros seleccionados porque la ayuda ya llego."""
    actualizados = queryset.update(estado=Estado.RESUELTA)
    modeladmin.message_user(
        request,
        f"{actualizados} registro(s) marcado(s) como resuelto(s).",
    )


@admin.action(description="Bloquear (retirar del sitio publico)")
def accion_bloquear(modeladmin, request, queryset):
    """Retira del sitio publico contenido falso o inapropiado."""
    actualizados = queryset.update(estado=Estado.BLOQUEADA)
    modeladmin.message_user(
        request,
        f"{actualizados} registro(s) bloqueado(s) y retirado(s) del sitio publico.",
    )


@admin.action(description="Reactivar (volver a publicar)")
def accion_reactivar(modeladmin, request, queryset):
    """Devuelve al sitio publico un registro cerrado o bloqueado por error."""
    actualizados = queryset.update(estado=Estado.ACTIVA)
    modeladmin.message_user(request, f"{actualizados} registro(s) reactivado(s).")


ACCIONES_ESTADO = [accion_cerrar, accion_bloquear, accion_reactivar]


class RegistroComunitarioAdmin(admin.ModelAdmin):
    """Base para el admin de todos los modelos publicos."""

    actions = ACCIONES_ESTADO
    list_filter = ("estado", "ciudad", "creado")
    readonly_fields = ("creado", "actualizado", "ip_origen")
    date_hierarchy = "creado"
    list_per_page = 40
