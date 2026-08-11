"""
Tests de subida de imagenes.

Comprueban el camino completo: el navegador envia el archivo, el formulario lo
valida, el modelo lo guarda en disco y la plantilla lo muestra.
"""
import io
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from ayudas.models import OfertaAyuda
from puntos.models import PuntoAyuda
from reportes.models import ReporteComunitario
from solicitudes.models import SolicitudAyuda

# Las pruebas escriben archivos reales: los mandamos a una carpeta temporal
# para no ensuciar media/ del proyecto.
MEDIA_TEMPORAL = tempfile.mkdtemp()


def imagen_de_prueba(nombre="foto.jpg", formato="JPEG", tamano=(400, 300)):
    """Genera una imagen valida en memoria, como la que subiria un celular."""
    buffer = io.BytesIO()
    Image.new("RGB", tamano, color=(200, 60, 60)).save(buffer, format=formato)
    buffer.seek(0)
    tipo = "image/jpeg" if formato == "JPEG" else f"image/{formato.lower()}"
    return SimpleUploadedFile(nombre, buffer.read(), content_type=tipo)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class SubidaDeImagenesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)
        super().tearDownClass()

    def test_reporte_con_foto(self):
        """Lo que pidio la usuaria: fotos en los reportes."""
        datos = {
            "tipo_reporte": "DANOS",
            "ciudad": "Armenia",
            "zona": "Barrio Centro",
            "urgencia": "ALTA",
            "descripcion": "Varias casas de la cuadra tienen grietas visibles.",
            "reportado_por": "Vecino del sector",
            "foto": imagen_de_prueba("danos.jpg"),
        }
        respuesta = self.client.post(reverse("reportes:crear"), datos)

        reporte = ReporteComunitario.objects.first()
        self.assertIsNotNone(reporte)
        self.assertTrue(reporte.foto, "La foto no se guardo")
        self.assertIn("reportes/", reporte.foto.name)

        # La foto se muestra en el detalle
        detalle = self.client.get(reverse("reportes:detalle", args=[reporte.pk]))
        self.assertContains(detalle, reporte.foto.url)

        # Y tambien en el listado
        listado = self.client.get(reverse("reportes:lista"))
        self.assertContains(listado, reporte.foto.url)

    def test_solicitud_con_foto(self):
        datos = {
            "alias": "Familia Perez",
            "ciudad": "Armenia",
            "zona": "La Milagrosa",
            "personas_afectadas": 5,
            "tipo_ayuda": "ALIMENTOS",
            "urgencia": "ALTA",
            "descripcion": "Necesitamos mercado para tres dias.",
            "contacto_telefono": "3001234567",
            "foto": imagen_de_prueba("necesidad.jpg"),
        }
        self.client.post(reverse("solicitudes:crear"), datos)

        solicitud = SolicitudAyuda.objects.first()
        self.assertTrue(solicitud.foto)
        self.assertIn("solicitudes/", solicitud.foto.name)

    def test_oferta_con_foto(self):
        datos = {
            "alias": "Panaderia El Trigal",
            "ciudad": "Armenia",
            "zona": "Centro",
            "tipo_ayuda": "ALIMENTOS",
            "cantidad": "5 mercados",
            "descripcion": "Tengo cinco mercados completos para entregar.",
            "disponibilidad": "INMEDIATA",
            "contacto_telefono": "3009876543",
            "foto": imagen_de_prueba("mercados.jpg"),
        }
        self.client.post(reverse("ayudas:crear"), datos)

        oferta = OfertaAyuda.objects.first()
        self.assertTrue(oferta.foto)
        self.assertIn("ayudas/", oferta.foto.name)

    def test_punto_con_foto(self):
        datos = {
            "nombre": "Salon comunal La Milagrosa",
            "tipo": "ACOPIO",
            "ciudad": "Armenia",
            "zona": "La Milagrosa",
            "horario": "Todos los dias de 7am a 7pm",
            "descripcion": "Centro de acopio comunitario de mercados y ropa.",
            "fuente_informacion": "Lo vi personalmente esta manana",
            "disponibilidad": "ACTIVO",
            "foto": imagen_de_prueba("salon.jpg"),
        }
        self.client.post(reverse("puntos:crear"), datos)

        punto = PuntoAyuda.objects.first()
        self.assertTrue(punto.foto)
        self.assertIn("puntos/", punto.foto.name)

    def test_la_foto_es_opcional(self):
        """Nadie debe quedarse sin publicar por no tener foto."""
        datos = {
            "tipo_reporte": "VIA_BLOQUEADA",
            "ciudad": "Pereira",
            "zona": "Barrio Cuba",
            "urgencia": "ALTA",
            "descripcion": "La via esta bloqueada por escombros desde ayer.",
        }
        self.client.post(reverse("reportes:crear"), datos)

        reporte = ReporteComunitario.objects.first()
        self.assertIsNotNone(reporte)
        self.assertFalse(reporte.foto)

    def test_se_rechaza_una_imagen_demasiado_pesada(self):
        """
        El limite es 5 MB.

        La imagen tiene que ser valida de verdad: si se envian bytes basura
        Django la rechaza antes por corrupta, y no se estaria probando el
        limite de tamano sino la validacion de formato.
        """
        buffer = io.BytesIO()
        # Ruido aleatorio para que el JPEG no se comprima y supere los 5 MB.
        import random

        grande = Image.frombytes(
            "RGB",
            (2600, 2600),
            bytes(random.getrandbits(8) for _ in range(2600 * 2600 * 3)),
        )
        grande.save(buffer, format="JPEG", quality=100)
        buffer.seek(0)
        contenido = buffer.read()
        self.assertGreater(
            len(contenido), 5 * 1024 * 1024,
            "La imagen de prueba no supera los 5 MB; el test no probaria nada.",
        )

        datos = {
            "tipo_reporte": "DANOS",
            "ciudad": "Armenia",
            "zona": "Centro",
            "urgencia": "ALTA",
            "descripcion": "Descripcion suficientemente larga para pasar.",
            "foto": SimpleUploadedFile("enorme.jpg", contenido, content_type="image/jpeg"),
        }
        respuesta = self.client.post(reverse("reportes:crear"), datos)

        self.assertEqual(ReporteComunitario.objects.count(), 0)
        self.assertContains(respuesta, "pesa demasiado")

    def test_se_rechaza_un_archivo_corrupto_o_disfrazado(self):
        """Un .exe renombrado a .jpg no debe pasar."""
        datos = {
            "tipo_reporte": "DANOS",
            "ciudad": "Armenia",
            "zona": "Centro",
            "urgencia": "ALTA",
            "descripcion": "Descripcion suficientemente larga para pasar.",
            "foto": SimpleUploadedFile(
                "disfrazado.jpg", b"MZ\x90\x00 esto no es una imagen",
                content_type="image/jpeg",
            ),
        }
        respuesta = self.client.post(reverse("reportes:crear"), datos)

        self.assertEqual(ReporteComunitario.objects.count(), 0)
        self.assertContains(respuesta, "imagen")

    def test_png_tambien_se_acepta(self):
        datos = {
            "tipo_reporte": "DANOS",
            "ciudad": "Armenia",
            "zona": "Centro",
            "urgencia": "MEDIA",
            "descripcion": "Descripcion suficientemente larga para pasar.",
            "foto": imagen_de_prueba("captura.png", formato="PNG"),
        }
        self.client.post(reverse("reportes:crear"), datos)
        self.assertTrue(ReporteComunitario.objects.first().foto)

    def test_la_foto_aparece_en_el_mapa(self):
        datos = {
            "tipo_reporte": "DANOS",
            "ciudad": "Armenia",
            "zona": "Centro",
            "urgencia": "ALTA",
            "descripcion": "Descripcion suficientemente larga para pasar.",
            "latitud": "4.535000",
            "longitud": "-75.681000",
            "foto": imagen_de_prueba("mapa.jpg"),
        }
        self.client.post(reverse("reportes:crear"), datos)

        respuesta = self.client.get(reverse("mapa:marcadores"), {"categorias": "reporte"})
        marcador = respuesta.json()["marcadores"][0]
        self.assertTrue(marcador["foto"], "El marcador no incluye la foto")
