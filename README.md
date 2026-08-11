# 🇨🇴 ESTAMOS CONTIGO

*Juntos somos más fuertes · Conecta · Comparte · Ayuda*

Plataforma web comunitaria para conectar personas afectadas por un terremoto
con personas que pueden brindarles ayuda.

> **⚠️ Esta plataforma NO reemplaza a los organismos oficiales de emergencia.**
> No está afiliada a Bomberos, Policía, Defensa Civil, Cruz Roja, alcaldías ni
> ninguna entidad del Estado. Ante peligro inmediato: **123**.

---

## Índice

1. [Qué hace](#qué-hace)
2. [Decisiones de diseño](#decisiones-de-diseño)
3. [Tecnologías](#tecnologías)
4. [Instalación paso a paso](#instalación-paso-a-paso)
5. [Seguridad](#seguridad)
6. [Configurar MySQL](#configurar-mysql)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Base de datos](#base-de-datos)
9. [Comandos útiles](#comandos-útiles)
10. [Antes de lanzarla al público](#antes-de-lanzarla-al-público)
11. [Lista de pruebas](#lista-de-pruebas)

---

## Qué hace

| Módulo | Función |
|---|---|
| 1. Necesito ayuda | Registro público de necesidades, sin cuenta |
| 2. Quiero ayudar | Registro público de ofertas de ayuda, sin cuenta |
| 3. Coincidencias | Empareja automáticamente necesidades con ofertas |
| 4. Mapa | Muestra todo en un mapa Leaflet con filtros |
| 5. Puntos de ayuda | Lugares comunitarios que están ayudando |
| 6. Reportes | Situaciones reportadas por la comunidad |
| 7. Información oficial | Enlaces a fuentes oficiales (solo los agrega el admin) |
| Panel | Dashboard para cerrar casos y retirar contenido falso |

---

## Decisiones de diseño

**Nadie se registra.** El público publica sin crear cuenta, sin contraseña y sin
verificar correo. En una emergencia cada paso extra entre la persona y la
publicación cuesta ayuda que no llega.

**Un solo usuario: el administrador.** El superusuario de Django. No hay sistema
de roles porque con un solo rol no hay nada que rolificar.

**Publicación inmediata.** No hay moderación previa. El contenido aparece al
instante y el administrador puede retirarlo después. Es la decisión correcta
para una emergencia, con el costo de que puede aparecer contenido falso.

**El administrador cierra los casos manualmente.** Cuando ves que una solicitud
ya recibió ayuda, la cierras desde el panel. No hay autocierre ni códigos: como
nadie tiene cuenta, nadie más puede cerrar su propia publicación.

**Los contactos son públicos.** Teléfono y correo se muestran en el sitio y en
el mapa, siempre acompañados del aviso de verificación. Es lo que hace que la
plataforma funcione, y por eso todos los formularios advierten que esos datos
serán visibles.

**Sin edición pública.** El visitante crea un registro y termina ahí. Esto
elimina por construcción la posibilidad de que alguien modifique registros
ajenos: no hace falta comprobar propiedad porque no existe ninguna ruta de
edición pública.

---

## Tecnologías

- Python 3.11+ (probado en 3.13.3)
- Django 5.1
- MySQL 8 (con **fallback automático a SQLite** si no lo configuras)
- Bootstrap 5.3 · Leaflet 1.9 + OpenStreetMap · Chart.js 4.4
- Pillow (imágenes) · python-dotenv (configuración)

---

## Instalación paso a paso

### 1. Entra a la carpeta del proyecto

```bash
cd c:\Users\lorena\Desktop\colombia
```

### 2. Crea y activa un entorno virtual

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

Si `mysqlclient` falla al instalar y todavía no vas a usar MySQL, puedes
omitirlo por ahora:

```bash
pip install Django==5.1.4 Pillow python-dotenv
```

### 4. Crea el archivo de configuración

```powershell
Copy-Item .env.example .env
```

Ábrelo y cambia `SECRET_KEY` por una cadena larga y aleatoria. **Deja
`DB_ENGINE` vacío** para arrancar con SQLite sin instalar nada más.

### 5. Crea las tablas

```bash
python manage.py migrate
```

### 6. Crea tu usuario administrador

```bash
python manage.py createsuperuser
```

Este es el **único** usuario del sistema. Guarda bien la contraseña.

### 7. Arranca el servidor

```bash
python manage.py runserver
```

Abre **http://127.0.0.1:8000/**
El panel está en **http://127.0.0.1:8000/panel/**

La plataforma arranca **vacía**: todo lo que aparezca será contenido real
publicado por personas. No hay datos de ejemplo ni casos inventados.

Si en algún momento necesitas volver a dejarla vacía:

```bash
python manage.py limpiar_datos
```

Borra todas las publicaciones y sus fotos. Pide confirmación escribiendo
`BORRAR` y **no se puede deshacer**. No toca tu usuario ni los enlaces de
información oficial.

---

## Seguridad

La plataforma publica contenido sin registro, así que la superficie de ataque
es amplia. Estas son las capas activas.

### Lo que trae Django de serie

| Ataque | Protección |
|---|---|
| Inyección SQL | El ORM parametriza todas las consultas. Nunca se concatena SQL a mano. |
| XSS en plantillas | Escapado automático de todo lo que se renderiza. No se usa `\|safe` sobre entrada de usuario. |
| CSRF | Token obligatorio en todos los formularios. |
| Contraseñas | Hash PBKDF2 con sal. Nunca se guardan en claro. |

### Lo que se añadió encima

**Cabeceras HTTP** (en `core/middleware.py`):

- `Content-Security-Policy` — aunque alguien lograra inyectar un `<script>`,
  el navegador se niega a ejecutarlo. Solo se permiten scripts de este sitio,
  jsDelivr y unpkg.
- `X-Frame-Options: DENY` y `frame-ancestors 'none'` — nadie puede meter el
  sitio dentro de un iframe para engañar a la gente (clickjacking).
- `X-Content-Type-Options: nosniff` — el navegador no adivina tipos de archivo.
- `Referrer-Policy` — no se filtra a sitios externos qué publicación se estaba viendo.
- `Permissions-Policy` — se deniegan micrófono, pagos y USB.

**Contra bots y spam:**

- **Campo trampa (honeypot)** en los cuatro formularios. Es invisible para las
  personas; los bots lo rellenan y el envío se descarta.
- **Límite por IP**: máximo 15 publicaciones por hora desde una misma conexión
  (`MAX_PUBLICACIONES_POR_HORA`). Leer el sitio nunca se limita.

**Contra contenido malicioso:**

- Se rechaza texto con `<script>`, `<iframe>`, `javascript:` o manejadores
  como `onerror=`.
- Límite de 3000 caracteres por campo y eliminación de caracteres de control.
- **Imágenes**: se verifica el contenido real con Pillow, no solo la extensión.
  Un `.exe` renombrado a `.jpg` se rechaza. Los SVG no se aceptan (pueden
  contener JavaScript). Límite de 5 MB y de 12000 px por lado, para evitar
  imágenes que revientan la memoria del servidor.

**Sesiones y acceso:**

- La sesión del administrador caduca a las 8 horas y al cerrar el navegador.
- Cookies `HttpOnly` y `SameSite=Lax`.
- Con `DEBUG=False` se activan solos: HTTPS obligatorio, cookies seguras y
  HSTS por un año.
- El panel y el admin rechazan a cualquiera sin sesión de administrador.

**Registro:** los intentos de CSRF, hosts inválidos y errores de servidor
quedan en `seguridad.log`, con rotación automática.

### Lo que la plataforma NO puede evitar

Conviene tenerlo claro:

- **Contenido falso publicado por personas.** No hay moderación previa. Tu
  única defensa es el botón 🚫 Bloquear del panel, y funciona cuando estás
  mirando.
- **Que alguien copie los teléfonos publicados.** Son públicos por diseño; es
  lo que hace funcionar la plataforma. Los formularios lo advierten antes de
  publicar.
- **Un ataque de denegación de servicio a gran escala.** Eso se mitiga en el
  servidor o con un servicio como Cloudflare, no en el código.

---

## Configurar MySQL

Cuando quieras pasar de SQLite a MySQL:

### 1. Crea la base de datos

```sql
CREATE DATABASE ayuda_colombia
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'ayuda_user'@'localhost' IDENTIFIED BY 'tu-contraseña-segura';
GRANT ALL PRIVILEGES ON ayuda_colombia.* TO 'ayuda_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Edita tu `.env`

```env
DB_ENGINE=mysql
DB_NAME=ayuda_colombia
DB_USER=ayuda_user
DB_PASSWORD=tu-contraseña-segura
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 3. Instala el conector y migra

```bash
pip install mysqlclient
python manage.py migrate
python manage.py createsuperuser
```

Si `mysqlclient` no compila en Windows, la alternativa es
`pip install pymysql` y añadir al inicio de `config/__init__.py`:

```python
import pymysql
pymysql.install_as_MySQLdb()
```

---

## Estructura del proyecto

```
colombia/
├── manage.py
├── requirements.txt
├── .env.example              → cópialo como .env
│
├── config/                   Configuración del proyecto
│   ├── settings.py           MySQL con fallback a SQLite
│   ├── urls.py
│   ├── wsgi.py  asgi.py
│
├── core/                     Base compartida
│   ├── models.py             RegistroComunitario, UbicacionMixin, ContactoMixin
│   ├── choices.py            Catálogos de tipos, estados y urgencias
│   ├── forms.py              FormularioBase, ContactoObligatorioMixin
│   ├── utils.py              normalizar(), validar_imagen(), obtener_ip()
│   ├── admin.py              Acciones cerrar / bloquear / reactivar
│   ├── views.py  urls.py
│   ├── templatetags/ayuda_extras.py
│   └── management/commands/limpiar_datos.py
│
├── solicitudes/              Módulo 1
├── ayudas/                   Módulo 2
├── coincidencias/            Módulo 3
│   ├── services.py           Motor de emparejamiento
│   ├── signals.py            Recalcula al guardar
│   └── management/commands/recalcular_coincidencias.py
├── mapa/                     Módulo 4
│   ├── serializers.py        Registros → marcadores JSON
│   └── views.py              Vista + endpoint /mapa/api/marcadores/
├── puntos/                   Módulo 5
├── reportes/                 Módulo 6
├── informacion/              Módulo 7
├── panel/                    Dashboard del administrador
│
├── templates/
│   ├── base.html             Advertencia legal en todas las páginas
│   ├── parciales/            aviso_verificacion, selector_mapa, campo
│   └── [una carpeta por app]
│
├── static/
│   ├── css/estilos.css
│   └── js/                   mapa.js, selector-mapa.js, mapa-detalle.js, panel.js
│
└── media/                    Fotos subidas por los usuarios
```

---

## Base de datos

### Modelos y relaciones

```
SolicitudAyuda ──┐
                 ├──< Coincidencia >── OfertaAyuda
                 │    (unique: solicitud + ayuda)
PuntoAyuda           ReporteComunitario      InformacionOficial
```

**Campos heredados por todo el contenido comunitario** (`RegistroComunitario`):
`estado` (indexado), `creado` (indexado), `actualizado`, `ip_origen`, `nota_admin`.

**Campos de ubicación** (`UbicacionMixin`): `ciudad` (indexado), `zona`,
`latitud`, `longitud` (índice compuesto).

**Campos de contacto** (`ContactoMixin`): `contacto_telefono`, `contacto_email`.

### Estados

| Estado | Quién lo pone | Efecto |
|---|---|---|
| `ACTIVA` | Automático al publicar | Visible en el sitio y en el mapa |
| `RESUELTA` | El administrador | Se marca como atendido, sale del listado por defecto |
| `BLOQUEADA` | El administrador | Desaparece del sitio público; ni por URL directa |

En los reportes, `ACTIVA` se muestra como 🟡 **Reportado** y `RESUELTA` como
⚫ **Cerrado**.

### Cómo funciona el motor de coincidencias

En `coincidencias/services.py`. Al guardar una solicitud o una oferta, una señal
`post_save` busca emparejamientos:

- Mismo `tipo_ayuda`, **y**
- Misma ciudad (comparada sin tildes ni mayúsculas), **y**
- Ambas en estado `ACTIVA`

**Score 100** si además coincide la zona · **Score 70** si solo coincide la ciudad.

Los emparejamientos se presentan siempre como *"posible coincidencia"*, nunca
como algo confirmado.

---

## Comandos útiles

```bash
python manage.py runserver              # Arrancar el sitio
python manage.py createsuperuser        # Crear el administrador
python manage.py migrate                # Aplicar cambios de la base de datos
python manage.py makemigrations         # Generar migraciones tras editar modelos
python manage.py test                   # Correr los 70 tests
python manage.py limpiar_datos          # Vaciar la plataforma (irreversible)
python manage.py recalcular_coincidencias   # Recalcular emparejamientos
python manage.py collectstatic          # Preparar estáticos para producción
```

---

## Antes de lanzarla al público

### Ya está hecho ✅

- **Administrador propio creado.** El usuario provisional `admin` fue eliminado.
- **`SECRET_KEY` generada** y guardada en `.env` (única de esta instalación).
- **`DEBUG=False`** configurado.
- **Archivos estáticos recolectados** en `staticfiles/`.
- **`check --deploy` sin ningún aviso.**
- **La plataforma está vacía** de datos de prueba.

### Falta un solo paso 👇

**Escribe tu dominio en el archivo `.env`.** No pude hacerlo por ti porque no
sé dónde vas a publicar el sitio.

Abre `.env` y cambia esta línea:

```env
ALLOWED_HOSTS=localhost,127.0.0.1
```

Por tu dominio real, sin `http://` y separado por comas:

```env
ALLOWED_HOSTS=estamoscontigo.co,www.estamoscontigo.co
```

Y en el mismo archivo, cambia:

```env
MODO_LOCAL=False
```

Eso es todo. Con esos dos valores el sitio queda listo para producción.

### Ver el sitio en tu computador

Con `DEBUG=False` el sitio obliga a usar HTTPS, y en tu computador no hay
certificado. Por eso existe `MODO_LOCAL=True` en el `.env`: te deja abrirlo en
`http://127.0.0.1:8000` sin bajar el resto de las protecciones.

```bash
python manage.py runserver --insecure
```

El `--insecure` hace que se sirvan los archivos estáticos, que con
`DEBUG=False` normalmente los serviría el servidor web.

**Deja `MODO_LOCAL=False` al publicar.** Si se te olvida, verás un aviso en la
consola cada vez que arranque.

### Lo que necesita el servidor donde la publiques

- **HTTPS con certificado.** Casi todos los hostings lo dan gratis con
  Let's Encrypt. Sin él, las cookies seguras no funcionan.
- **Que la carpeta `media/` persista entre despliegues**, o las publicaciones
  se quedarán sin sus fotos.
- Si usas un proxy o balanceador, que envíe la cabecera
  `X-Forwarded-Proto: https` (la mayoría lo hace por defecto).

### Comprobar antes de publicar

```bash
python manage.py check --deploy   # no debe salir ningún aviso
python manage.py test             # 142 tests
```

### Una vez publicada

- Revisa `/panel/` al menos un par de veces al día: es donde cierras casos
  resueltos y retiras contenido falso.
- Agrega enlaces oficiales desde `/admin/` en cuanto las instituciones
  publiquen información sobre la emergencia.
- Vigila `seguridad.log` si sospechas que alguien está atacando el sitio.

---

## Lista de pruebas

Marca cada punto conforme lo verifiques. Son 15 bloques (A–O).

### A. Instalación

- [ ] `pip install -r requirements.txt` termina sin errores
- [ ] `python manage.py migrate` crea las tablas
- [ ] `python manage.py createsuperuser` crea tu usuario
- [ ] `python manage.py runserver` arranca sin errores
- [ ] `python manage.py test` → **70 tests OK**
- [ ] La plataforma arranca vacía: los contadores están en 0 y el mapa sin marcadores

### B. Página de inicio

- [ ] Abre http://127.0.0.1:8000/
- [ ] La **franja roja de advertencia** aparece arriba del todo
- [ ] Se ven los 5 botones grandes: 🆘 🤝 🗺️ 📍 📢
- [ ] Los 5 contadores muestran números, incluido **✅ Ayudas entregadas** en verde
- [ ] Cierra un caso desde el panel → el contador de ayudas entregadas sube en 1
- [ ] Los teléfonos de emergencia (123, 119, 132, 144, 125) son clicables
- [ ] Reduce la ventana a ancho de celular: los botones se apilan y siguen grandes

### C. Módulo 1 — Necesito ayuda

- [ ] Entra a "🆘 NECESITO AYUDA" **sin haber iniciado sesión** → el formulario abre
- [ ] Envía el formulario vacío → aparecen errores en rojo, no se crea nada
- [ ] Llena todo pero deja teléfono **y** correo vacíos → error pidiendo un contacto
- [ ] Escribe una descripción de 5 letras → error pidiendo más detalle
- [ ] Pon 0 personas afectadas → error
- [ ] Haz clic en el mapa → aparece el marcador y el texto "✅ Ubicación marcada"
- [ ] Prueba "🎯 Usar mi ubicación actual" → el mapa se centra (acepta el permiso)
- [ ] Arrastra el marcador → la ubicación se actualiza
- [ ] Envía el formulario completo → **"Tu solicitud fue registrada correctamente"**
- [ ] La solicitud aparece de inmediato en el listado, sin aprobación
- [ ] Sube una foto → se ve en la página de detalle
- [ ] Intenta subir un archivo que no sea imagen → lo rechaza

### D. Módulo 2 — Quiero ayudar

- [ ] Entra a "🤝 QUIERO AYUDAR" sin sesión → abre
- [ ] Envía sin contacto → error
- [ ] Envía completo → **"Tu oferta de ayuda fue registrada"**
- [ ] Aparece de inmediato en el listado de ayudas

### E. Módulo 3 — Coincidencias

- [ ] Publica una **necesidad** de "Alimentos" en Armenia, zona "Centro"
- [ ] Publica una **oferta** de "Alimentos" en Armenia, zona "Centro"
- [ ] En la pantalla de confirmación aparece **"🤝 Posibles coincidencias"** con **100%**
- [ ] Repite con zonas distintas (misma ciudad) → el score es **70%**
- [ ] Publica una oferta de "Agua" para una necesidad de "Alimentos" → **no** coincide
- [ ] Publica en ciudades distintas → **no** coincide
- [ ] Prueba con tildes: "Medellín" y "MEDELLIN" → **sí** coinciden
- [ ] Entra al detalle de la necesidad → la coincidencia aparece en la barra lateral

### F. Módulo 4 — Mapa

- [ ] Abre 🗺️ VER MAPA → carga con los marcadores
- [ ] Marcadores 🔴 rojos = urgencia alta, 🟠 media, 🟢 baja
- [ ] Marcadores 🔵 azules = ayudas, 🟣 morados = puntos, 🟡 amarillos = reportes
- [ ] Haz clic en un marcador → el popup muestra tipo, ciudad, zona, descripción,
      personas, estado **y el teléfono/correo**
- [ ] El popup incluye el aviso "🔎 Información de la comunidad, sin verificar"
- [ ] "Ver todos los detalles" lleva a la ficha completa
- [ ] Desmarca "Necesidades" → los marcadores rojos desaparecen
- [ ] Filtra por urgencia "Alta" → solo quedan los urgentes
- [ ] Filtra por tipo de ayuda → se reduce el conjunto
- [ ] Escribe "Armenia" en ciudad → solo quedan los de Armenia
- [ ] Cambia estado a "Resueltos" → cambia el conjunto
- [ ] "Limpiar filtros" restaura todo
- [ ] El contador de arriba a la izquierda coincide con lo que ves
- [ ] En celular: el botón "☰ Filtros" abre y cierra el panel

### G. Módulo 5 — Puntos de ayuda

- [ ] Registra un punto sin iniciar sesión → funciona
- [ ] El punto aparece con la etiqueta **"Sin verificar"**
- [ ] En su ficha dice **"Información proporcionada por la comunidad"**
- [ ] Desde el panel, márcalo como verificado → ahora muestra **"✅ Verificado"**
- [ ] Marca un punto como "Cerrado" desde el admin → se ve atenuado con el aviso
- [ ] El filtro "Solo verificados ✅" funciona

### H. Módulo 6 — Reportes comunitarios

- [ ] Publica un reporte **dejando el nombre vacío** → se guarda como "Anónimo"
- [ ] Cada reporte muestra **"Reporte realizado por un usuario de la comunidad"**
- [ ] Estado 🟡 Reportado por defecto
- [ ] Ciérralo desde el panel → pasa a ⚫ Cerrado
- [ ] El detalle incluye el botón grande "📞 Llamar al 123"

### I. Módulo 7 — Información oficial

- [ ] Abre 📢 INFORMACIÓN OFICIAL → se ven las líneas de emergencia
- [ ] Aparece el aviso "Consulta siempre fuentes oficiales"
- [ ] **No existe** un formulario público para agregar información oficial
- [ ] Desde `/admin/` agrega una entrada con URL → aparece en el listado
- [ ] El botón "Ir a la fuente oficial ↗" abre en pestaña nueva
- [ ] Desmarca "publicada" → desaparece del sitio público

### J. Panel de administración

- [ ] Sin sesión, entra a `/panel/` → **te redirige al login** (no entra)
- [ ] Inicia sesión con tu superusuario → el panel carga
- [ ] Las 6 métricas muestran números coherentes
- [ ] Los 3 gráficos se dibujan (tipos, urgencia, últimos 7 días)
- [ ] Pulsa **"✅ Cerrar"** en una solicitud → cambia a RESUELTA y sale del listado público
- [ ] Pulsa **"🚫 Bloquear"** → desaparece del sitio público
- [ ] Copia la URL de un registro bloqueado y ábrela sin sesión → **404**
- [ ] Pulsa "↩️ Reactivar" en la bandeja de moderación → vuelve a aparecer
- [ ] La bandeja de moderación filtra por tipo, estado y ciudad
- [ ] "✅ Verificar" en un punto de ayuda funciona

### K. Fotos en las publicaciones

Las cuatro secciones aceptan una foto opcional.

- [ ] Publica un **reporte** con una foto tomada desde el celular → se sube
- [ ] La foto aparece en el detalle del reporte
- [ ] La foto aparece como miniatura en el listado de reportes
- [ ] La foto aparece en el popup del mapa al hacer clic en su marcador
- [ ] Haz clic en la miniatura del listado → te lleva al detalle
- [ ] Repite con una **necesidad**, una **oferta de ayuda** y un **punto de ayuda**
- [ ] Publica **sin** foto → funciona igual, la publicación se crea normal
- [ ] Las tarjetas con y sin foto se ven alineadas en el listado
- [ ] Intenta subir un archivo que no sea imagen (renombra un `.txt` a `.jpg`)
      → lo rechaza con un mensaje claro
- [ ] Intenta subir una foto de más de 5 MB → la rechaza diciendo que pesa demasiado
- [ ] Desde `/admin/`, abre la publicación → ves la vista previa de la foto
      para poder revisarla antes de decidir si la bloqueas

### L. Contacto directo, difusión y anti-estafa

- [ ] En el **listado** de necesidades, cada tarjeta activa muestra los botones
      **📞 Llamar**, **💬 WhatsApp** y **✉️ Correo** sin tener que entrar al detalle
- [ ] Lo mismo en el listado de ayudas ("Pídele esta ayuda a...")
- [ ] Pulsa **💬 WhatsApp** → abre el chat con ese número, ya formateado
- [ ] Publica una necesidad con el teléfono escrito como `300 123 4567`
      (con espacios) → el enlace de WhatsApp funciona igual
- [ ] Prueba también con `+57 300-123-4567` y `(300) 1234567` → todos funcionan
- [ ] Publica dejando solo el correo, sin teléfono → **no** aparece el botón de WhatsApp
- [ ] En el detalle de una publicación, pulsa **💬 Compartir por WhatsApp**
      → se abre WhatsApp con el mensaje armado y el enlace a la publicación
- [ ] Verifica que el enlace compartido abre la publicación correcta
- [ ] Compartir funciona también en ayudas, puntos de ayuda y reportes
- [ ] La advertencia **🚫 Nunca envíes dinero** aparece en:
      - [ ] los listados (junto al aviso de verificación)
      - [ ] las páginas de detalle
      - [ ] los popups del mapa que muestran contacto
      - [ ] el aviso legal, en un bloque rojo destacado
- [ ] Los casos ya cerrados (RESUELTA) **no** muestran botones de contacto rápido

### M. Seguridad

- [ ] En un formulario, escribe en la descripción:
      `<script>alert('hola')</script> necesito ayuda urgente`
      → al ver la publicación, el texto se muestra **tal cual**, la alerta **no** salta
- [ ] Sin iniciar sesión, intenta `POST` a `/panel/estado/solicitud/1/`
      → el estado **no** cambia
- [ ] Crea un usuario normal en `/admin/` (sin marcar "staff") e inicia sesión con él
      → **no** puede entrar al panel
- [ ] Abre un formulario, borra el campo `csrfmiddlewaretoken` con las herramientas
      del navegador y envía → **error 403**
- [ ] Sube una imagen de más de 5 MB → la rechaza
- [ ] `/mapa/api/marcadores/` **no** devuelve `ip_origen` ni `nota_admin`

### N. Responsive y accesibilidad

- [ ] Prueba en celular real o con F12 → modo dispositivo
- [ ] Los botones se pueden tocar cómodamente con el pulgar
- [ ] Ninguna página se desborda horizontalmente
- [ ] Navega solo con la tecla Tab → el foco se ve claramente
- [ ] El texto se lee bien (contraste suficiente)

### O. Antes de publicar en internet

- [ ] `DEBUG=False` en el `.env`
- [ ] `SECRET_KEY` cambiada por una larga y aleatoria
- [ ] `ALLOWED_HOSTS` con tu dominio real
- [ ] Si hiciste pruebas, vacía la plataforma: `python manage.py limpiar_datos`
- [ ] `python manage.py collectstatic`
- [ ] Servidor con HTTPS (los ajustes de seguridad se activan solos con DEBUG=False)
- [ ] Contraseña fuerte para el superusuario

---

## Aviso importante

Esta plataforma publica información sin verificar, aportada por la comunidad.
Todas las páginas lo advierten, pero conviene repetirlo:

- **No sustituye a los organismos oficiales de emergencia.**
- Nadie la vigila las 24 horas.
- Los datos de contacto son públicos y pueden ser usados por cualquiera.
- Antes de entregar o recibir ayuda, verifica por teléfono, prefiere lugares
  públicos y, si puedes, no vayas solo.

**Ante una emergencia: 123.**
