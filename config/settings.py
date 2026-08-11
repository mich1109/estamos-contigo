"""
Configuracion de Django para el proyecto ESTAMOS CONTIGO.

La base de datos se elige con la variable DB_ENGINE del archivo .env:
  - DB_ENGINE=mysql  -> usa MySQL con las credenciales del .env
  - vacio o ausente  -> usa SQLite (permite ejecutar el proyecto sin instalar nada)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(nombre, por_defecto=False):
    """Lee una variable de entorno como booleano."""
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "yes", "si", "on")


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "clave-de-desarrollo-insegura-cambiala-en-produccion",
)

DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# Render entrega el dominio real del sitio en esta variable. Se agrega solo,
# para no tener que escribirlo a mano al desplegar.
_dominio_render = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if _dominio_render and _dominio_render not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_dominio_render)


# --- Aplicaciones -----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Apps del proyecto
    "core",
    "solicitudes",
    "ayudas",
    "coincidencias",
    "mapa",
    "puntos",
    "reportes",
    "informacion",
    "panel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve el CSS, el JS y las imagenes del sitio. Sin el, en
    # Render la pagina se veria sin estilos. Va justo despues de seguridad.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.CabecerasSeguridadMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Detecta el idioma elegido (sesion, cookie o cabecera del navegador).
    # Va despues de SessionMiddleware y antes de CommonMiddleware.
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.LimitePublicacionesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                # Expone LANGUAGE_CODE y LANGUAGES al selector de idioma.
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Base de datos ----------------------------------------------------------

# Render entrega la base de datos PostgreSQL en esta variable. Si existe, tiene
# prioridad: es la senal de que el sitio esta publicado.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,       # reutiliza conexiones, va mas rapido
            conn_health_checks=True,
            ssl_require=True,       # Render exige conexion cifrada
        )
    }
elif os.getenv("DB_ENGINE", "").strip().lower() == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "ayuda_colombia"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Validacion de contrasenas (solo aplica al superusuario) ----------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internacionalizacion ---------------------------------------------------

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# Idiomas disponibles en el selector. El espanol es el idioma principal: el
# ingles esta para personas de organizaciones internacionales que apoyan la
# emergencia.
LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]


# --- Archivos estaticos y media ---------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
# En Render se puede montar un disco persistente en /var/data para que las
# fotos no se borren en cada actualizacion del sitio. Si no existe, se usa la
# carpeta local de siempre.
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "") or (BASE_DIR / "media")

# WhiteNoise comprime los archivos y les pone un nombre unico segun su
# contenido, para que el navegador los guarde en cache sin quedarse con
# versiones viejas.
#
# Ese modo exige un "manifiesto" que solo existe despues de ejecutar
# collectstatic. En los tests y en desarrollo no se ejecuta, asi que ahi se usa
# el almacenamiento normal: de lo contrario cualquier {% static %} fallaria.
_EN_RENDER = bool(os.getenv("RENDER"))

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if _EN_RENDER
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Autenticacion ----------------------------------------------------------
# El publico NO se registra ni inicia sesion. El unico usuario del sistema es
# el superusuario, que entra por /admin/ para cerrar casos y bloquear contenido.

LOGIN_URL = "/admin/login/"


# --- Seguridad --------------------------------------------------------------
#
# Django ya protege de serie contra inyeccion SQL (consultas parametrizadas por
# el ORM) y contra XSS en plantillas (escapado automatico). Lo de aqui son las
# capas adicionales.

# Cookies
SESSION_COOKIE_HTTPONLY = True          # JavaScript no puede leer la sesion
CSRF_COOKIE_HTTPONLY = False            # el token debe ser legible por el form
SESSION_COOKIE_SAMESITE = "Lax"         # bloquea envios desde otros sitios
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 8        # la sesion del admin caduca en 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cabeceras
SECURE_CONTENT_TYPE_NOSNIFF = True      # el navegador no adivina tipos MIME
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"                # nadie puede meter el sitio en un iframe

# Si el sitio va detras de un proxy o balanceador con HTTPS, esta cabecera es
# la que le dice a Django que la conexion original era segura.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# MODO_LOCAL permite revisar el sitio en el propio computador con DEBUG=False.
# Sin el, la redireccion a HTTPS impide abrirlo en 127.0.0.1, donde no hay
# certificado. Solo desactiva lo que depende de HTTPS; el resto de las
# protecciones (CSP, honeypot, limite por IP, validaciones) siguen activas.
MODO_LOCAL = env_bool("MODO_LOCAL", False)

if not DEBUG and not MODO_LOCAL:
    SECURE_SSL_REDIRECT = True          # todo el trafico pasa a HTTPS
    SESSION_COOKIE_SECURE = True        # cookies solo por HTTPS
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000      # un ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
elif not DEBUG and MODO_LOCAL:
    # Aviso en consola para que este modo no pase inadvertido al desplegar.
    import sys as _sys

    print(
        "\n  AVISO: MODO_LOCAL esta activo. El sitio NO obliga a usar HTTPS.\n"
        "  Sirve para revisarlo en tu computador. Ponlo en False antes de publicar.\n",
        file=_sys.stderr,
    )

# Origenes desde los que se aceptan formularios. Se deriva de ALLOWED_HOSTS
# para no tener que mantener dos listas.
CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if h not in ("*", "localhost", "127.0.0.1")
]


# --- Limites de subida de archivos ------------------------------------------

MAX_UPLOAD_SIZE_MB = 5
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
# Un formulario legitimo no manda cientos de campos: limitarlos frena ataques
# de agotamiento de memoria por hash collision.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100
DATA_UPLOAD_MAX_NUMBER_FILES = 5

# Las fotos subidas quedan con permisos de solo lectura.
FILE_UPLOAD_PERMISSIONS = 0o644

# Rechaza imagenes con dimensiones absurdas (decompression bomb).
MAX_IMAGE_DIMENSION = 12000

# Cuantas publicaciones puede hacer una misma IP por hora. Holgado a proposito:
# en una emergencia alguien puede publicar por si y por varios vecinos.
MAX_PUBLICACIONES_POR_HORA = 15


# --- Registro de eventos ----------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detallado": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "consola": {
            "class": "logging.StreamHandler",
            "formatter": "detallado",
        },
        "archivo_seguridad": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "seguridad.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "detallado",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # Django registra aqui intentos de CSRF, hosts invalidos y otros
        # indicios de ataque. Quedan en seguridad.log para poder revisarlos.
        "django.security": {
            "handlers": ["consola", "archivo_seguridad"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["consola", "archivo_seguridad"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
