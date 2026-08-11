"""Formulario publico del Modulo 1."""
from django import forms

from core.forms import ContactoObligatorioMixin, FormularioBase
from solicitudes.models import SolicitudAyuda


class SolicitudAyudaForm(ContactoObligatorioMixin, FormularioBase):
    """Formulario abierto: cualquier persona publica sin registrarse."""

    class Meta:
        model = SolicitudAyuda
        fields = [
            "alias",
            "ciudad",
            "departamento",
            "zona",
            "latitud",
            "longitud",
            "personas_afectadas",
            "tipo_ayuda",
            "urgencia",
            "descripcion",
            "foto",
            "contacto_telefono",
            "contacto_email",
        ]
        widgets = {
            "alias": forms.TextInput(attrs={"placeholder": "Ej: Maria G. o 'Familia del barrio Centro'"}),
            "ciudad": forms.TextInput(attrs={"placeholder": "Ej: Armenia"}),
            "zona": forms.TextInput(attrs={"placeholder": "Ej: Barrio La Milagrosa, cerca del parque"}),
            "descripcion": forms.Textarea(
                attrs={"placeholder": "Ej: Somos 5 personas, dos son ninos. Necesitamos mercado para tres dias."}
            ),
            "contacto_telefono": forms.TextInput(attrs={"placeholder": "Ej: 300 123 4567", "inputmode": "tel"}),
            "contacto_email": forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"}),
            "personas_afectadas": forms.NumberInput(attrs={"min": 1, "max": 500}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }

    def clean_personas_afectadas(self):
        cantidad = self.cleaned_data.get("personas_afectadas")
        if cantidad is not None and cantidad < 1:
            raise forms.ValidationError("Debe ser al menos 1 persona.")
        if cantidad is not None and cantidad > 500:
            raise forms.ValidationError(
                "Esa cifra es muy alta para una solicitud individual. Si se trata "
                "de una comunidad entera, registra mejor un punto de ayuda."
            )
        return cantidad

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get("descripcion") or "").strip()
        if len(descripcion) < 15:
            raise forms.ValidationError(
                "Describe un poco mas tu situacion para que puedan ayudarte mejor "
                "(al menos 15 caracteres)."
            )
        return descripcion
