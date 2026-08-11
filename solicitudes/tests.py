"""Tests del Modulo 1: formulario y vistas de solicitudes."""
from django.test import TestCase
from django.urls import reverse

from core.choices import Estado
from solicitudes.forms import SolicitudAyudaForm
from solicitudes.models import SolicitudAyuda

DATOS_VALIDOS = {
    "alias": "Familia Perez",
    "ciudad": "Armenia",
    "zona": "La Milagrosa",
    "personas_afectadas": 5,
    "tipo_ayuda": "ALIMENTOS",
    "urgencia": "ALTA",
    "descripcion": "Somos cinco personas y necesitamos mercado para tres dias.",
    "contacto_telefono": "3001234567",
    "contacto_email": "",
}


class FormularioSolicitudTests(TestCase):
    def test_datos_validos_son_aceptados(self):
        form = SolicitudAyudaForm(data=DATOS_VALIDOS)
        self.assertTrue(form.is_valid(), form.errors)

    def test_sin_ningun_contacto_se_rechaza(self):
        datos = dict(DATOS_VALIDOS, contacto_telefono="", contacto_email="")
        form = SolicitudAyudaForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn("al menos un medio de contacto", str(form.errors))

    def test_solo_correo_es_suficiente(self):
        datos = dict(DATOS_VALIDOS, contacto_telefono="", contacto_email="a@b.com")
        form = SolicitudAyudaForm(data=datos)
        self.assertTrue(form.is_valid(), form.errors)

    def test_descripcion_muy_corta_se_rechaza(self):
        datos = dict(DATOS_VALIDOS, descripcion="Ayuda")
        form = SolicitudAyudaForm(data=datos)
        self.assertFalse(form.is_valid())
        self.assertIn("descripcion", form.errors)

    def test_cero_personas_se_rechaza(self):
        datos = dict(DATOS_VALIDOS, personas_afectadas=0)
        form = SolicitudAyudaForm(data=datos)
        self.assertFalse(form.is_valid())

    def test_cifra_absurda_de_personas_se_rechaza(self):
        datos = dict(DATOS_VALIDOS, personas_afectadas=99999)
        form = SolicitudAyudaForm(data=datos)
        self.assertFalse(form.is_valid())


class VistasSolicitudTests(TestCase):
    def test_el_formulario_carga_sin_iniciar_sesion(self):
        """El publico no se registra: la pagina debe abrir para cualquiera."""
        respuesta = self.client.get(reverse("solicitudes:crear"))
        self.assertEqual(respuesta.status_code, 200)

    def test_publicar_crea_la_solicitud_y_redirige(self):
        respuesta = self.client.post(reverse("solicitudes:crear"), DATOS_VALIDOS)
        self.assertEqual(SolicitudAyuda.objects.count(), 1)
        solicitud = SolicitudAyuda.objects.first()
        self.assertEqual(solicitud.estado, Estado.ACTIVA)
        self.assertRedirects(
            respuesta, reverse("solicitudes:confirmacion", args=[solicitud.pk])
        )

    def test_se_guarda_la_ip_de_origen(self):
        self.client.post(reverse("solicitudes:crear"), DATOS_VALIDOS)
        self.assertIsNotNone(SolicitudAyuda.objects.first().ip_origen)

    def test_el_listado_oculta_los_bloqueados(self):
        SolicitudAyuda.objects.create(**dict(DATOS_VALIDOS, estado=Estado.BLOQUEADA))
        respuesta = self.client.get(reverse("solicitudes:lista"))
        self.assertEqual(len(respuesta.context["pagina"].object_list), 0)

    def test_el_detalle_de_un_bloqueado_devuelve_404(self):
        solicitud = SolicitudAyuda.objects.create(
            **dict(DATOS_VALIDOS, estado=Estado.BLOQUEADA)
        )
        respuesta = self.client.get(reverse("solicitudes:detalle", args=[solicitud.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_el_listado_filtra_por_urgencia(self):
        SolicitudAyuda.objects.create(**dict(DATOS_VALIDOS, urgencia="ALTA"))
        SolicitudAyuda.objects.create(**dict(DATOS_VALIDOS, urgencia="BAJA"))
        respuesta = self.client.get(reverse("solicitudes:lista"), {"urgencia": "ALTA"})
        self.assertEqual(len(respuesta.context["pagina"].object_list), 1)

    def test_un_intento_de_xss_se_rechaza_al_publicar(self):
        """
        Un texto con <script> ni siquiera llega a guardarse.

        Antes se guardaba y se mostraba escapado; ahora la validacion lo
        rechaza de entrada, que es mejor: el contenido malicioso nunca entra
        a la base de datos.
        """
        datos = dict(
            DATOS_VALIDOS,
            descripcion="<script>alert('xss')</script> Necesitamos mercado urgente.",
        )
        respuesta = self.client.post(reverse("solicitudes:crear"), datos)

        self.assertEqual(SolicitudAyuda.objects.count(), 0)
        self.assertContains(respuesta, "no esta permitido")

    def test_el_texto_normal_se_escapa_al_mostrarse(self):
        """Los simbolos legitimos se guardan y salen escapados en el HTML."""
        datos = dict(
            DATOS_VALIDOS,
            descripcion="Somos 5 personas & necesitamos mercado <urgente> ya.",
        )
        self.client.post(reverse("solicitudes:crear"), datos)
        solicitud = SolicitudAyuda.objects.first()

        respuesta = self.client.get(reverse("solicitudes:detalle", args=[solicitud.pk]))
        contenido = respuesta.content.decode()

        self.assertIn("&lt;urgente&gt;", contenido)
        self.assertIn("&amp;", contenido)
