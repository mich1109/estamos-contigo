"""
Tests de las protecciones de seguridad.

Cubren las capas que se agregaron sobre lo que Django ya trae: cabeceras,
honeypot, limite por IP, sanitizado de texto y validacion de imagenes.
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from reportes.models import ReporteComunitario
from solicitudes.models import SolicitudAyuda

DATOS_REPORTE = {
    "tipo_reporte": "DANOS",
    "ciudad": "Armenia",
    "zona": "Barrio Centro",
    "urgencia": "ALTA",
    "descripcion": "Varias casas de la cuadra tienen grietas visibles.",
}


def imagen(nombre="foto.jpg", formato="JPEG", tamano=(400, 300)):
    b = io.BytesIO()
    Image.new("RGB", tamano, (200, 60, 60)).save(b, format=formato)
    b.seek(0)
    return SimpleUploadedFile(nombre, b.read(), content_type="image/jpeg")


class CabecerasSeguridadTests(TestCase):
    """Las cabeceras deben llegar en todas las respuestas."""

    def test_content_security_policy(self):
        respuesta = self.client.get(reverse("core:inicio"))
        csp = respuesta.headers.get("Content-Security-Policy", "")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)

    def test_la_csp_permite_lo_que_el_mapa_necesita(self):
        """Si la CSP bloquea OpenStreetMap, el mapa se ve en blanco."""
        respuesta = self.client.get(reverse("mapa:mapa"))
        csp = respuesta.headers["Content-Security-Policy"]
        self.assertIn("tile.openstreetmap.org", csp)
        self.assertIn("unpkg.com", csp)

    def test_cabeceras_contra_ataques_comunes(self):
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(respuesta.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(respuesta.headers["X-Frame-Options"], "DENY")
        self.assertIn("Referrer-Policy", respuesta.headers)
        self.assertIn("Permissions-Policy", respuesta.headers)


class HoneypotTests(TestCase):
    """El campo trampa detiene bots sin molestar a las personas."""

    def test_un_bot_que_rellena_la_trampa_no_publica(self):
        datos = dict(DATOS_REPORTE, website="https://spam.example.com")
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_una_persona_que_deja_la_trampa_vacia_si_publica(self):
        self.client.post(reverse("reportes:crear"), DATOS_REPORTE)
        self.assertEqual(ReporteComunitario.objects.count(), 1)

    def test_la_trampa_esta_oculta_en_el_formulario(self):
        respuesta = self.client.get(reverse("reportes:crear"))
        self.assertContains(respuesta, "campo-trampa")
        self.assertContains(respuesta, 'name="website"')


class TextoPeligrosoTests(TestCase):
    """El texto del publico se limpia antes de guardarse."""

    def test_rechaza_una_etiqueta_script(self):
        datos = dict(
            DATOS_REPORTE,
            descripcion="<script>alert('hackeado')</script> hay danos en la via.",
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_rechaza_un_manejador_de_eventos(self):
        datos = dict(
            DATOS_REPORTE,
            descripcion="Casa con danos <img src=x onerror=alert(1)> en el muro.",
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_rechaza_una_url_javascript(self):
        datos = dict(
            DATOS_REPORTE,
            descripcion="Mira aqui javascript:robarDatos() para mas informacion.",
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_rechaza_un_texto_gigantesco(self):
        datos = dict(DATOS_REPORTE, descripcion="a" * 5000)
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_un_texto_normal_con_simbolos_si_pasa(self):
        """No se puede ser tan estricto que se rechace lenguaje legitimo."""
        datos = dict(
            DATOS_REPORTE,
            descripcion="La via <calle 20> esta bloqueada; somos 5 personas & 2 ninos.",
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 1)

    def test_el_texto_guardado_sale_escapado_en_la_pagina(self):
        datos = dict(
            DATOS_REPORTE,
            descripcion="La via <calle 20> esta bloqueada por escombros grandes.",
        )
        self.client.post(reverse("reportes:crear"), datos)
        reporte = ReporteComunitario.objects.first()

        respuesta = self.client.get(reporte.get_absolute_url())
        self.assertContains(respuesta, "&lt;calle 20&gt;")


class ImagenesMaliciosasTests(TestCase):
    """Solo se aceptan imagenes reales y de tamano razonable."""

    def test_rechaza_un_ejecutable_disfrazado(self):
        datos = dict(
            DATOS_REPORTE,
            foto=SimpleUploadedFile(
                "virus.jpg", b"MZ\x90\x00\x03 ejecutable de windows",
                content_type="image/jpeg",
            ),
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_rechaza_un_svg_con_script(self):
        """Los SVG pueden contener JavaScript: no estan permitidos."""
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        datos = dict(
            DATOS_REPORTE,
            foto=SimpleUploadedFile("dibujo.svg", svg, content_type="image/svg+xml"),
        )
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_rechaza_una_imagen_de_dimensiones_absurdas(self):
        """Una imagen enorme consume toda la memoria del servidor al abrirla."""
        with override_settings(MAX_IMAGE_DIMENSION=500):
            datos = dict(DATOS_REPORTE, foto=imagen(tamano=(2000, 2000)))
            self.client.post(reverse("reportes:crear"), datos)
            self.assertEqual(ReporteComunitario.objects.count(), 0)

    def test_una_foto_normal_de_celular_si_pasa(self):
        datos = dict(DATOS_REPORTE, foto=imagen(tamano=(1200, 900)))
        self.client.post(reverse("reportes:crear"), datos)
        self.assertEqual(ReporteComunitario.objects.count(), 1)


@override_settings(MAX_PUBLICACIONES_POR_HORA=3)
class LimitePorIPTests(TestCase):
    """Una sola IP no puede inundar el sitio."""

    def test_se_bloquea_al_superar_el_limite(self):
        for i in range(3):
            self.client.post(
                reverse("reportes:crear"),
                dict(DATOS_REPORTE, zona=f"Barrio {i}"),
            )
        self.assertEqual(ReporteComunitario.objects.count(), 3)

        respuesta = self.client.post(
            reverse("reportes:crear"), dict(DATOS_REPORTE, zona="Uno de mas")
        )

        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(ReporteComunitario.objects.count(), 3)

    def test_la_pagina_de_limite_recuerda_llamar_al_123(self):
        for i in range(4):
            respuesta = self.client.post(
                reverse("reportes:crear"), dict(DATOS_REPORTE, zona=f"Barrio {i}")
            )
        self.assertContains(respuesta, "123", status_code=429)

    def test_leer_el_sitio_nunca_se_bloquea(self):
        """El limite es solo para publicar: consultar debe ser siempre libre."""
        for _ in range(30):
            respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(respuesta.status_code, 200)


class ProteccionCSRFTests(TestCase):
    """Sin token CSRF no se puede publicar."""

    def test_un_envio_sin_token_es_rechazado(self):
        cliente = self.client_class(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("reportes:crear"), DATOS_REPORTE)

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(ReporteComunitario.objects.count(), 0)


class InyeccionSQLTests(TestCase):
    """El ORM parametriza las consultas: la inyeccion no es posible."""

    def test_una_busqueda_maliciosa_no_borra_datos(self):
        SolicitudAyuda.objects.create(
            alias="Familia Perez",
            ciudad="Armenia",
            zona="Centro",
            tipo_ayuda="ALIMENTOS",
            urgencia="ALTA",
            descripcion="Necesitamos mercado para tres dias.",
            personas_afectadas=4,
            contacto_telefono="3001234567",
        )

        ataque = "'; DROP TABLE solicitudes_solicitudayuda; --"
        respuesta = self.client.get(reverse("core:inicio"), {"q": ataque})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(SolicitudAyuda.objects.count(), 1)

    def test_ataque_en_el_filtro_de_ciudad(self):
        ataque = "Armenia' OR '1'='1"
        respuesta = self.client.get(reverse("solicitudes:lista"), {"ciudad": ataque})
        self.assertEqual(respuesta.status_code, 200)


class AccesoAdministrativoTests(TestCase):
    """Las rutas privadas rechazan a cualquiera sin sesion de administrador."""

    def test_el_panel_rechaza_anonimos(self):
        for ruta in ["/panel/", "/panel/moderacion/"]:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)
                self.assertNotEqual(respuesta.status_code, 200)

    def test_el_admin_rechaza_anonimos(self):
        respuesta = self.client.get("/admin/")
        self.assertNotEqual(respuesta.status_code, 200)
