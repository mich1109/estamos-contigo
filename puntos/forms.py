"""Formulario publico del Modulo 5."""
from django import forms

from core.forms import FormularioBase
from puntos.models import PuntoAyuda


class PuntoAyudaForm(FormularioBase):
    """
    Registro comunitario de un punto de ayuda.

    El campo `verificado` no aparece aqui a proposito: solo la administracion
    puede marcar un punto como verificado, desde el admin de Django.
    """

    class Meta:
        model = PuntoAyuda
        fields = [
            "nombre",
            "tipo",
            "ciudad",
            "departamento",
            "zona",
            "direccion",
            "latitud",
            "longitud",
            "horario",
            "descripcion",
            "servicios",
            "elementos_recibidos",
            "elementos_no_recibidos",
            "foto",
            "contacto",
            "fuente_informacion",
            "url_fuente",
            "disponibilidad",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Ej: Salon comunal La Milagrosa"}),
            "ciudad": forms.TextInput(attrs={"placeholder": "Ej: Armenia"}),
            "zona": forms.TextInput(attrs={"placeholder": "Ej: Barrio La Milagrosa"}),
            "direccion": forms.TextInput(attrs={"placeholder": "Ej: Calle 20 # 15-30"}),
            "horario": forms.TextInput(attrs={"placeholder": "Ej: Todos los dias de 8am a 6pm"}),
            "descripcion": forms.Textarea(
                attrs={"placeholder": "Ej: Se entregan mercados y agua. Tambien reciben donaciones de ropa."}
            ),
            "contacto": forms.TextInput(attrs={"placeholder": "Ej: 300 123 4567 - Sra. Marta"}),
            "fuente_informacion": forms.TextInput(
                attrs={"placeholder": "Ej: Alcaldia de Manizales, o 'Lo vi personalmente'"}
            ),
            "url_fuente": forms.URLInput(
                attrs={"placeholder": "https://... (enlace a la publicacion oficial)"}
            ),
            "servicios": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Un servicio por linea. Ej:\nAlojamiento temporal\nAlimentacion",
            }),
            "elementos_recibidos": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Un elemento por linea. Ej:\nCobijas\nKits de aseo\nPanales",
            }),
            "elementos_no_recibidos": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Un elemento por linea. Ej:\nMedicamentos\nAlimentos perecederos",
            }),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get("descripcion") or "").strip()
        if len(descripcion) < 15:
            raise forms.ValidationError(
                "Describe un poco mas que se hace en este punto (al menos 15 caracteres)."
            )
        return descripcion

    def clean_fuente_informacion(self):
        fuente = (self.cleaned_data.get("fuente_informacion") or "").strip()
        if len(fuente) < 5:
            raise forms.ValidationError(
                "Indica de donde sacaste esta informacion. Ayuda a que otros "
                "sepan que tan confiable es."
            )
        return fuente
