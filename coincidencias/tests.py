"""Tests del motor de coincidencias."""
from django.test import TestCase

from ayudas.models import OfertaAyuda
from coincidencias import services
from coincidencias.models import Coincidencia
from core.choices import Estado
from solicitudes.models import SolicitudAyuda


def crear_solicitud(**extra):
    datos = {
        "alias": "Familia Perez",
        "ciudad": "Armenia",
        "zona": "La Milagrosa",
        "tipo_ayuda": "ALIMENTOS",
        "urgencia": "ALTA",
        "descripcion": "Somos cinco personas y necesitamos mercado.",
        "personas_afectadas": 5,
        "contacto_telefono": "3001234567",
    }
    datos.update(extra)
    return SolicitudAyuda.objects.create(**datos)


def crear_oferta(**extra):
    datos = {
        "alias": "Panaderia El Trigal",
        "ciudad": "Armenia",
        "zona": "Centro",
        "tipo_ayuda": "ALIMENTOS",
        "cantidad": "5 mercados",
        "descripcion": "Tengo cinco mercados completos para entregar.",
        "disponibilidad": "INMEDIATA",
        "contacto_telefono": "3009876543",
    }
    datos.update(extra)
    return OfertaAyuda.objects.create(**datos)


class CalculoDeScoreTests(TestCase):
    """Comprueba la regla de emparejamiento en aislamiento."""

    def test_misma_ciudad_y_mismo_tipo_da_70(self):
        solicitud = crear_solicitud(zona="La Milagrosa")
        oferta = crear_oferta(zona="Centro")
        self.assertEqual(services.calcular_score(solicitud, oferta), 70)

    def test_misma_ciudad_y_misma_zona_da_100(self):
        solicitud = crear_solicitud(zona="Centro")
        oferta = crear_oferta(zona="Centro")
        self.assertEqual(services.calcular_score(solicitud, oferta), 100)

    def test_distinto_tipo_no_coincide(self):
        solicitud = crear_solicitud(tipo_ayuda="ALIMENTOS")
        oferta = crear_oferta(tipo_ayuda="AGUA")
        self.assertEqual(services.calcular_score(solicitud, oferta), 0)

    def test_distinta_ciudad_no_coincide(self):
        solicitud = crear_solicitud(ciudad="Armenia")
        oferta = crear_oferta(ciudad="Pereira")
        self.assertEqual(services.calcular_score(solicitud, oferta), 0)

    def test_la_ciudad_se_compara_sin_tildes_ni_mayusculas(self):
        """'Medellín', 'MEDELLIN' y 'medellin ' deben tratarse como la misma."""
        solicitud = crear_solicitud(ciudad="Medellín", zona="Laureles")
        oferta = crear_oferta(ciudad="MEDELLIN ", zona="laureles")
        self.assertEqual(services.calcular_score(solicitud, oferta), 100)

    def test_ciudad_vacia_no_coincide(self):
        """Sin ciudad no hay forma de emparejar con sentido geografico."""
        solicitud = crear_solicitud(ciudad="")
        oferta = crear_oferta(ciudad="")
        self.assertEqual(services.calcular_score(solicitud, oferta), 0)


class CreacionAutomaticaTests(TestCase):
    """Comprueba que las senales crean las coincidencias al publicar."""

    def test_publicar_oferta_despues_crea_la_coincidencia(self):
        crear_solicitud()
        self.assertEqual(Coincidencia.objects.count(), 0)

        crear_oferta()
        self.assertEqual(Coincidencia.objects.count(), 1)

    def test_publicar_solicitud_despues_crea_la_coincidencia(self):
        crear_oferta()
        self.assertEqual(Coincidencia.objects.count(), 0)

        crear_solicitud()
        self.assertEqual(Coincidencia.objects.count(), 1)

    def test_no_se_duplican_al_volver_a_guardar(self):
        solicitud = crear_solicitud()
        crear_oferta()
        self.assertEqual(Coincidencia.objects.count(), 1)

        solicitud.descripcion = "Descripcion actualizada de la necesidad."
        solicitud.save()

        self.assertEqual(Coincidencia.objects.count(), 1)

    def test_una_oferta_cubre_varias_necesidades(self):
        crear_solicitud(alias="Familia A")
        crear_solicitud(alias="Familia B")
        crear_oferta()
        self.assertEqual(Coincidencia.objects.count(), 2)

    def test_registro_resuelto_no_genera_coincidencias(self):
        crear_solicitud()
        crear_oferta(estado=Estado.RESUELTA)
        self.assertEqual(Coincidencia.objects.count(), 0)

    def test_registro_bloqueado_no_genera_coincidencias(self):
        crear_solicitud()
        crear_oferta(estado=Estado.BLOQUEADA)
        self.assertEqual(Coincidencia.objects.count(), 0)


class RecalculoTests(TestCase):
    """Comprueba el comando de recalculo completo."""

    def test_recalcular_reconstruye_todas_las_coincidencias(self):
        crear_solicitud()
        crear_oferta()
        Coincidencia.objects.all().delete()
        self.assertEqual(Coincidencia.objects.count(), 0)

        total = services.recalcular_todo()

        self.assertEqual(total, 1)
        self.assertEqual(Coincidencia.objects.count(), 1)
