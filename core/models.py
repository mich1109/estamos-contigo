"""
Modelos abstractos compartidos por las apps de ESTAMOS CONTIGO.

Ningun modelo concreto vive aqui: esta app solo aporta la base comun de
timestamps, estado y ubicacion, mas los gestores que filtran lo que es visible
para el publico.
"""
from django.db import models

from core.choices import Estado


class RegistroPublicoManager(models.Manager):
    """Gestor que devuelve unicamente lo que puede verse en el sitio publico."""

    def visibles(self):
        """Todo lo que no ha sido bloqueado por el administrador."""
        return self.get_queryset().exclude(estado=Estado.BLOQUEADA)

    def activas(self):
        """Registros vigentes: ni resueltos ni bloqueados."""
        return self.get_queryset().filter(estado=Estado.ACTIVA)


class RegistroComunitario(models.Model):
    """
    Base de todo contenido publicado por la comunidad.

    Los registros se publican de inmediato, sin moderacion previa. El
    administrador puede despues cerrarlos (RESUELTA) o retirarlos (BLOQUEADA).
    """

    estado = models.CharField(
        "Estado",
        max_length=12,
        choices=Estado.choices,
        default=Estado.ACTIVA,
        db_index=True,
    )
    creado = models.DateTimeField("Fecha de publicacion", auto_now_add=True, db_index=True)
    actualizado = models.DateTimeField("Ultima actualizacion", auto_now=True)
    ip_origen = models.GenericIPAddressField(
        "IP de origen",
        null=True,
        blank=True,
        help_text="Se registra para poder rastrear abuso. No se muestra al publico.",
    )
    nota_admin = models.TextField(
        "Nota interna del administrador",
        blank=True,
        help_text="Visible solo en el panel. Por ejemplo: por que se cerro o bloqueo.",
    )

    objects = RegistroPublicoManager()

    class Meta:
        abstract = True
        ordering = ["-creado"]

    @property
    def esta_activa(self):
        return self.estado == Estado.ACTIVA

    @property
    def esta_bloqueada(self):
        return self.estado == Estado.BLOQUEADA


class UbicacionMixin(models.Model):
    """
    Datos geograficos de todo lo que aparece en el mapa.

    La latitud y la longitud son opcionales: alguien puede publicar sin marcar
    el mapa, y el registro sigue siendo util en los listados aunque no tenga
    marcador.
    """

    ciudad = models.CharField("Ciudad o municipio", max_length=100, db_index=True)
    departamento = models.CharField(
        "Departamento",
        max_length=60,
        blank=True,
        db_index=True,
        help_text="Ej: Caldas, Risaralda, Valle del Cauca. Ayuda a ubicar el municipio.",
    )
    # Copia de ciudad + zona sin tildes ni mayusculas, para poder buscar
    # "medellin" y encontrar "Medellín". Se rellena sola al guardar; ni el
    # publico ni el administrador la escriben.
    busqueda_lugar = models.CharField(
        max_length=260,
        blank=True,
        editable=False,
        db_index=True,
    )
    zona = models.CharField(
        "Zona o barrio",
        max_length=150,
        help_text="Barrio, vereda, comuna o punto de referencia.",
    )
    latitud = models.DecimalField(
        "Latitud",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitud = models.DecimalField(
        "Longitud",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["latitud", "longitud"])]

    def save(self, *args, **kwargs):
        """
        Mantiene al dia los campos derivados.

        - `departamento` se deduce del municipio cuando la persona no lo
          escribio, usando la tabla de municipios conocidos. Asi el listado
          puede agrupar por "Manizales — Caldas" sin pedirselo al publico.
        - `busqueda_lugar` es la copia sin tildes que usa el buscador.
        """
        from core.utils import DEPARTAMENTO_POR_MUNICIPIO, normalizar

        if not self.departamento:
            self.departamento = DEPARTAMENTO_POR_MUNICIPIO.get(
                normalizar(self.ciudad), ""
            )

        self.busqueda_lugar = " ".join([
            normalizar(self.ciudad),
            normalizar(self.zona),
            normalizar(self.departamento),
        ]).strip()

        # Si se guarda con update_fields hay que incluir el campo derivado,
        # o quedaria desactualizado.
        campos = kwargs.get("update_fields")
        if campos is not None and "busqueda_lugar" not in campos:
            kwargs["update_fields"] = list(campos) + ["busqueda_lugar"]

        super().save(*args, **kwargs)

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None

    @property
    def ubicacion_texto(self):
        return f"{self.zona}, {self.ciudad}"

    @property
    def lugar(self):
        """
        Etiqueta del municipio con su departamento.

        Es lo que se usa para agrupar en el directorio: "Manizales — Caldas".
        Si no se conoce el departamento, se muestra solo el municipio.
        """
        if self.departamento:
            return f"{self.ciudad} — {self.departamento}"
        return self.ciudad


class ContactoMixin(models.Model):
    """
    Datos de contacto publicos.

    Se muestran en el sitio junto al aviso de verificacion. Al menos uno de los
    dos campos debe venir lleno; esa validacion vive en los formularios.
    """

    contacto_telefono = models.CharField(
        "Telefono o WhatsApp",
        max_length=30,
        blank=True,
    )
    contacto_email = models.EmailField("Correo electronico", blank=True)

    class Meta:
        abstract = True

    @property
    def tiene_contacto(self):
        return bool(self.contacto_telefono or self.contacto_email)
