"""Tests del endpoint de marcadores del mapa."""
import json

from django.test import TestCase
from django.urls import reverse

from ayudas.models import OfertaAyuda
from core.choices import Estado
from solicitudes.models import SolicitudAyuda


class EndpointMarcadoresTests(TestCase):
    def setUp(self):
        self.solicitud = SolicitudAyuda.objects.create(
            alias="Familia Perez",
            ciudad="Armenia",
            zona="La Milagrosa",
            tipo_ayuda="ALIMENTOS",
            urgencia="ALTA",
            descripcion="Necesitamos mercado para tres dias.",
            personas_afectadas=5,
            contacto_telefono="3001234567",
            latitud="4.535000",
            longitud="-75.681000",
        )
        self.oferta = OfertaAyuda.objects.create(
            alias="Panaderia El Trigal",
            ciudad="Armenia",
            zona="Centro",
            tipo_ayuda="ALIMENTOS",
            cantidad="5 mercados",
            descripcion="Tengo cinco mercados completos para entregar.",
            disponibilidad="INMEDIATA",
            contacto_telefono="3009876543",
            latitud="4.539000",
            longitud="-75.670000",
        )

    def datos(self, **parametros):
        respuesta = self.client.get(reverse("mapa:marcadores"), parametros)
        self.assertEqual(respuesta.status_code, 200)
        return json.loads(respuesta.content)

    def test_devuelve_todos_los_marcadores_por_defecto(self):
        datos = self.datos()
        self.assertEqual(datos["total"], 2)

    def test_filtra_por_categoria(self):
        datos = self.datos(categorias="solicitud")
        self.assertEqual(datos["total"], 1)
        self.assertEqual(datos["marcadores"][0]["categoria"], "solicitud")

    def test_filtra_por_ciudad(self):
        self.assertEqual(self.datos(ciudad="Armenia")["total"], 2)
        self.assertEqual(self.datos(ciudad="Pereira")["total"], 0)

    def test_filtra_por_urgencia(self):
        self.assertEqual(self.datos(categorias="solicitud", urgencia="ALTA")["total"], 1)
        self.assertEqual(self.datos(categorias="solicitud", urgencia="BAJA")["total"], 0)

    def test_los_registros_sin_coordenadas_no_aparecen(self):
        SolicitudAyuda.objects.create(
            alias="Sin ubicacion",
            ciudad="Armenia",
            zona="Centro",
            tipo_ayuda="AGUA",
            urgencia="MEDIA",
            descripcion="No marque la ubicacion en el mapa.",
            personas_afectadas=2,
            contacto_telefono="3001112222",
        )
        self.assertEqual(self.datos(categorias="solicitud")["total"], 1)

    def test_los_bloqueados_nunca_se_serializan(self):
        self.solicitud.estado = Estado.BLOQUEADA
        self.solicitud.save()
        datos = self.datos(categorias="solicitud")
        self.assertEqual(datos["total"], 0)

    def test_no_expone_datos_internos(self):
        """La IP de origen y las notas del admin no deben salir al publico."""
        datos = self.datos()
        for marcador in datos["marcadores"]:
            self.assertNotIn("ip_origen", marcador)
            self.assertNotIn("nota_admin", marcador)

    def test_incluye_el_contacto_publico(self):
        """El contacto se muestra a proposito, junto al aviso de verificacion."""
        datos = self.datos(categorias="solicitud")
        self.assertEqual(datos["marcadores"][0]["telefono"], "3001234567")


class ZonasAfectadasTests(TestCase):
    """
    Los accesos rapidos por zona deben reconocer como escribe la gente.

    Alguien de Quibdo escribe "Quibdo", no "Choco": si la zona solo buscara su
    propio nombre, marcaria cero aunque tenga publicaciones.
    """

    def crear_en(self, ciudad):
        return SolicitudAyuda.objects.create(
            alias="Vecino",
            ciudad=ciudad,
            zona="Centro",
            tipo_ayuda="AGUA",
            urgencia="ALTA",
            descripcion="No tenemos agua potable desde hace dos dias.",
            personas_afectadas=3,
            contacto_telefono="3001234567",
            latitud="5.694700",
            longitud="-76.661100",
        )

    def test_la_pagina_del_mapa_lista_las_cinco_zonas(self):
        respuesta = self.client.get(reverse("mapa:mapa"))
        nombres = [z["nombre"] for z in respuesta.context["zonas"]]
        self.assertEqual(nombres, ["Chocó", "Cali", "Pereira", "Manizales", "Armenia"])

    def test_quibdo_cuenta_como_choco(self):
        self.crear_en("Quibdó")
        respuesta = self.client.get(reverse("mapa:mapa"))
        choco = next(z for z in respuesta.context["zonas"] if z["nombre"] == "Chocó")
        self.assertEqual(choco["publicaciones"], 1)

    def test_dosquebradas_cuenta_como_pereira(self):
        self.crear_en("Dosquebradas")
        respuesta = self.client.get(reverse("mapa:mapa"))
        pereira = next(z for z in respuesta.context["zonas"] if z["nombre"] == "Pereira")
        self.assertEqual(pereira["publicaciones"], 1)

    def test_filtrar_por_zona_incluye_sus_municipios(self):
        self.crear_en("Quibdó")
        self.crear_en("Armenia")

        respuesta = self.client.get(reverse("mapa:marcadores"), {"zona": "Chocó"})
        datos = respuesta.json()

        self.assertEqual(datos["total"], 1)
        self.assertEqual(datos["marcadores"][0]["ciudad"], "Quibdó")

    def test_una_zona_inventada_no_rompe_el_mapa(self):
        self.crear_en("Armenia")
        respuesta = self.client.get(reverse("mapa:marcadores"), {"zona": "Atlantida"})
        self.assertEqual(respuesta.status_code, 200)
