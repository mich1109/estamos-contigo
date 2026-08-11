# AYUDA COLOMBIA — Diseño

Fecha: 2026-08-03

## Propósito

Plataforma web comunitaria para conectar personas afectadas por un terremoto con
personas que pueden ayudarlas. No reemplaza a ningún organismo oficial de
emergencia y debe declararlo de forma visible en todas las páginas.

## Principios de diseño

1. **Cero fricción para publicar.** Nadie se registra. Nadie inicia sesión. En una
   emergencia, cada paso adicional entre la persona y la publicación cuesta ayuda
   que no llega.
2. **Un solo administrador.** El superusuario de Django. Su única función operativa
   es cerrar casos ya resueltos y retirar contenido falso.
3. **Nada se presenta como oficial.** Todo el contenido generado por visitantes se
   marca como reportado por la comunidad y sin verificar.
4. **Velocidad sobre sofisticación.** Renderizado del lado del servidor, sin SPA,
   sin API pública. Debe cargar en un celular con mala señal.

## Decisiones tomadas

| Decisión | Elección | Razón |
|---|---|---|
| Base de datos | MySQL con fallback automático a SQLite | Permite ejecutar el proyecto sin instalar MySQL; se migra cambiando `.env` |
| Moderación | Publicación inmediata, bloqueo posterior | En emergencia la velocidad importa más que el filtro previo |
| Datos de contacto | Visibles públicamente con aviso de verificación | Requisito explícito; el campo alias permite seudónimo |
| Autenticación | Solo superusuario Django | El usuario pidió que nadie más se registre |
| Cierre de casos | 100% manual desde el panel | El administrador cierra cuando ve que la ayuda llegó |

## Arquitectura

Django 5.x monolítico. Renderizado server-side con plantillas. Bootstrap 5 para
responsive. Leaflet + OpenStreetMap para el mapa. Sin framework de frontend.

### Apps

| App | Responsabilidad |
|---|---|
| `core` | Home, avisos legales, modelos abstractos, choices compartidos |
| `solicitudes` | Módulo 1 — registro de necesidades |
| `ayudas` | Módulo 2 — registro de ofertas de ayuda |
| `coincidencias` | Módulo 3 — motor de emparejamiento |
| `mapa` | Módulo 4 — vista de mapa y endpoint GeoJSON |
| `puntos` | Módulo 5 — puntos de ayuda comunitarios |
| `reportes` | Módulo 6 — reportes comunitarios de situaciones |
| `informacion` | Módulo 7 — enlaces a información oficial |
| `panel` | Dashboard del administrador |

No existe app `usuarios`. El sistema de roles se elimina: con un solo rol no hay
nada que rolificar. Django Admin provee el login.

### Modelos abstractos

`RegistroComunitario` — heredado por todos los modelos públicos:
- `creado` (DateTimeField, auto_now_add, indexado)
- `actualizado` (DateTimeField, auto_now)
- `estado` (CharField: ACTIVA / RESUELTA / BLOQUEADA, indexado)
- `ip_origen` (GenericIPAddressField, null=True) — para rastrear abuso

`UbicacionMixin` — heredado por todo lo que aparece en el mapa:
- `ciudad` (CharField, indexado)
- `zona` (CharField)
- `latitud`, `longitud` (DecimalField, index_together)

### Modelos concretos

**SolicitudAyuda** (Módulo 1)
- Hereda `RegistroComunitario` + `UbicacionMixin`
- `alias`, `personas_afectadas` (PositiveIntegerField)
- `tipo_ayuda` (choices: alimentos, agua, alojamiento, ropa, transporte,
  medicamentos, electricidad, mascotas, otro)
- `urgencia` (ALTA / MEDIA / BAJA, indexado)
- `descripcion`, `foto` (ImageField, opcional)
- `contacto_telefono`, `contacto_email` (al menos uno obligatorio)

**OfertaAyuda** (Módulo 2)
- Hereda `RegistroComunitario` + `UbicacionMixin`
- `alias`, `tipo_ayuda` (mismos choices más donaciones y mano de obra)
- `cantidad` (CharField libre: "5 mercados", "2 habitaciones")
- `descripcion`
- `disponibilidad` (INMEDIATA / HOY / PROXIMOS_DIAS)
- `contacto_telefono`, `contacto_email`

**Coincidencia** (Módulo 3)
- FK `solicitud`, FK `ayuda`, `unique_together`
- `score` (PositiveSmallIntegerField)
- `creado`
- Sin ciclo de vida propio: la coincidencia solo sugiere. El cierre ocurre sobre
  la solicitud y la oferta.

**PuntoAyuda** (Módulo 5)
- Hereda `RegistroComunitario` + `UbicacionMixin`
- `nombre`, `tipo` (acopio, alimentos, agua, refugio, donaciones, carga, otro)
- `horario`, `descripcion`, `contacto`, `fuente_informacion`
- `verificado` (BooleanField, default False) — solo el admin lo activa; mientras
  sea False la interfaz muestra "información proporcionada por la comunidad"
- `disponibilidad` (ACTIVO / NO_DISPONIBLE / CERRADO)

**ReporteComunitario** (Módulo 6)
- Hereda `RegistroComunitario` + `UbicacionMixin`
- `tipo_reporte` (daños, vía bloqueada, falta de agua, falta de alimentos,
  necesidad de alojamiento, otra)
- `descripcion`, `foto`, `urgencia`

**InformacionOficial** (Módulo 7)
- `titulo`, `descripcion`, `institucion`, `url`, `fecha`
- `categoria` (sísmica, recomendaciones, comunicados, centros de atención,
  municipal, departamental)
- Sin formulario público. Solo se crea desde Django Admin.

## Motor de coincidencias

Función pura en `coincidencias/services.py`, invocada por señal `post_save` sobre
SolicitudAyuda y OfertaAyuda.

Regla, deliberadamente simple y auditable:
- Misma ciudad (comparación normalizada, sin tildes ni mayúsculas)
- Mismo `tipo_ayuda`
- Ambas en estado ACTIVA
- Score 100 si además coincide la zona; 70 si solo coincide la ciudad

Sin aprendizaje automático, sin dependencias externas. La coincidencia se presenta
como "posible coincidencia", nunca como un emparejamiento confirmado.

## Mapa

Vista `/mapa/` con un endpoint `/mapa/api/marcadores/` que devuelve GeoJSON
filtrable por `tipo`, `urgencia`, `ciudad` y `estado`. Los registros BLOQUEADA
nunca se serializan.

Colores de marcador: rojo urgencia alta, naranja media, verde baja, azul ofertas,
morado puntos de ayuda. Agrupación con MarkerClusterGroup. Los filtros son
casillas que refiltran sin recargar la página.

Cada marcador abre un popup con tipo, ciudad, zona, descripción, número de
personas, estado, contacto y el aviso de verificación.

## Panel del administrador

Ruta `/panel/`, protegida con `staff_member_required`.

Métricas: solicitudes activas, ofertas activas, puntos de ayuda, reportes
abiertos, casos resueltos, coincidencias detectadas.

Gráficos con Chart.js: solicitudes por tipo de ayuda, solicitudes por urgencia,
publicaciones por día en la última semana.

Acciones sobre cada registro: **Cerrar caso** (pasa a RESUELTA) y **Bloquear**
(pasa a BLOQUEADA y desaparece del sitio público). Django Admin cubre la edición
detallada y el borrado.

## Seguridad

- CSRF en todos los formularios
- Escape automático de plantillas; ningún `|safe` sobre entrada de usuario
- Validación de imágenes: extensión permitida y tamaño máximo de 5 MB
- No existe edición pública de ningún registro: el visitante crea y termina ahí.
  Esto elimina por construcción la posibilidad de que alguien modifique registros
  ajenos, sin necesidad de comprobaciones de propiedad.
- `SECRET_KEY`, `DEBUG` y credenciales de base de datos leídos de `.env`

## Diseño visual

Fondo blanco y gris claro. Rojo `#E63946` reservado para urgencia y la alerta
legal. Azul `#1D3557` para navegación. Verde `#2A9D8F` para ofertas de ayuda.

Los cinco botones de la home ocupan como mínimo 120 px de alto para ser tocables
con el pulgar. La advertencia legal vive en `base.html` y por lo tanto aparece en
todas las páginas sin excepción.

## Pruebas

Tests unitarios sobre el motor de coincidencias y las validaciones de formularios.
El resto se verifica con una lista de pruebas manuales entregada al final de la
implementación.
