"""
Modulo 7 - Enlaces a informacion oficial.

Esta es la unica seccion del sitio que NO es contenido comunitario: solo la
administracion puede crear entradas aqui, y cada una debe apuntar a una fuente
oficial real mediante su URL. La plataforma no genera informacion oficial
propia: solo enlaza a la de las instituciones.
"""
from django.db import models


class CategoriaInformacion(models.TextChoices):
    SISMICA = "SISMICA", "Informacion sismica"
    RECOMENDACIONES = "RECOMENDACIONES", "Recomendaciones"
    COMUNICADOS = "COMUNICADOS", "Comunicados"
    CENTROS = "CENTROS", "Centros de atencion"
    MUNICIPAL = "MUNICIPAL", "Informacion municipal"
    DEPARTAMENTAL = "DEPARTAMENTAL", "Informacion departamental"


ICONOS_CATEGORIA = {
    CategoriaInformacion.SISMICA: "🌍",
    CategoriaInformacion.RECOMENDACIONES: "📋",
    CategoriaInformacion.COMUNICADOS: "📣",
    CategoriaInformacion.CENTROS: "🏥",
    CategoriaInformacion.MUNICIPAL: "🏛️",
    CategoriaInformacion.DEPARTAMENTAL: "🗺️",
}


class InformacionOficial(models.Model):
    """
    Un enlace a informacion publicada por una institucion oficial.

    Se guarda siempre la URL de origen para que cualquiera pueda ir a la fuente
    y comprobarla. No se copia el contenido de la institucion: se enlaza.
    """

    titulo = models.CharField("Titulo", max_length=200)
    descripcion = models.TextField(
        "Descripcion",
        help_text="Resumen breve de que contiene el enlace. No copies el comunicado completo.",
    )
    institucion = models.CharField(
        "Institucion",
        max_length=150,
        db_index=True,
        help_text="Nombre exacto de la entidad que publico la informacion. "
        "Ej: Servicio Geologico Colombiano, UNGRD, Alcaldia de Armenia.",
    )
    url = models.URLField(
        "URL de la fuente oficial",
        max_length=500,
        help_text="Enlace directo a la pagina oficial. Es obligatorio: sin fuente "
        "verificable la entrada no debe publicarse.",
    )
    categoria = models.CharField(
        "Categoria",
        max_length=20,
        choices=CategoriaInformacion.choices,
        db_index=True,
    )
    fecha = models.DateField(
        "Fecha de la informacion",
        db_index=True,
        help_text="Fecha en que la institucion publico esta informacion.",
    )
    destacada = models.BooleanField(
        "Destacar",
        default=False,
        help_text="Las entradas destacadas aparecen primero en el listado.",
    )
    publicada = models.BooleanField(
        "Publicada",
        default=True,
        help_text="Desmarcalo para ocultarla del sitio sin borrarla.",
    )
    creado = models.DateTimeField("Agregada el", auto_now_add=True)
    actualizado = models.DateTimeField("Actualizada el", auto_now=True)

    class Meta:
        verbose_name = "Informacion oficial"
        verbose_name_plural = "Informacion oficial"
        ordering = ["-destacada", "-fecha", "-creado"]
        indexes = [models.Index(fields=["categoria", "fecha"])]

    def __str__(self):
        return f"{self.titulo} ({self.institucion})"

    @property
    def icono(self):
        return ICONOS_CATEGORIA.get(self.categoria, "📄")
