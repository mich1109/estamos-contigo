"""
Carga el directorio inicial de puntos de ayuda por la emergencia.

ORIGEN DE LOS DATOS
Los puntos, direcciones y listas de elementos de este archivo fueron aportados
por la administradora del sitio, que los recopilo de las fuentes que se citan
en cada registro (alcaldias, bancos de alimentos, Cruz Roja).

Esta carga NO verifica nada por su cuenta: no consulta internet ni comprueba
que los lugares sigan operando. El estado de verificacion de cada punto es el
que la administradora indico. Si un punto deja de funcionar, hay que cerrarlo
desde el panel.

Donde no se dispuso de direccion, telefono u horario, el campo queda VACIO a
proposito. Nunca se inventa un dato de contacto en una emergencia.

Uso:
    python manage.py cargar_directorio
    python manage.py cargar_directorio --actualizar   (sobreescribe existentes)
"""
from datetime import date

from django.core.management.base import BaseCommand

from core.choices import Estado
from puntos.models import DisponibilidadPunto, EstadoVerificacion, PuntoAyuda

CONFIRMADO = EstadoVerificacion.CONFIRMADO
POR_CONFIRMAR = EstadoVerificacion.POR_CONFIRMAR

# Coordenadas aproximadas del centro de cada ciudad. Solo se usan para que el
# punto aparezca en el mapa en la ciudad correcta cuando no hay direccion
# exacta geolocalizada. La direccion escrita es siempre la referencia valida.
CENTROS = {
    "Manizales": (5.0689, -75.5174),
    "Pereira": (4.8133, -75.6961),
    "Armenia": (4.5339, -75.6811),
    "Cali": (3.4516, -76.5320),
    "Bogotá": (4.7110, -74.0721),
    "Quibdó": (5.6947, -76.6611),
    "San José del Palmar": (4.8951, -76.2281),
    "Buenaventura": (3.8801, -77.0313),
}

# Departamento de cada municipio. Es division politica de Colombia, no un dato
# sobre la emergencia: sirve para agrupar el directorio como "Manizales — Caldas".
DEPARTAMENTOS = {
    "Manizales": "Caldas",
    "Pereira": "Risaralda",
    "Armenia": "Quindío",
    "Cali": "Valle del Cauca",
    "Bogotá": "Cundinamarca",
    "Quibdó": "Chocó",
    "San José del Palmar": "Chocó",
    "Buenaventura": "Valle del Cauca",
}

PUNTOS = [
    # ------------------------------------------------------------------ MANIZALES
    {
        "nombre": "Coliseo Mayor Jorge Arango Uribe",
        "ciudad": "Manizales",
        "zona": "Coliseos",
        "direccion": "",
        "tipo": "REFUGIO",
        "descripcion": (
            "Albergue temporal para personas afectadas por el terremoto que "
            "necesitan un lugar seguro donde permanecer."
        ),
        "servicios": (
            "Alojamiento temporal\n"
            "Atencion a ninos y ninas\n"
            "Atencion a adultos mayores\n"
            "Atencion a mujeres gestantes\n"
            "Atencion a personas con movilidad reducida"
        ),
        "horario": "",
        "contacto": "",
        "fuente_informacion": "Alcaldia de Manizales / Centro de Informacion de Manizales",
        "verificacion": CONFIRMADO,
        "destacado": True,
    },
    {
        "nombre": "Coliseo Menor Ramón Marín Vargas",
        "ciudad": "Manizales",
        "zona": "Avenida Lindsay",
        "direccion": "Entrada A, Avenida Lindsay",
        "tipo": "DONACIONES",
        "descripcion": (
            "Centro de recepcion de donaciones para las personas afectadas por "
            "la emergencia. Revisa la lista antes de ir: hay elementos que no "
            "se estan recibiendo."
        ),
        "elementos_recibidos": (
            "Cobijas\nFrazadas\nToallas\nKits de aseo\nToallas higienicas\n"
            "Panales para ninos\nPanales para adultos\nRopa nueva con etiqueta\n"
            "Alimento para perros\nAlimento para gatos\nEquipos ortopedicos"
        ),
        "elementos_no_recibidos": (
            "Medicamentos\nAlimentos perecederos\nRopa interior"
        ),
        "horario": "",
        "contacto": "",
        "fuente_informacion": "Alcaldia de Manizales / Centro de Informacion de Manizales",
        "verificacion": CONFIRMADO,
        "destacado": True,
    },
    {
        "nombre": "SIC de Aranjuez",
        "ciudad": "Manizales",
        "zona": "Aranjuez",
        "direccion": "",
        "tipo": "REFUGIO",
        "descripcion": (
            "Albergue temporal habilitado durante la emergencia. Confirma que "
            "siga operando antes de desplazarte."
        ),
        "servicios": "Alojamiento temporal",
        "horario": "",
        "contacto": "",
        "fuente_informacion": "Alcaldia de Manizales",
        # La administradora indico que este punto depende de la informacion
        # oficial mas reciente, asi que se carga pendiente de confirmar.
        "verificacion": POR_CONFIRMAR,
    },
    {
        "nombre": "Banco de Alimentos de Manizales",
        "ciudad": "Manizales",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": (
            "Centro de recepcion de donaciones. Forma parte de la red de bancos "
            "de alimentos que esta apoyando la emergencia."
        ),
        "horario": "",
        "contacto": "",
        "fuente_informacion": "Red de Bancos de Alimentos de Colombia (ABACO)",
        "verificacion": CONFIRMADO,
    },

    # ------------------------------------------------------------------ PEREIRA
    {
        "nombre": "Café Consota",
        "ciudad": "Pereira",
        "zona": "Villa Consota, Cuba",
        "direccion": "Manzanas 7 y 8, barrio Villa Consota, Cuba",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café Perla del Otún",
        "ciudad": "Pereira",
        "zona": "Cuba",
        "direccion": "Diagonal a la iglesia de los 2.500 Lotes, Cuba",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café El Remanso",
        "ciudad": "Pereira",
        "zona": "El Remanso",
        "direccion": "Avenida principal de El Remanso, junto al Centro de Salud",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café Kennedy",
        "ciudad": "Pereira",
        "zona": "Kennedy",
        "direccion": "Parque principal del barrio Kennedy",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café Ormaza",
        "ciudad": "Pereira",
        "zona": "Avenida del Río",
        "direccion": "Calle 3 Bis #5-38, Avenida del Río",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café San Nicolás",
        "ciudad": "Pereira",
        "zona": "San Nicolás",
        "direccion": "Carrera 14 Bis #28-38, antigua estación de Policía",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Café Comuna del Café",
        "ciudad": "Pereira",
        "zona": "Parque Industrial",
        "direccion": "Carrera 3 con Calle 59A, Parque Industrial",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio habilitado por la emergencia.",
        "fuente_informacion": "Alcaldia de Pereira",
        "verificacion": CONFIRMADO,
    },

    # ------------------------------------------------------------------ CALI
    {
        "nombre": "Plazoleta Jairo Varela",
        "ciudad": "Cali",
        "zona": "Centro",
        "direccion": "Plazoleta Jairo Varela",
        "tipo": "ACOPIO",
        "descripcion": (
            "Centro de acopio para apoyar a los organismos de socorro y a las "
            "personas afectadas por la emergencia."
        ),
        "elementos_recibidos": (
            "Agua\nGuantes de construccion\nGafas de seguridad\nCascos\nColchonetas"
        ),
        "fuente_informacion": "Alcaldia de Santiago de Cali",
        "verificacion": CONFIRMADO,
        "destacado": True,
    },
    {
        "nombre": "Hospital Universitario del Valle",
        "ciudad": "Cali",
        "zona": "",
        "direccion": "",
        "tipo": "SANGRE",
        "descripcion": (
            "Punto de donacion de sangre y atencion relacionada con la "
            "emergencia. Recibe donaciones de diferentes grupos sanguineos."
        ),
        "servicios": "Donacion de sangre\nAtencion medica relacionada con la emergencia",
        "fuente_informacion": "Hospital Universitario del Valle",
        "verificacion": CONFIRMADO,
        "prioritario": True,
    },
    {
        "nombre": "Fundación Arquidiocesana Banco de Alimentos de Cali",
        "ciudad": "Cali",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de recepcion de ayudas para las personas afectadas.",
        "fuente_informacion": "Fundacion Arquidiocesana Banco de Alimentos de Cali",
        "verificacion": CONFIRMADO,
    },

    # ------------------------------------------------------------------ ARMENIA
    {
        "nombre": "Banco de Alimentos Monseñor Roberto López Londoño",
        "ciudad": "Armenia",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": (
            "Centro de recepcion de donaciones para las personas afectadas por "
            "la emergencia."
        ),
        "fuente_informacion": "Banco de Alimentos Monsenor Roberto Lopez Londono",
        "verificacion": CONFIRMADO,
    },

    # ------------------------------------------------------------------ BOGOTÁ
    {
        "nombre": "SAMU Sur",
        "ciudad": "Bogotá",
        "zona": "Sur",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio y ayuda humanitaria.",
        "fuente_informacion": "Cruz Roja Colombiana / Alcaldia de Bogota",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "SAMU Norte",
        "ciudad": "Bogotá",
        "zona": "Norte",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio y ayuda humanitaria.",
        "fuente_informacion": "Cruz Roja Colombiana / Alcaldia de Bogota",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Centro de Salvamento Acuático",
        "ciudad": "Bogotá",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio y ayuda humanitaria.",
        "fuente_informacion": "Cruz Roja Colombiana",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Sede administrativa de la Cruz Roja",
        "ciudad": "Bogotá",
        "zona": "",
        "direccion": "",
        "tipo": "SOCORRO",
        "descripcion": "Centro de acopio y ayuda humanitaria de la Cruz Roja Colombiana.",
        "fuente_informacion": "Cruz Roja Colombiana",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Bodega de la Cruz Roja",
        "ciudad": "Bogotá",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio y ayuda humanitaria de la Cruz Roja Colombiana.",
        "fuente_informacion": "Cruz Roja Colombiana",
        "verificacion": CONFIRMADO,
    },
    {
        "nombre": "Palacio de los Deportes",
        "ciudad": "Bogotá",
        "zona": "",
        "direccion": "",
        "tipo": "ACOPIO",
        "descripcion": "Centro de acopio y apoyo humanitario por la emergencia.",
        "elementos_recibidos": (
            "Agua potable\nCobijas\nMantas\nColchonetas\n"
            "Alimentos no perecederos\nArticulos de higiene\n"
            "Suministros de primeros auxilios"
        ),
        "fuente_informacion": "Alcaldia Mayor de Bogota",
        "verificacion": CONFIRMADO,
        "destacado": True,
    },

    # ------------------------------- ZONAS SIN PUNTOS CONFIRMADOS TODAVIA
    # Se crean para que la ciudad exista en el directorio y la gente sepa que
    # se esta trabajando en ella, sin inventar ninguna direccion.
    {
        "nombre": "Puntos de ayuda en Quibdó",
        "ciudad": "Quibdó",
        "zona": "",
        "direccion": "",
        "tipo": "INFORMACION",
        "descripcion": (
            "Todavia no hay puntos fisicos con confirmacion oficial publicados "
            "en esta plataforma para Quibdo. La informacion sobre puntos de "
            "ayuda puede estar cambiando: consulta los canales de la Alcaldia y "
            "de la Gobernacion del Choco. En emergencia, llama al 123."
        ),
        "fuente_informacion": "Pendiente de confirmacion oficial",
        "verificacion": POR_CONFIRMAR,
    },
    {
        "nombre": "Ayuda de emergencia en San José del Palmar",
        "ciudad": "San José del Palmar",
        "zona": "",
        "direccion": "",
        "tipo": "INFORMACION",
        "descripcion": (
            "Zona directamente afectada. Todavia no hay direcciones de puntos "
            "fisicos con confirmacion oficial publicadas en esta plataforma. "
            "En cuanto las autoridades habiliten albergues, centros de acopio o "
            "puntos medicos, se agregaran aqui. En emergencia, llama al 123."
        ),
        "fuente_informacion": "Pendiente de confirmacion oficial",
        "verificacion": POR_CONFIRMAR,
        "prioritario": True,
    },
    {
        "nombre": "Puntos de ayuda en Buenaventura",
        "ciudad": "Buenaventura",
        "zona": "",
        "direccion": "",
        "tipo": "INFORMACION",
        "descripcion": (
            "Todavia no hay puntos fisicos con confirmacion oficial publicados "
            "en esta plataforma para Buenaventura. Consulta los canales de la "
            "Alcaldia Distrital. En emergencia, llama al 123."
        ),
        "fuente_informacion": "Pendiente de confirmacion oficial",
        "verificacion": POR_CONFIRMAR,
    },
]


class Command(BaseCommand):
    help = "Carga el directorio inicial de puntos de ayuda por la emergencia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--actualizar",
            action="store_true",
            help="Sobreescribe los puntos que ya existan con el mismo nombre y ciudad.",
        )

    def handle(self, *args, **opciones):
        hoy = date.today()
        creados = actualizados = omitidos = 0

        for datos in PUNTOS:
            ciudad = datos["ciudad"]
            lat, lng = CENTROS.get(ciudad, (None, None))

            campos = {
                "departamento": DEPARTAMENTOS.get(ciudad, ""),
                "zona": datos.get("zona") or ciudad,
                "direccion": datos.get("direccion", ""),
                "tipo": datos["tipo"],
                "descripcion": datos["descripcion"],
                "servicios": datos.get("servicios", ""),
                "elementos_recibidos": datos.get("elementos_recibidos", ""),
                "elementos_no_recibidos": datos.get("elementos_no_recibidos", ""),
                "horario": datos.get("horario", ""),
                "contacto": datos.get("contacto", ""),
                "fuente_informacion": datos["fuente_informacion"],
                "url_fuente": datos.get("url_fuente", ""),
                "verificacion": datos["verificacion"],
                "destacado": datos.get("destacado", False),
                "prioritario": datos.get("prioritario", False),
                "fecha_verificacion": hoy,
                "disponibilidad": DisponibilidadPunto.ACTIVO,
                "estado": Estado.ACTIVA,
                # `verificado` es la marca antigua del sitio; se mantiene
                # alineada con el estado nuevo para que la interfaz existente
                # siga mostrando lo correcto.
                "verificado": datos["verificacion"] == CONFIRMADO,
                "latitud": lat,
                "longitud": lng,
            }

            existente = PuntoAyuda.objects.filter(
                nombre=datos["nombre"], ciudad=ciudad
            ).first()

            if existente and not opciones["actualizar"]:
                omitidos += 1
                continue

            if existente:
                for clave, valor in campos.items():
                    setattr(existente, clave, valor)
                existente.save()
                actualizados += 1
            else:
                PuntoAyuda.objects.create(nombre=datos["nombre"], ciudad=ciudad, **campos)
                creados += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDirectorio cargado: {creados} creado(s), "
            f"{actualizados} actualizado(s), {omitidos} omitido(s)."
        ))

        total = PuntoAyuda.objects.filter(estado=Estado.ACTIVA).count()
        confirmados = PuntoAyuda.objects.filter(
            estado=Estado.ACTIVA, verificacion=CONFIRMADO
        ).count()
        self.stdout.write(f"Puntos activos: {total} ({confirmados} confirmados)")

        self.stdout.write(self.style.WARNING(
            "\nRECUERDA: esta carga no comprueba que los lugares sigan operando.\n"
            "Revisa cada punto y cierralo desde el panel si deja de funcionar."
        ))
