"""Formulario publico del Modulo 2."""
from django import forms

from ayudas.models import OfertaAyuda
from core.forms import ContactoObligatorioMixin, FormularioBase


class OfertaAyudaForm(ContactoObligatorioMixin, FormularioBase):
    """Formulario abierto: cualquier persona ofrece ayuda sin registrarse."""

    class Meta:
        model = OfertaAyuda
        fields = [
            "alias",
            "ciudad",
            "departamento",
            "zona",
            "latitud",
            "longitud",
            "tipo_ayuda",
            "cantidad",
            "descripcion",
            "disponibilidad",
            "foto",
            "contacto_telefono",
            "contacto_email",
        ]
        widgets = {
            "alias": forms.TextInput(attrs={"placeholder": "Ej: Juan P. o 'Panaderia El Trigal'"}),
            "ciudad": forms.TextInput(attrs={"placeholder": "Ej: Armenia"}),
            "zona": forms.TextInput(attrs={"placeholder": "Ej: Barrio Centro, calle 20"}),
            "cantidad": forms.TextInput(attrs={"placeholder": "Ej: 5 mercados completos"}),
            "descripcion": forms.Textarea(
                attrs={"placeholder": "Ej: Tengo 5 mercados con arroz, aceite, panela y enlatados. Puedo entregarlos en mi local o llevarlos si es cerca."}
            ),
            "contacto_telefono": forms.TextInput(attrs={"placeholder": "Ej: 300 123 4567", "inputmode": "tel"}),
            "contacto_email": forms.EmailInput(attrs={"placeholder": "correo@ejemplo.com"}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get("descripcion") or "").strip()
        if len(descripcion) < 15:
            raise forms.ValidationError(
                "Describe un poco mas lo que ofreces para que sea util "
                "(al menos 15 caracteres)."
            )
        return descripcion

    def clean_cantidad(self):
        cantidad = (self.cleaned_data.get("cantidad") or "").strip()
        if len(cantidad) < 2:
            raise forms.ValidationError(
                "Indica una cantidad concreta. Ej: '5 mercados', '2 habitaciones'."
            )
        return cantidad
