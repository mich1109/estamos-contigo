"""Tests del directorio de puntos de ayuda."""
from django.test import TestCase
from django.urls import reverse

from core.choices import Estado
from puntos.models import EstadoVerificacion, PuntoAyuda

BASE = {
    "zona": "Centro",
    "horario": "8am a 6pm",
    "descripcion": "Punto de ayuda habilitado durante la emergencia.",
    "fuente_informacion": "Alcaldia",
}


def crear(nombre, ciudad="Manizales", tipo="ACOPIO", **extra):
    datos = dict(BASE, nombre=nombre, ciudad=ciudad, tipo=tipo)
    datos.update(extra)
    return PuntoAyuda.objects.create(**datos)


class DepartamentoTests(TestCase):
    """El municipio se agrupa con su departamento."""

    def test_el_departamento_se_deduce_del_municipio(self):
        punto = crear("Coliseo", ciudad="Manizales")
        self.assertEqual(punto.departamento, "Caldas")
        self.assertEqual(punto.lugar, "Manizales — Caldas")

    def test_funciona_sin_tildes(self):
        self.assertEqual(crear("A", ciudad="Quibdo").departamento, "Chocó")
        self.assertEqual(crear("B", ciudad="Bogota").departamento, "Cundinamarca")

    def test_respeta_el_departamento_escrito_a_mano(self):
        """Si la administracion lo escribe, no se sobreescribe."""
        punto = crear("C", ciudad="Manizales", departamento="Otro")
        self.assertEqual(punto.departamento, "Otro")

    def test_un_municipio_desconocido_no_rompe_nada(self):
        punto = crear("D", ciudad="Pueblo Nuevo Inventado")
        self.assertEqual(punto.departamento, "")
        self.assertEqual(punto.lugar, "Pueblo Nuevo Inventado")


class AgrupacionTests(TestCase):
    def test_el_listado_agrupa_por_municipio(self):
        crear("Uno", ciudad="Manizales")
        crear("Dos", ciudad="Manizales")
        crear("Tres", ciudad="Pereira")

        respuesta = self.client.get(reverse("puntos:lista"))
        grupos = {g["ciudad"]: g for g in respuesta.context["grupos"]}

        self.assertEqual(grupos["Manizales"]["total"], 2)
        self.assertEqual(grupos["Pereira"]["total"], 1)
        self.assertEqual(grupos["Manizales"]["lugar"], "Manizales — Caldas")

    def test_al_elegir_una_ciudad_no_se_agrupa(self):
        crear("Uno", ciudad="Manizales")
        crear("Dos", ciudad="Pereira")

        respuesta = self.client.get(reverse("puntos:lista"), {"ciudad": "Manizales"})

        self.assertEqual(respuesta.context["grupos"], [])
        self.assertEqual(len(respuesta.context["pagina"].object_list), 1)


class FiltrosTests(TestCase):
    def setUp(self):
        crear("Albergue", tipo="REFUGIO")
        crear("Acopio", tipo="ACOPIO", elementos_recibidos="Cobijas\nPanales")
        crear("Sangre", tipo="SANGRE", ciudad="Cali")

    def test_filtra_por_necesidad(self):
        r = self.client.get(reverse("puntos:lista"), {"necesidad": "alojamiento"})
        self.assertEqual(r.context["total"], 1)

    def test_filtra_por_tipo(self):
        r = self.client.get(reverse("puntos:lista"), {"tipo": "SANGRE"})
        self.assertEqual(r.context["total"], 1)

    def test_filtra_por_estado_de_verificacion(self):
        PuntoAyuda.objects.filter(nombre="Albergue").update(
            verificacion=EstadoVerificacion.CONFIRMADO
        )
        r = self.client.get(reverse("puntos:lista"), {"estado": "CONFIRMADO"})
        self.assertEqual(r.context["total"], 1)

    def test_busca_en_los_elementos_que_recibe(self):
        """Buscar 'panales' debe encontrar el acopio que los recoge."""
        r = self.client.get(reverse("puntos:lista"), {"q": "panales"})
        self.assertEqual(r.context["total"], 1)

    def test_una_necesidad_inventada_no_rompe(self):
        r = self.client.get(reverse("puntos:lista"), {"necesidad": "xyz"})
        self.assertEqual(r.status_code, 200)


class VerificacionTests(TestCase):
    """Lo que reporta el publico nunca entra como confirmado."""

    def test_un_reporte_publico_queda_por_confirmar(self):
        datos = {
            "nombre": "Salon comunal del barrio",
            "tipo": "ACOPIO",
            "ciudad": "Manizales",
            "zona": "Centro",
            "horario": "Todos los dias de 8am a 6pm",
            "descripcion": "Se reciben mercados y ropa para los damnificados.",
            "fuente_informacion": "Lo vi personalmente esta manana",
            "disponibilidad": "ACTIVO",
        }
        self.client.post(reverse("puntos:crear"), datos)

        punto = PuntoAyuda.objects.get(nombre="Salon comunal del barrio")
        self.assertEqual(punto.verificacion, EstadoVerificacion.POR_CONFIRMAR)
        self.assertFalse(punto.verificado)

    def test_el_publico_no_puede_autoconfirmar(self):
        """Aunque envie el campo en el POST, se ignora."""
        datos = {
            "nombre": "Punto falso",
            "tipo": "ACOPIO",
            "ciudad": "Cali",
            "zona": "Centro",
            "horario": "Todo el dia",
            "descripcion": "Descripcion suficientemente larga para pasar.",
            "fuente_informacion": "Yo mismo lo digo",
            "disponibilidad": "ACTIVO",
            "verificacion": "CONFIRMADO",
            "verificado": "true",
            "destacado": "true",
        }
        self.client.post(reverse("puntos:crear"), datos)

        punto = PuntoAyuda.objects.get(nombre="Punto falso")
        self.assertEqual(punto.verificacion, EstadoVerificacion.POR_CONFIRMAR)
        self.assertFalse(punto.verificado)
        self.assertFalse(punto.destacado)

    def test_el_detalle_avisa_cuando_falta_confirmar(self):
        punto = crear("Sin confirmar")
        respuesta = self.client.get(punto.get_absolute_url())
        self.assertContains(respuesta, "pendiente de confirmación oficial")


class ElementosTests(TestCase):
    def test_las_listas_se_parten_por_linea(self):
        punto = crear(
            "Acopio",
            elementos_recibidos="Cobijas\nToallas\n\n  Panales  ",
            elementos_no_recibidos="Medicamentos",
        )
        self.assertEqual(punto.lista_recibidos, ["Cobijas", "Toallas", "Panales"])
        self.assertEqual(punto.lista_no_recibidos, ["Medicamentos"])

    def test_sin_elementos_devuelve_lista_vacia(self):
        self.assertEqual(crear("Vacio").lista_recibidos, [])

    def test_la_tarjeta_muestra_lo_que_no_reciben(self):
        crear("Acopio", elementos_no_recibidos="Medicamentos\nRopa interior")
        respuesta = self.client.get(reverse("puntos:lista"))
        self.assertContains(respuesta, "NO recibe")
        self.assertContains(respuesta, "Medicamentos")


class ComoLlegarTests(TestCase):
    def test_usa_coordenadas_cuando_existen(self):
        punto = crear("Con mapa", latitud="5.0689", longitud="-75.5174")
        self.assertIn("5.0689,-75.5174", punto.url_como_llegar)

    def test_usa_la_direccion_cuando_no_hay_coordenadas(self):
        punto = crear("Sin mapa", direccion="Calle 20 # 15-30")
        self.assertIn("Calle", punto.url_como_llegar)
        self.assertIn("Manizales", punto.url_como_llegar)


class NoRomperTests(TestCase):
    """Las funcionalidades que ya existian siguen operando."""

    def test_los_bloqueados_siguen_ocultos(self):
        crear("Bloqueado", estado=Estado.BLOQUEADA)
        respuesta = self.client.get(reverse("puntos:lista"))
        self.assertEqual(respuesta.context["total"], 0)

    def test_el_formulario_publico_sigue_abierto_sin_cuenta(self):
        self.assertEqual(self.client.get(reverse("puntos:crear")).status_code, 200)

    def test_el_punto_sigue_apareciendo_en_el_mapa(self):
        crear("En el mapa", latitud="5.0689", longitud="-75.5174")
        datos = self.client.get(
            reverse("mapa:marcadores"), {"categorias": "punto"}
        ).json()
        self.assertEqual(datos["total"], 1)
        self.assertEqual(datos["marcadores"][0]["icono"], "📦")
