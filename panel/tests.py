"""
Tests del panel de administracion.

Lo importante aqui es que NADIE sin sesion de administrador pueda cambiar
estados: es la unica accion privilegiada de toda la plataforma.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.choices import Estado
from solicitudes.models import SolicitudAyuda


class AccesoAlPanelTests(TestCase):
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
        )

    def test_visitante_anonimo_no_entra_al_panel(self):
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertNotEqual(respuesta.status_code, 200)

    def test_visitante_anonimo_no_puede_cerrar_un_caso(self):
        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        self.client.post(url, {"estado": Estado.RESUELTA})

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.ACTIVA)

    def test_usuario_normal_no_puede_cerrar_un_caso(self):
        User.objects.create_user("vecino", password="clave-de-prueba-123")
        self.client.login(username="vecino", password="clave-de-prueba-123")

        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        self.client.post(url, {"estado": Estado.RESUELTA})

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.ACTIVA)

    def test_el_administrador_si_puede_cerrar_un_caso(self):
        User.objects.create_superuser("admin", "admin@ejemplo.com", "clave-de-prueba-123")
        self.client.login(username="admin", password="clave-de-prueba-123")

        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        self.client.post(url, {"estado": Estado.RESUELTA})

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.RESUELTA)

    def test_el_administrador_puede_bloquear_contenido(self):
        User.objects.create_superuser("admin", "admin@ejemplo.com", "clave-de-prueba-123")
        self.client.login(username="admin", password="clave-de-prueba-123")

        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        self.client.post(url, {"estado": Estado.BLOQUEADA})

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.BLOQUEADA)

    def test_no_se_acepta_un_estado_inventado(self):
        User.objects.create_superuser("admin", "admin@ejemplo.com", "clave-de-prueba-123")
        self.client.login(username="admin", password="clave-de-prueba-123")

        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        self.client.post(url, {"estado": "INVENTADO"})

        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.ACTIVA)

    def test_cambiar_estado_solo_acepta_post(self):
        """Un GET no debe poder modificar datos."""
        User.objects.create_superuser("admin", "admin@ejemplo.com", "clave-de-prueba-123")
        self.client.login(username="admin", password="clave-de-prueba-123")

        url = reverse("panel:cambiar_estado", args=["solicitud", self.solicitud.pk])
        respuesta = self.client.get(url, {"estado": Estado.RESUELTA})

        self.assertEqual(respuesta.status_code, 405)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, Estado.ACTIVA)

    def test_el_dashboard_carga_para_el_administrador(self):
        User.objects.create_superuser("admin", "admin@ejemplo.com", "clave-de-prueba-123")
        self.client.login(username="admin", password="clave-de-prueba-123")

        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["metricas"]["solicitudes_activas"], 1)
