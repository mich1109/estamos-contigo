"""Utilidades compartidas por las apps de ESTAMOS CONTIGO."""
import re
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError

EXTENSIONES_IMAGEN_PERMITIDAS = (".jpg", ".jpeg", ".png", ".webp")

# Patrones que no tienen ningun uso legitimo en el texto de una publicacion y
# si aparecen en intentos de inyeccion.
PATRONES_PELIGROSOS = (
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"\bon\w+\s*=", re.IGNORECASE),  # onerror=, onclick=, etc.
)

LARGO_MAXIMO_TEXTO = 3000

# Departamentos de Colombia, para el desplegable de los formularios.
DEPARTAMENTOS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá",
    "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba",
    "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena",
    "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío", "Risaralda",
    "San Andrés y Providencia", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]

# Municipios mas relevantes para esta emergencia y su departamento.
#
# Sirve para completar el departamento cuando la persona solo escribe la
# ciudad, de modo que el directorio pueda agrupar como "Manizales — Caldas".
# La clave esta normalizada (sin tildes ni mayusculas) para que coincida sin
# importar como se escriba.
_MUNICIPIOS = {
    # Caldas
    "manizales": "Caldas", "villamaria": "Caldas", "chinchina": "Caldas",
    "la dorada": "Caldas", "riosucio": "Caldas", "anserma": "Caldas",
    # Risaralda
    "pereira": "Risaralda", "dosquebradas": "Risaralda",
    "santa rosa de cabal": "Risaralda", "la virginia": "Risaralda",
    # Quindío
    "armenia": "Quindío", "calarca": "Quindío", "montenegro": "Quindío",
    "circasia": "Quindío", "quimbaya": "Quindío", "la tebaida": "Quindío",
    "salento": "Quindío", "filandia": "Quindío",
    # Valle del Cauca
    "cali": "Valle del Cauca", "santiago de cali": "Valle del Cauca",
    "buenaventura": "Valle del Cauca", "palmira": "Valle del Cauca",
    "yumbo": "Valle del Cauca", "jamundi": "Valle del Cauca",
    "tulua": "Valle del Cauca", "buga": "Valle del Cauca",
    "cartago": "Valle del Cauca",
    # Chocó
    "quibdo": "Chocó", "san jose del palmar": "Chocó", "istmina": "Chocó",
    "condoto": "Chocó", "tado": "Chocó", "novita": "Chocó",
    "bahia solano": "Chocó", "nuqui": "Chocó",
    # Cundinamarca y Bogotá
    "bogota": "Cundinamarca", "bogota d.c.": "Cundinamarca",
    "bogota dc": "Cundinamarca", "soacha": "Cundinamarca",
    "chia": "Cundinamarca", "zipaquira": "Cundinamarca",
    "fusagasuga": "Cundinamarca", "girardot": "Cundinamarca",
    # Otras capitales
    "medellin": "Antioquia", "bello": "Antioquia", "itagui": "Antioquia",
    "envigado": "Antioquia", "apartado": "Antioquia",
    "barranquilla": "Atlántico", "soledad": "Atlántico",
    "cartagena": "Bolívar", "bucaramanga": "Santander",
    "floridablanca": "Santander", "cucuta": "Norte de Santander",
    "santa marta": "Magdalena", "villavicencio": "Meta",
    "pasto": "Nariño", "ipiales": "Nariño", "popayan": "Cauca",
    "neiva": "Huila", "ibague": "Tolima", "monteria": "Córdoba",
    "sincelejo": "Sucre", "valledupar": "Cesar", "riohacha": "La Guajira",
    "tunja": "Boyacá", "florencia": "Caquetá", "yopal": "Casanare",
    "arauca": "Arauca", "mocoa": "Putumayo", "leticia": "Amazonas",
    "san andres": "San Andrés y Providencia",
}


# El indice normalizado se construye al final del modulo, cuando `normalizar`
# ya esta definida. Ver DEPARTAMENTO_POR_MUNICIPIO abajo.


def validar_texto_publico(texto, nombre_campo="", formulario=None):
    """
    Normaliza y revisa un texto escrito por el publico.

    Django escapa el HTML al renderizar, asi que esta no es la unica defensa
    contra XSS: es una capa adicional que ademas quita caracteres de control y
    limita el largo, para que nadie pueda reventar la maquetacion ni la base
    de datos con un texto enorme.
    """
    if not isinstance(texto, str):
        return texto

    # Quita caracteres de control invisibles, que solo sirven para ofuscar.
    limpio = "".join(c for c in texto if c == "\n" or c == "\t" or ord(c) >= 32)
    # Colapsa saltos de linea excesivos.
    limpio = re.sub(r"\n{4,}", "\n\n\n", limpio).strip()

    if len(limpio) > LARGO_MAXIMO_TEXTO:
        raise ValidationError(
            f"El texto es demasiado largo. El maximo es {LARGO_MAXIMO_TEXTO} caracteres."
        )

    for patron in PATRONES_PELIGROSOS:
        if patron.search(limpio):
            raise ValidationError(
                "El texto contiene codigo que no esta permitido. "
                "Escribe tu mensaje sin etiquetas HTML."
            )

    return limpio


def normalizar(texto):
    """
    Deja un texto comparable: sin tildes, sin espacios sobrantes, en minusculas.

    Es lo que permite que "Armenia", "armenia" y "ARMENIA " se traten como la
    misma ciudad al buscar coincidencias.
    """
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def validar_imagen(archivo):
    """
    Valida una imagen subida por el publico.

    La idea es que CUALQUIER foto tomada con un celular funcione: si pesa mas
    de la cuenta, se encoge automaticamente en lugar de rechazarla. Solo se
    rechaza lo que no es una imagen de verdad.

    Comprueba, en este orden:
      1. Extension: solo formatos de imagen conocidos.
      2. Contenido real: se abre con Pillow y se verifica que sea de verdad
         una imagen. Sin esto, alguien podria subir un ejecutable renombrado
         a .jpg.
      3. Dimensiones absurdas: una imagen de 30.000 x 30.000 px cabe en pocos
         KB comprimida pero consume gigas de memoria al procesarla.
      4. Peso: si excede el limite, se reduce en vez de rechazarse.
    """
    if not archivo:
        return archivo

    # Tope absoluto para no agotar la memoria al abrir el archivo. Muy por
    # encima de cualquier foto de celular (las mas pesadas rondan los 15 MB).
    tope_mb = getattr(settings, "MAX_UPLOAD_ABSOLUTO_MB", 40)
    if archivo.size > tope_mb * 1024 * 1024:
        raise ValidationError(
            f"El archivo pesa mas de {tope_mb} MB. "
            "Toma la foto con la camara normal de tu celular."
        )

    nombre = (archivo.name or "").lower()
    if not nombre.endswith(EXTENSIONES_IMAGEN_PERMITIDAS):
        permitidas = ", ".join(EXTENSIONES_IMAGEN_PERMITIDAS)
        raise ValidationError(f"Formato no permitido. Usa una imagen: {permitidas}.")

    # Verificacion del contenido real del archivo.
    try:
        from PIL import Image

        posicion = archivo.tell()
        archivo.seek(0)
        imagen = Image.open(archivo)
        imagen.verify()  # Lanza excepcion si el contenido no es una imagen.

        archivo.seek(0)
        imagen = Image.open(archivo)
        ancho, alto = imagen.size
        formato = (imagen.format or "").upper()
        archivo.seek(posicion)
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(
            "El archivo no es una imagen valida o esta danado. "
            "Intenta con otra foto."
        )

    if formato not in ("JPEG", "PNG", "WEBP"):
        raise ValidationError(
            "Formato de imagen no permitido. Usa una foto JPG, PNG o WEBP."
        )

    limite_px = getattr(settings, "MAX_IMAGE_DIMENSION", 12000)
    if ancho > limite_px or alto > limite_px:
        raise ValidationError(
            "La imagen tiene dimensiones demasiado grandes. "
            "Toma la foto con tu celular normalmente o reduce su tamano."
        )

    # Si la foto es pesada, se reduce en vez de rechazarla: quien esta pidiendo
    # ayuda no deberia pelear con el tamano de su propia foto.
    limite_mb = getattr(settings, "MAX_UPLOAD_SIZE_MB", 5)
    if archivo.size > limite_mb * 1024 * 1024:
        return _reducir_imagen(archivo, formato)

    return archivo


def _reducir_imagen(archivo, formato):
    """
    Encoge una foto demasiado pesada conservando su aspecto.

    Se reduce el lado mayor a 1920 px y se recomprime. Una foto de celular de
    12 MB queda en torno a 300 KB, suficiente para verse bien en el sitio.

    Si algo falla, se devuelve el archivo original: es preferible guardar una
    foto grande a perder la publicacion de alguien que necesita ayuda.
    """
    import io

    from django.core.files.uploadedfile import InMemoryUploadedFile
    from PIL import Image, ImageOps

    LADO_MAXIMO = 1920

    try:
        archivo.seek(0)
        imagen = Image.open(archivo)

        # Respeta la orientacion con que se tomo la foto: sin esto, las fotos
        # verticales de celular aparecen acostadas.
        imagen = ImageOps.exif_transpose(imagen)

        if imagen.mode in ("RGBA", "P", "LA"):
            fondo = Image.new("RGB", imagen.size, (255, 255, 255))
            fondo.paste(imagen, mask=imagen.split()[-1] if imagen.mode != "P" else None)
            imagen = fondo
        elif imagen.mode != "RGB":
            imagen = imagen.convert("RGB")

        imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.LANCZOS)

        buffer = io.BytesIO()
        imagen.save(buffer, format="JPEG", quality=82, optimize=True, progressive=True)
        buffer.seek(0)

        nombre = (archivo.name or "foto.jpg").rsplit(".", 1)[0] + ".jpg"

        return InMemoryUploadedFile(
            buffer,
            "ImageField",
            nombre,
            "image/jpeg",
            buffer.getbuffer().nbytes,
            None,
        )
    except Exception:
        archivo.seek(0)
        return archivo


def obtener_ip(request):
    """
    Devuelve la IP del visitante.

    Se guarda junto a cada publicacion para poder rastrear abuso. Nunca se
    muestra en el sitio publico.
    """
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# Indice municipio normalizado -> departamento. Se construye aqui, al final,
# porque necesita que `normalizar` ya exista.
DEPARTAMENTO_POR_MUNICIPIO = {
    normalizar(municipio): departamento
    for municipio, departamento in _MUNICIPIOS.items()
}


def departamento_de(municipio):
    """Devuelve el departamento de un municipio conocido, o cadena vacia."""
    return DEPARTAMENTO_POR_MUNICIPIO.get(normalizar(municipio), "")
