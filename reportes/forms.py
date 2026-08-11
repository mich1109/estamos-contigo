"""Formulario publico del Modulo 6."""
from django import forms

from core.forms import FormularioBase
from reportes.models import ReporteComunitario


class ReporteComunitarioForm(FormularioBase):
    """Reporte abierto: se puede publicar incluso de forma anonima."""

    class Meta:
        model = ReporteComunitario
        fields = [
            "tipo_reporte",
            "ciudad",
            "departamento",
            "zona",
            "latitud",
            "longitud",
            "urgencia",
            "descripcion",
            "foto",
            "reportado_por",
        ]
        widgets = {
            "ciudad": forms.TextInput(attrs={"placeholder": "Ej: Armenia"}),
            "zona": forms.TextInput(attrs={"placeholder": "Ej: Barrio Centro, calle 20 con carrera 15"}),
            "descripcion": forms.Textarea(
                attrs={"placeholder": "Ej: La via esta bloqueada por escombros desde ayer. No pasan vehiculos."}
            ),
            "reportado_por": forms.TextInput(attrs={"placeholder": "Opcional. Puedes dejarlo vacio."}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get("descripcion") or "").strip()
        if len(descripcion) < 15:
            raise forms.ValidationError(
                "Describe la situacion con un poco mas de detalle "
                "(al menos 15 caracteres)."
            )
        return descripcion
