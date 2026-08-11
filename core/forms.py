"""Formulario base compartido por los formularios publicos."""
from django import forms

from core.utils import validar_imagen, validar_texto_publico


class FormularioBase(forms.ModelForm):
    """
    Base de todos los formularios publicos.

    Hace tres cosas:
      - Aplica las clases de Bootstrap sin repetirlas en cada widget.
      - Incluye un campo trampa (honeypot) que los bots rellenan y las
        personas no ven: si viene lleno, se descarta el envio.
      - Limpia el texto de cada campo antes de guardarlo.
    """

    # Campo trampa. Se llama "website" porque es lo que los bots buscan; queda
    # oculto por CSS y con autocomplete apagado para que ningun navegador lo
    # rellene solo.
    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "class": "campo-trampa",
            "tabindex": "-1",
            "autocomplete": "off",
            "aria-hidden": "true",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre == "website":
                continue

            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select form-select-lg")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "form-control")
                widget.attrs.setdefault("rows", 4)
                widget.attrs.setdefault("maxlength", 3000)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "form-control")
                widget.attrs.setdefault("accept", "image/*")
            else:
                widget.attrs.setdefault("class", "form-control form-control-lg")

    def clean_website(self):
        """Si el campo trampa viene lleno, quien envio es un bot."""
        if self.cleaned_data.get("website"):
            raise forms.ValidationError(
                "No se pudo procesar el envio. Intenta de nuevo."
            )
        return ""

    def clean_foto(self):
        return validar_imagen(self.cleaned_data.get("foto"))

    def clean(self):
        """
        Limpia todo el texto antes de guardarlo.

        Django ya escapa al renderizar, asi que esto no es la defensa contra
        XSS sino una segunda capa: normaliza espacios y rechaza contenido que
        solo tiene sentido en un ataque (etiquetas <script>, urls javascript:).
        """
        datos = super().clean()
        for nombre, valor in list(datos.items()):
            if isinstance(valor, str) and nombre != "website":
                datos[nombre] = validar_texto_publico(valor, nombre, self)
        return datos


class ContactoObligatorioMixin:
    """
    Exige al menos un medio de contacto.

    Sin telefono ni correo la publicacion es inutil: nadie podria responder a
    la necesidad ni aceptar la ayuda ofrecida.
    """

    def clean(self):
        datos = super().clean()
        telefono = (datos.get("contacto_telefono") or "").strip()
        email = (datos.get("contacto_email") or "").strip()
        if not telefono and not email:
            raise forms.ValidationError(
                "Debes dejar al menos un medio de contacto: telefono o correo. "
                "Sin el, nadie podra comunicarse contigo."
            )
        return datos
