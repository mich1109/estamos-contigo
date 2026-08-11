"""Modulo 5 - Puntos de ayuda comunitarios."""
from django.db import models
from django.urls import reverse

from core.models import RegistroComunitario, UbicacionMixin


class TipoPunto(models.TextChoices):
    """
    Catalogo de servicios fisicos habilitados por la emergencia.

    Los primeros nueve existian desde el inicio y no se renombran: cambiar sus
    codigos invalidaria los registros ya guardados. Los siguientes se agregaron
    para cubrir el directorio nacional completo.
    """

    ACOPIO = "ACOPIO", "Centro de acopio"
    ALIMENTOS = "ALIMENTOS", "Entrega de alimentos"
    AGUA = "AGUA", "Punto de agua"
    REFUGIO = "REFUGIO", "Albergue temporal"
    DONACIONES = "DONACIONES", "Recepcion de donaciones"
    CARGA = "CARGA", "Punto de carga de celulares"
    SALUD = "SALUD", "Atencion medica"
    ORGANIZACION = "ORGANIZACION", "Organizacion comunitaria"
    # --- Ampliacion del directorio nacional ---
    SANGRE = "SANGRE", "Donacion de sangre"
    ALOJAMIENTO = "ALOJAMIENTO", "Alojamiento temporal"
    ROPA = "ROPA", "Recepcion de ropa"
    ABRIGO = "ABRIGO", "Recepcion de cobijas y colchonetas"
    ASEO = "ASEO", "Recepcion de kits de aseo"
    BEBES = "BEBES", "Articulos para bebes"
    ANIMALES = "ANIMALES", "Ayuda para animales"
    DINERO = "DINERO", "Canal oficial de donacion economica"
    SOCORRO = "SOCORRO", "Organismo de socorro"
    INFORMACION = "INFORMACION", "Punto de informacion"
    BUSQUEDA = "BUSQUEDA", "Personas desaparecidas o busqueda"
    OTRO = "OTRO", "Otro"


# Icono de cada tipo, usado en tarjetas, filtros y marcadores del mapa.
ICONOS_PUNTO = {
    TipoPunto.ACOPIO: "📦",
    TipoPunto.ALIMENTOS: "🍲",
    TipoPunto.AGUA: "💧",
    TipoPunto.REFUGIO: "🏠",
    TipoPunto.DONACIONES: "📦",
    TipoPunto.CARGA: "🔌",
    TipoPunto.SALUD: "🩺",
    TipoPunto.ORGANIZACION: "🤝",
    TipoPunto.SANGRE: "🩸",
    TipoPunto.ALOJAMIENTO: "🛏️",
    TipoPunto.ROPA: "👕",
    TipoPunto.ABRIGO: "🛏️",
    TipoPunto.ASEO: "🧼",
    TipoPunto.BEBES: "👶",
    TipoPunto.ANIMALES: "🐶",
    TipoPunto.DINERO: "💰",
    TipoPunto.SOCORRO: "🧑‍🚒",
    TipoPunto.INFORMACION: "📞",
    TipoPunto.BUSQUEDA: "🔎",
    TipoPunto.OTRO: "📍",
}


class EstadoVerificacion(models.TextChoices):
    """
    Que tan confiable es la informacion de este punto.

    Es distinto de `disponibilidad` (si el lugar opera o no) y de `estado`
    (moderacion). Aqui se responde: quien dice que esto es cierto.
    """

    CONFIRMADO = "CONFIRMADO", "Confirmado por fuente oficial"
    POR_CONFIRMAR = "POR_CONFIRMAR", "Pendiente de confirmacion oficial"
    CERRADO = "CERRADO", "Cerrado o inactivo"


# Necesidades que una persona puede tener, y que tipos de punto las resuelven.
# Es lo que alimenta los filtros de "Necesito ayuda" y "Quiero ayudar".
NECESIDADES = [
    ("alojamiento", "🏠 Necesito alojamiento", [TipoPunto.REFUGIO, TipoPunto.ALOJAMIENTO]),
    ("comida", "🍲 Necesito comida", [TipoPunto.ALIMENTOS]),
    ("agua", "💧 Necesito agua", [TipoPunto.AGUA]),
    ("medica", "🩺 Necesito atencion medica", [TipoPunto.SALUD]),
    ("sangre", "🩸 Donar sangre", [TipoPunto.SANGRE]),
    ("donar", "📦 Quiero donar", [TipoPunto.ACOPIO, TipoPunto.DONACIONES]),
    ("ropa", "👕 Donar ropa", [TipoPunto.ROPA, TipoPunto.ACOPIO]),
    ("aseo", "🧼 Donar articulos de aseo", [TipoPunto.ASEO, TipoPunto.ACOPIO]),
    ("bebes", "👶 Donar articulos para bebes", [TipoPunto.BEBES, TipoPunto.ACOPIO]),
    ("abrigo", "🛏️ Donar cobijas y colchonetas", [TipoPunto.ABRIGO, TipoPunto.ACOPIO]),
    ("animales", "🐶 Ayudar animales", [TipoPunto.ANIMALES]),
    ("dinero", "💰 Donar dinero", [TipoPunto.DINERO]),
    ("informacion", "📞 Necesito informacion", [TipoPunto.INFORMACION, TipoPunto.SOCORRO]),
]


class DisponibilidadPunto(models.TextChoices):
    """
    Estado operativo del lugar, distinto del estado de moderacion.

    Un punto puede estar CERRADO (ya no opera) y aun asi seguir ACTIVA en el
    sentido de moderacion: sigue publicado, solo que marcado como cerrado.
    """

    ACTIVO = "ACTIVO", "Activo"
    NO_DISPONIBLE = "NO_DISPONIBLE", "No disponible temporalmente"
    CERRADO = "CERRADO", "Cerrado"


class PuntoAyuda(RegistroComunitario, UbicacionMixin):
    """
    Un lugar comunitario que esta ayudando.

    El campo `verificado` es la unica marca que distingue un dato confirmado por
    la administracion de uno aportado por la comunidad. Por defecto es False y
    la interfaz muestra el aviso correspondiente.
    """

    nombre = models.CharField(
        "Nombre del lugar",
        max_length=150,
        help_text="Ej: Salon comunal La Milagrosa, Parroquia San Jose.",
    )
    tipo = models.CharField(
        "Tipo de punto",
        max_length=20,
        choices=TipoPunto.choices,
        db_index=True,
    )
    horario = models.CharField(
        "Horario de atencion",
        max_length=150,
        help_text="Ej: Lunes a sabado de 8am a 6pm. O 'Las 24 horas'.",
    )
    descripcion = models.TextField(
        "Descripcion",
        help_text="Que se hace en este punto, que se entrega o que se recibe.",
    )
    contacto = models.CharField(
        "Contacto",
        max_length=200,
        blank=True,
        help_text="Telefono, correo o nombre de la persona encargada.",
    )
    direccion = models.CharField(
        "Direccion",
        max_length=250,
        blank=True,
        help_text="Direccion exacta si la conoces.",
    )
    fuente_informacion = models.CharField(
        "Fuente de la informacion",
        max_length=200,
        help_text="De donde salio este dato. Ej: 'Lo vi personalmente', 'Me lo dijo un vecino'.",
    )
    disponibilidad = models.CharField(
        "Estado del punto",
        max_length=15,
        choices=DisponibilidadPunto.choices,
        default=DisponibilidadPunto.ACTIVO,
        db_index=True,
    )
    verificado = models.BooleanField(
        "Verificado por la administracion",
        default=False,
        help_text=(
            "Marcalo SOLO si confirmaste que este punto existe y opera. "
            "Mientras este sin marcar, el sitio avisa que es informacion "
            "aportada por la comunidad y sin verificar."
        ),
    )
    foto = models.ImageField(
        "Foto del lugar (opcional)",
        upload_to="puntos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Una foto ayuda a que las personas reconozcan el lugar al llegar.",
    )

    # --- Directorio nacional de ayuda ---

    verificacion = models.CharField(
        "Estado de la informacion",
        max_length=15,
        choices=EstadoVerificacion.choices,
        default=EstadoVerificacion.POR_CONFIRMAR,
        db_index=True,
        help_text=(
            "CONFIRMADO solo si la informacion proviene de una fuente oficial "
            "o de una organizacion reconocida."
        ),
    )
    elementos_recibidos = models.TextField(
        "Que reciben",
        blank=True,
        help_text="Un elemento por linea. Ej: Cobijas / Toallas / Kits de aseo.",
    )
    elementos_no_recibidos = models.TextField(
        "Que NO reciben",
        blank=True,
        help_text=(
            "Un elemento por linea. Evita que la gente lleve cosas que van a "
            "ser rechazadas. Ej: Medicamentos / Alimentos perecederos."
        ),
    )
    servicios = models.TextField(
        "Que se puede hacer alli",
        blank=True,
        help_text="Un servicio por linea. Ej: Alojamiento / Alimentacion / Atencion a menores.",
    )
    url_fuente = models.URLField(
        "Enlace a la fuente",
        max_length=500,
        blank=True,
        help_text="Enlace a la publicacion oficial que respalda esta informacion.",
    )
    fecha_verificacion = models.DateField(
        "Fecha de verificacion",
        null=True,
        blank=True,
        help_text="Cuando se comprobo por ultima vez que esta informacion sigue vigente.",
    )
    hora_verificacion = models.TimeField(
        "Hora de verificacion",
        null=True,
        blank=True,
    )
    destacado = models.BooleanField(
        "⭐ Punto recomendado",
        default=False,
        help_text="Aparece primero en los listados.",
    )
    prioritario = models.BooleanField(
        "🚨 Atencion prioritaria",
        default=False,
        help_text="Se resalta como punto critico durante la emergencia.",
    )

    class Meta:
        verbose_name = "Punto de ayuda"
        verbose_name_plural = "Puntos de ayuda"
        # Primero lo urgente, luego lo destacado, luego lo confirmado.
        ordering = ["-prioritario", "-destacado", "-verificado", "-creado"]
        indexes = [
            models.Index(fields=["estado", "disponibilidad"]),
            models.Index(fields=["ciudad", "tipo"]),
            models.Index(fields=["latitud", "longitud"]),
            models.Index(fields=["verificacion", "ciudad"]),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()}) - {self.ciudad}"

    def get_absolute_url(self):
        return reverse("puntos:detalle", args=[self.pk])

    @property
    def esta_operando(self):
        return self.disponibilidad == DisponibilidadPunto.ACTIVO

    @property
    def icono(self):
        """Emoji del tipo de punto, para tarjetas y marcadores."""
        return ICONOS_PUNTO.get(self.tipo, "📍")

    @property
    def punto_verificacion(self):
        """Circulo de color segun que tan confiable es la informacion."""
        return {
            EstadoVerificacion.CONFIRMADO: "🟢",
            EstadoVerificacion.POR_CONFIRMAR: "🟡",
            EstadoVerificacion.CERRADO: "🔴",
        }.get(self.verificacion, "🟡")

    @property
    def esta_confirmado(self):
        return self.verificacion == EstadoVerificacion.CONFIRMADO

    def _lineas(self, texto):
        """Convierte un campo de varias lineas en una lista limpia."""
        if not texto:
            return []
        return [linea.strip(" -•\t") for linea in texto.splitlines() if linea.strip()]

    @property
    def lista_recibidos(self):
        return self._lineas(self.elementos_recibidos)

    @property
    def lista_no_recibidos(self):
        return self._lineas(self.elementos_no_recibidos)

    @property
    def lista_servicios(self):
        return self._lineas(self.servicios)

    @property
    def url_como_llegar(self):
        """
        Enlace para llegar al punto.

        Si hay coordenadas se usan, porque son inequivocas. Si no, se busca por
        direccion y ciudad, que es lo que la persona escribiria a mano.
        """
        from urllib.parse import quote

        if self.tiene_coordenadas:
            return (
                f"https://www.google.com/maps/dir/?api=1"
                f"&destination={self.latitud},{self.longitud}"
            )
        destino = quote(f"{self.direccion or self.nombre}, {self.ciudad}, Colombia")
        return f"https://www.google.com/maps/dir/?api=1&destination={destino}"

    @property
    def telefono_limpio(self):
        """Solo digitos, para el enlace tel:."""
        import re

        return re.sub(r"[^\d+]", "", self.contacto or "")

    @property
    def texto_para_compartir(self):
        """Mensaje que se envia al compartir el punto por WhatsApp."""
        verificacion = (
            "Verificado por la administracion"
            if self.verificado
            else "Informacion de la comunidad, sin verificar"
        )
        return (
            f"📍 ESTAMOS CONTIGO · {self.nombre} ({self.get_tipo_display()}) "
            f"en {self.zona}, {self.ciudad}. "
            f"Horario: {self.horario}. "
            f"{verificacion}:"
        )
