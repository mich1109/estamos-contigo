"""Tests de las utilidades y filtros compartidos."""
from django.test import TestCase
from django.urls import reverse

from ayudas.models import OfertaAyuda
from core.choices import Estado
from core.templatetags.ayuda_extras import whatsapp
from core.utils import normalizar
from solicitudes.models import SolicitudAyuda


class NormalizarTests(TestCase):
    def test_quita_tildes_y_mayusculas(self):
        self.assertEqual(normalizar("Medellín"), "medellin")
        self.assertEqual(normalizar("BOGOTÁ"), "bogota")

    def test_colapsa_espacios(self):
        self.assertEqual(normalizar("  Santa   Marta  "), "santa marta")

    def test_valores_vacios(self):
        self.assertEqual(normalizar(""), "")
        self.assertEqual(normalizar(None), "")


class WhatsappTests(TestCase):
    """
    El numero lo escribe el publico en formato libre.

    wa.me solo acepta digitos con indicativo de pais, asi que el filtro debe
    tolerar espacios, guiones, parentesis y el prefijo +57.
    """

    def test_celular_con_espacios(self):
        self.assertEqual(whatsapp("300 123 4567"), "573001234567")

    def test_celular_con_guiones(self):
        self.assertEqual(whatsapp("300-123-4567"), "573001234567")

    def test_celular_con_prefijo_pais(self):
        self.assertEqual(whatsapp("+57 300 123 4567"), "573001234567")

    def test_celular_con_parentesis(self):
        self.assertEqual(whatsapp("(300) 1234567"), "573001234567")

    def test_celular_limpio(self):
        self.assertEqual(whatsapp("3001234567"), "573001234567")

    def test_numero_vacio_devuelve_cadena_vacia(self):
        """Sin numero utilizable la plantilla debe poder ocultar el boton."""
        self.assertEqual(whatsapp(""), "")
        self.assertEqual(whatsapp(None), "")

    def test_texto_sin_digitos_devuelve_cadena_vacia(self):
        self.assertEqual(whatsapp("llamar a la casa"), "")

    def test_numero_absurdamente_largo_se_descarta(self):
        self.assertEqual(whatsapp("1" * 30), "")


class TextoParaCompartirTests(TestCase):
    def test_solicitud_incluye_tipo_ciudad_y_aviso(self):
        solicitud = SolicitudAyuda.objects.create(
            alias="Familia Perez",
            ciudad="Armenia",
            zona="La Milagrosa",
            tipo_ayuda="ALIMENTOS",
            urgencia="ALTA",
            descripcion="Necesitamos mercado para tres dias.",
            personas_afectadas=5,
            contacto_telefono="3001234567",
        )
        texto = solicitud.texto_para_compartir
        self.assertIn("Armenia", texto)
        self.assertIn("La Milagrosa", texto)
        self.assertIn("sin verificar", texto)

    def test_oferta_incluye_cantidad(self):
        oferta = OfertaAyuda.objects.create(
            alias="Panaderia El Trigal",
            ciudad="Armenia",
            zona="Centro",
            tipo_ayuda="ALIMENTOS",
            cantidad="5 mercados",
            descripcion="Tengo cinco mercados completos para entregar.",
            disponibilidad="INMEDIATA",
            contacto_telefono="3009876543",
        )
        texto = oferta.texto_para_compartir
        self.assertIn("5 mercados", texto)
        self.assertIn("sin verificar", texto)


class AvisosDeSeguridadTests(TestCase):
    """La advertencia contra estafas debe estar donde se muestran contactos."""

    def setUp(self):
        self.solicitud = SolicitudAyuda.objects.create(
            alias="Familia Perez",
            ciudad="Armenia",
            zona="La Milagrosa",
            tipo_ayuda="ALIMENTOS",
            urgencia="ALTA",
            descripcion="Necesitamos mercado para tres dias.",
            personas_afectadas=5,
            contacto_telefono="300 123 4567",
        )

    def test_el_detalle_advierte_sobre_el_dinero(self):
        respuesta = self.client.get(
            reverse("solicitudes:detalle", args=[self.solicitud.pk])
        )
        self.assertContains(respuesta, "Nunca env")

    def test_el_listado_advierte_sobre_el_dinero(self):
        respuesta = self.client.get(reverse("solicitudes:lista"))
        self.assertContains(respuesta, "Nunca env")

    def test_el_aviso_legal_advierte_sobre_el_dinero(self):
        respuesta = self.client.get(reverse("core:aviso_legal"))
        self.assertContains(respuesta, "Nunca env")

    def test_la_tarjeta_muestra_el_boton_de_whatsapp(self):
        """El numero con espacios debe convertirse en un enlace wa.me valido."""
        respuesta = self.client.get(reverse("solicitudes:lista"))
        self.assertContains(respuesta, "wa.me/573001234567")

    def test_el_detalle_ofrece_compartir(self):
        respuesta = self.client.get(
            reverse("solicitudes:detalle", args=[self.solicitud.pk])
        )
        self.assertContains(respuesta, "Compartir por WhatsApp")

    def test_las_cuatro_secciones_advierten_sobre_el_dinero(self):
        """
        La advertencia anti-estafa no puede faltar en ninguna seccion.

        Se perdio una vez en los reportes por no llevar bloque de contacto;
        este test evita que vuelva a pasar en cualquiera de las cuatro.
        """
        from ayudas.models import OfertaAyuda
        from puntos.models import PuntoAyuda
        from reportes.models import ReporteComunitario

        oferta = OfertaAyuda.objects.create(
            alias="Tienda Don Jose",
            ciudad="Armenia",
            zona="Centro",
            tipo_ayuda="ALIMENTOS",
            cantidad="5 mercados",
            descripcion="Tengo cinco mercados completos para entregar.",
            disponibilidad="INMEDIATA",
            contacto_telefono="3009876543",
        )
        punto = PuntoAyuda.objects.create(
            nombre="Salon comunal",
            ciudad="Armenia",
            zona="Centro",
            tipo="ACOPIO",
            horario="8am a 6pm",
            descripcion="Centro de acopio comunitario del barrio.",
            contacto="300 123 4567",
            fuente_informacion="Lo vi personalmente",
        )
        reporte = ReporteComunitario.objects.create(
            ciudad="Armenia",
            zona="Centro",
            tipo_reporte="VIA_BLOQUEADA",
            urgencia="ALTA",
            descripcion="La via esta bloqueada por escombros desde ayer.",
        )

        paginas = [
            ("necesidad", self.solicitud.get_absolute_url()),
            ("oferta", oferta.get_absolute_url()),
            ("punto", punto.get_absolute_url()),
            ("reporte", reporte.get_absolute_url()),
        ]

        for nombre, url in paginas:
            with self.subTest(seccion=nombre):
                respuesta = self.client.get(url)
                self.assertContains(
                    respuesta,
                    "Nunca env",
                    msg_prefix=f"Falta la advertencia anti-estafa en {nombre}",
                )


DATOS_SOLICITUD = dict(
    alias="Familia Perez",
    ciudad="Armenia",
    zona="La Milagrosa",
    tipo_ayuda="ALIMENTOS",
    urgencia="ALTA",
    descripcion="Necesitamos mercado para tres dias.",
    personas_afectadas=5,
    contacto_telefono="3001234567",
)

DATOS_OFERTA = dict(
    alias="Panaderia El Trigal",
    ciudad="Armenia",
    zona="Centro",
    tipo_ayuda="ALIMENTOS",
    cantidad="5 mercados",
    descripcion="Tengo cinco mercados completos para entregar.",
    disponibilidad="INMEDIATA",
    contacto_telefono="3009876543",
)


class ContadorDeAyudasEntregadasTests(TestCase):
    def test_cuenta_solo_los_casos_cerrados(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.RESUELTA))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.RESUELTA))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.BLOQUEADA))

        respuesta = self.client.get(reverse("core:inicio"))

        self.assertEqual(respuesta.context["ayudas_entregadas"], 2)
        self.assertEqual(respuesta.context["total_solicitudes"], 1)


class PortadaTests(TestCase):
    """
    La portada debe mostrar de entrada lo que la gente publico, sin que
    el visitante tenga que navegar a otra pagina.
    """

    def test_la_portada_abre_sin_publicaciones(self):
        """Recien instalada, la plataforma no debe romperse ni verse rota."""
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Todavía nadie ha pedido ayuda")

    def test_muestra_las_necesidades_publicadas(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        respuesta = self.client.get(reverse("core:inicio"))

        self.assertEqual(len(respuesta.context["solicitudes"]), 1)
        self.assertContains(respuesta, "La Milagrosa")

    def test_muestra_las_ofertas_publicadas(self):
        OfertaAyuda.objects.create(**DATOS_OFERTA)
        respuesta = self.client.get(reverse("core:inicio"))

        self.assertEqual(len(respuesta.context["ofertas"]), 1)
        self.assertContains(respuesta, "5 mercados")

    def test_las_dos_pestanas_estan_presentes(self):
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertContains(respuesta, "Necesitan ayuda")
        self.assertContains(respuesta, "Ofrecen ayuda")

    def test_la_pestana_abierta_se_elige_por_parametro(self):
        respuesta = self.client.get(reverse("core:inicio"), {"ver": "ayudas"})
        self.assertEqual(respuesta.context["pestana"], "ayudas")

    def test_un_valor_raro_de_pestana_no_rompe_nada(self):
        respuesta = self.client.get(reverse("core:inicio"), {"ver": "<script>"})
        self.assertEqual(respuesta.context["pestana"], "necesidades")

    def test_las_urgentes_aparecen_primero(self):
        """En una emergencia el orden de la portada importa."""
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, urgencia="BAJA", zona="Zona baja"))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, urgencia="MEDIA", zona="Zona media"))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, urgencia="ALTA", zona="Zona alta"))

        respuesta = self.client.get(reverse("core:inicio"))
        urgencias = [s.urgencia for s in respuesta.context["solicitudes"]]

        self.assertEqual(urgencias, ["ALTA", "MEDIA", "BAJA"])

    def test_filtra_por_ciudad(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, ciudad="Pereira"))

        respuesta = self.client.get(reverse("core:inicio"), {"ciudad": "Pereira"})

        self.assertEqual(len(respuesta.context["solicitudes"]), 1)
        self.assertEqual(respuesta.context["solicitudes"][0].ciudad, "Pereira")

    def test_filtra_por_tipo_de_ayuda(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, tipo_ayuda="AGUA"))

        respuesta = self.client.get(reverse("core:inicio"), {"tipo": "AGUA"})

        self.assertEqual(len(respuesta.context["solicitudes"]), 1)

    def test_el_buscador_encuentra_por_descripcion(self):
        SolicitudAyuda.objects.create(
            **dict(DATOS_SOLICITUD, descripcion="Necesitamos mercado para tres dias.")
        )
        respuesta = self.client.get(reverse("core:inicio"), {"q": "mercado"})
        self.assertEqual(len(respuesta.context["solicitudes"]), 1)

    def test_el_buscador_encuentra_por_tipo_de_ayuda(self):
        """
        Alguien busca "alojamiento" y debe encontrarlo aunque esa palabra no
        aparezca en la descripcion: el tipo de ayuda tambien cuenta.
        """
        SolicitudAyuda.objects.create(
            **dict(
                DATOS_SOLICITUD,
                tipo_ayuda="ALOJAMIENTO",
                descripcion="Nos quedamos sin casa y no tenemos donde dormir.",
            )
        )
        respuesta = self.client.get(reverse("core:inicio"), {"q": "alojamiento"})
        self.assertEqual(len(respuesta.context["solicitudes"]), 1)

    def test_el_buscador_ignora_tildes(self):
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, ciudad="Medellín"))
        respuesta = self.client.get(reverse("core:inicio"), {"q": "medellin"})
        self.assertEqual(len(respuesta.context["solicitudes"]), 1)

    def test_varias_palabras_se_combinan(self):
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, ciudad="Armenia"))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, ciudad="Pereira"))

        respuesta = self.client.get(reverse("core:inicio"), {"q": "mercado Armenia"})

        self.assertEqual(len(respuesta.context["solicitudes"]), 1)
        self.assertEqual(respuesta.context["solicitudes"][0].ciudad, "Armenia")

    def test_una_busqueda_sin_resultados_no_rompe(self):
        respuesta = self.client.get(reverse("core:inicio"), {"q": "xyzabc123"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["resultados_busqueda"], 0)

    def test_el_panel_de_resumen_trae_los_numeros(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        OfertaAyuda.objects.create(**DATOS_OFERTA)

        respuesta = self.client.get(reverse("core:inicio"))
        resumen = respuesta.context["resumen"]

        self.assertEqual(resumen["solicitudes"], 1)
        self.assertEqual(resumen["ofertas"], 1)
        self.assertEqual(resumen["coincidencias"], 1)

    def test_no_muestra_lo_bloqueado_ni_lo_resuelto(self):
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.BLOQUEADA))
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.RESUELTA))

        respuesta = self.client.get(reverse("core:inicio"))

        self.assertEqual(len(respuesta.context["solicitudes"]), 0)


class MuroDeActividadTests(TestCase):
    """El muro reune lo publicado en las cuatro secciones."""

    def test_reune_publicaciones_de_todas_las_secciones(self):
        from puntos.models import PuntoAyuda
        from reportes.models import ReporteComunitario

        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        OfertaAyuda.objects.create(**DATOS_OFERTA)
        PuntoAyuda.objects.create(
            nombre="Salon comunal",
            ciudad="Armenia",
            zona="Centro",
            tipo="ACOPIO",
            horario="8am a 6pm",
            descripcion="Centro de acopio comunitario del barrio.",
            fuente_informacion="Lo vi personalmente",
        )
        ReporteComunitario.objects.create(
            ciudad="Armenia",
            zona="Centro",
            tipo_reporte="VIA_BLOQUEADA",
            urgencia="ALTA",
            descripcion="La via esta bloqueada por escombros.",
        )

        respuesta = self.client.get(reverse("core:inicio"))
        tipos = {item["tipo"] for item in respuesta.context["actividad"]}

        self.assertEqual(tipos, {"solicitud", "ayuda", "punto", "reporte"})

    def test_ordena_lo_mas_reciente_primero(self):
        SolicitudAyuda.objects.create(**DATOS_SOLICITUD)
        OfertaAyuda.objects.create(**DATOS_OFERTA)

        respuesta = self.client.get(reverse("core:inicio"))
        actividad = respuesta.context["actividad"]

        self.assertEqual(actividad[0]["tipo"], "ayuda")
        self.assertGreaterEqual(actividad[0]["creado"], actividad[1]["creado"])

    def test_el_muro_ignora_lo_bloqueado(self):
        SolicitudAyuda.objects.create(**dict(DATOS_SOLICITUD, estado=Estado.BLOQUEADA))
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(len(respuesta.context["actividad"]), 0)
