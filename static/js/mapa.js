/**
 * Mapa principal de AYUDA COLOMBIA.
 *
 * Carga los marcadores desde /mapa/api/marcadores/ y los dibuja con Leaflet
 * sobre OpenStreetMap.
 *
 * Nota de seguridad: los popups se construyen con createElement y textContent,
 * nunca con innerHTML sobre datos del servidor. Los textos los escribe el
 * publico sin moderacion previa, asi que insertarlos como HTML permitiria XSS.
 */
(function () {
  "use strict";

  var contenedor = document.getElementById("mapaPrincipal");
  if (!contenedor) {
    return;
  }

  var URL_MARCADORES = contenedor.dataset.urlMarcadores;

  var COLORES = {
    solicitud: { ALTA: "#e63946", MEDIA: "#f4a261", BAJA: "#2a9d8f" },
    ayuda: "#1d6fb8",
    punto: "#7b4397",
    reporte: "#e9c46a",
  };

  var mapa = L.map("mapaPrincipal").setView(
    [parseFloat(contenedor.dataset.lat), parseFloat(contenedor.dataset.lng)],
    parseInt(contenedor.dataset.zoom, 10)
  );

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; colaboradores de <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mapa);

  var grupo = L.markerClusterGroup({
    maxClusterRadius: 45,
    spiderfyOnMaxZoom: true,
  });
  mapa.addLayer(grupo);

  /** Devuelve el color que corresponde a un marcador. */
  function colorDe(dato) {
    if (dato.categoria === "solicitud") {
      return COLORES.solicitud[dato.urgencia] || COLORES.solicitud.MEDIA;
    }
    return COLORES[dato.categoria] || "#666666";
  }

  /** Crea el icono circular con el emoji del tipo. */
  function iconoDe(dato) {
    var color = colorDe(dato);
    return L.divIcon({
      className: "marcador-personalizado",
      html:
        '<div class="marcador-circulo" style="background:' +
        color +
        '"><span>' +
        // El emoji viene de un catalogo fijo del servidor, no de texto libre.
        dato.icono +
        "</span></div>",
      iconSize: [36, 36],
      iconAnchor: [18, 18],
      popupAnchor: [0, -18],
    });
  }

  /** Crea un elemento con texto plano. Nunca interpreta HTML. */
  function crear(etiqueta, texto, clase) {
    var el = document.createElement(etiqueta);
    if (texto !== undefined && texto !== null && texto !== "") {
      el.textContent = texto;
    }
    if (clase) {
      el.className = clase;
    }
    return el;
  }

  /** Agrega una fila "etiqueta: valor" al popup si el valor existe. */
  function agregarDato(padre, etiqueta, valor) {
    if (!valor && valor !== 0) {
      return;
    }
    var fila = crear("p", null, "popup-dato");
    fila.appendChild(crear("strong", etiqueta + ": "));
    fila.appendChild(document.createTextNode(String(valor)));
    padre.appendChild(fila);
  }

  /** Construye el contenido del popup de un marcador. */
  function construirPopup(dato) {
    var caja = crear("div", null, "popup-mapa popup-" + dato.categoria);

    var etiquetas = {
      solicitud: "🆘 Necesidad",
      ayuda: "🤝 Ayuda disponible",
      punto: "📍 Punto de ayuda",
      reporte: "📢 Reporte comunitario",
    };
    caja.appendChild(crear("span", etiquetas[dato.categoria], "popup-categoria"));
    caja.appendChild(crear("h3", dato.titulo, "popup-titulo"));

    // La foto la sube el publico. Se inserta como src de una imagen, nunca
    // como HTML, y la URL siempre la genera Django desde MEDIA_URL.
    if (dato.foto) {
      var img = document.createElement("img");
      img.src = dato.foto;
      img.alt = "Foto de la publicación";
      img.className = "popup-foto";
      img.loading = "lazy";
      caja.appendChild(img);
    }

    agregarDato(caja, "Ciudad", dato.ciudad);
    agregarDato(caja, "Zona", dato.zona);

    if (dato.categoria === "solicitud") {
      agregarDato(caja, "Urgencia", dato.urgencia_texto);
      agregarDato(caja, "Personas afectadas", dato.personas);
      agregarDato(caja, "Publicado por", dato.alias);
    } else if (dato.categoria === "ayuda") {
      agregarDato(caja, "Cantidad", dato.cantidad);
      agregarDato(caja, "Disponibilidad", dato.disponibilidad);
      agregarDato(caja, "Ofrecido por", dato.alias);
    } else if (dato.categoria === "punto") {
      agregarDato(caja, "Tipo", dato.tipo_texto);
      agregarDato(caja, "Dirección", dato.direccion);
      agregarDato(caja, "Horario", dato.horario);
      agregarDato(caja, "Estado del punto", dato.disponibilidad);
      agregarDato(caja, "Fuente", dato.fuente);

      if (dato.recibe && dato.recibe.length) {
        var bloqueRecibe = crear("div", null, "popup-recibe");
        bloqueRecibe.appendChild(crear("strong", "Recibe: "));
        bloqueRecibe.appendChild(
          document.createTextNode(dato.recibe.join(", "))
        );
        caja.appendChild(bloqueRecibe);
      }
    } else if (dato.categoria === "reporte") {
      agregarDato(caja, "Urgencia", dato.urgencia_texto);
      agregarDato(caja, "Reportado por", dato.reportado_por);
    }

    agregarDato(caja, "Estado", dato.estado_texto);
    agregarDato(caja, "Publicado", dato.creado);

    if (dato.descripcion) {
      var desc = crear("p", dato.descripcion, "popup-descripcion");
      caja.appendChild(desc);
    }

    // Contacto
    var tieneContacto = dato.telefono || dato.email || dato.contacto;
    if (tieneContacto) {
      var bloque = crear("div", null, "popup-contacto");
      bloque.appendChild(crear("strong", "Contacto"));

      if (dato.telefono) {
        var tel = document.createElement("a");
        tel.href = "tel:" + dato.telefono;
        tel.className = "popup-enlace popup-telefono";
        tel.textContent = "📞 " + dato.telefono;
        bloque.appendChild(tel);
      }
      if (dato.email) {
        var mail = document.createElement("a");
        mail.href = "mailto:" + dato.email;
        mail.className = "popup-enlace";
        mail.textContent = "✉️ " + dato.email;
        bloque.appendChild(mail);
      }
      if (dato.contacto) {
        bloque.appendChild(crear("p", dato.contacto, "popup-dato"));
      }
      caja.appendChild(bloque);
    }

    if (dato.categoria === "punto" && dato.verificado) {
      caja.appendChild(crear("p", "✅ Verificado por la administración", "popup-verificado"));
    } else {
      caja.appendChild(
        crear("p", "🔎 Información de la comunidad, sin verificar. Confirma antes de ir.", "popup-aviso")
      );
    }

    if (tieneContacto) {
      caja.appendChild(
        crear("p", "🚫 Nunca envíes dinero ni des claves bancarias.", "popup-dinero")
      );
    }

    // Quien mira el mapa suele estar decidiendo a donde ir: el boton de
    // "como llegar" va junto al de detalles.
    if (dato.url_como_llegar) {
      var comoLlegar = document.createElement("a");
      comoLlegar.href = dato.url_como_llegar;
      comoLlegar.target = "_blank";
      comoLlegar.rel = "noopener noreferrer";
      comoLlegar.className = "popup-boton popup-boton-llegar";
      comoLlegar.textContent = "📍 Cómo llegar";
      caja.appendChild(comoLlegar);
    }

    var enlace = document.createElement("a");
    enlace.href = dato.url;
    enlace.className = "popup-boton";
    enlace.textContent = "Ver todos los detalles";
    caja.appendChild(enlace);

    return caja;
  }

  // Zona seleccionada con los botones de acceso rapido. Vacio = todo el pais.
  var zonaActiva = "";

  /** Lee el estado actual de los filtros de la barra lateral. */
  function leerFiltros() {
    var categorias = [];
    document.querySelectorAll(".filtro-categoria:checked").forEach(function (c) {
      categorias.push(c.value);
    });

    return {
      categorias: categorias.join(","),
      urgencia: document.getElementById("filtroUrgencia").value,
      tipo: document.getElementById("filtroTipo").value,
      ciudad: document.getElementById("filtroCiudad").value.trim(),
      zona: zonaActiva,
      estado: document.getElementById("filtroEstado").value,
    };
  }

  var cargando = document.getElementById("cargandoMapa");
  var contador = document.getElementById("contadorMarcadores");

  // Cuando el usuario elige una zona, el mapa ya quedo donde el quiso: no hay
  // que reencuadrarlo sobre los marcadores.
  var respetarVista = false;

  /** Pide los marcadores al servidor y los dibuja. */
  function cargarMarcadores() {
    var filtros = leerFiltros();

    // Si el usuario desmarca todas las categorias, no hay nada que pedir.
    if (!filtros.categorias) {
      grupo.clearLayers();
      contador.textContent = "0";
      cargando.style.display = "none";
      return;
    }

    cargando.style.display = "block";
    cargando.textContent = "Cargando ubicaciones…";

    var parametros = new URLSearchParams(filtros);

    fetch(URL_MARCADORES + "?" + parametros.toString(), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (respuesta) {
        if (!respuesta.ok) {
          throw new Error("Respuesta " + respuesta.status);
        }
        return respuesta.json();
      })
      .then(function (datos) {
        grupo.clearLayers();

        var marcadores = [];
        datos.marcadores.forEach(function (dato) {
          var marcador = L.marker([dato.lat, dato.lng], { icon: iconoDe(dato) });
          marcador.bindPopup(construirPopup(dato), { maxWidth: 320, minWidth: 240 });
          marcadores.push(marcador);
        });

        grupo.addLayers(marcadores);
        contador.textContent = datos.total;

        if (marcadores.length > 0) {
          if (!respetarVista) {
            mapa.fitBounds(grupo.getBounds(), { padding: [40, 40], maxZoom: 15 });
          }
          cargando.style.display = "none";
        } else {
          cargando.textContent =
            "Todavía no hay publicaciones en esta zona con estos filtros.";
        }
        respetarVista = false;
      })
      .catch(function () {
        cargando.textContent =
          "No se pudieron cargar las ubicaciones. Revisa tu conexión e intenta de nuevo.";
      });
  }

  // --- Eventos de los filtros ---

  document.querySelectorAll(".filtro-categoria").forEach(function (check) {
    check.addEventListener("change", cargarMarcadores);
  });
  ["filtroUrgencia", "filtroTipo", "filtroEstado"].forEach(function (id) {
    document.getElementById(id).addEventListener("change", cargarMarcadores);
  });

  // La ciudad se escribe: esperamos a que el usuario deje de teclear.
  var temporizador = null;
  document.getElementById("filtroCiudad").addEventListener("input", function () {
    // Buscar una ciudad a mano sustituye a la zona elegida con los botones.
    if (this.value.trim()) {
      zonaActiva = "";
      document.querySelectorAll(".zona-boton").forEach(function (b) {
        b.classList.remove("zona-activa");
      });
    }
    clearTimeout(temporizador);
    temporizador = setTimeout(cargarMarcadores, 400);
  });

  document.getElementById("btnLimpiarFiltros").addEventListener("click", function () {
    document.querySelectorAll(".filtro-categoria").forEach(function (c) {
      c.checked = true;
    });
    document.getElementById("filtroUrgencia").value = "";
    document.getElementById("filtroTipo").value = "";
    document.getElementById("filtroCiudad").value = "";
    document.getElementById("filtroEstado").value = "ACTIVA";
    zonaActiva = "";
    document.querySelectorAll(".zona-boton").forEach(function (b) {
      b.classList.remove("zona-activa");
    });
    cargarMarcadores();
  });

  // Accesos rapidos a las zonas con mas actividad.
  document.querySelectorAll(".zona-boton").forEach(function (boton) {
    boton.addEventListener("click", function () {
      var campoCiudad = document.getElementById("filtroCiudad");

      if (boton.dataset.todas) {
        // Volver a la vista nacional: se quitan los filtros de lugar.
        zonaActiva = "";
        campoCiudad.value = "";
        mapa.setView(
          [parseFloat(contenedor.dataset.lat), parseFloat(contenedor.dataset.lng)],
          parseInt(contenedor.dataset.zoom, 10)
        );
      } else {
        // La zona filtra por todos sus municipios, asi que el campo de ciudad
        // se limpia para no restringir de mas.
        zonaActiva = boton.dataset.nombre;
        campoCiudad.value = "";
        mapa.setView(
          [parseFloat(boton.dataset.lat), parseFloat(boton.dataset.lng)],
          parseInt(boton.dataset.zoom, 10)
        );
      }

      document.querySelectorAll(".zona-boton").forEach(function (b) {
        b.classList.toggle("zona-activa", b === boton && !boton.dataset.todas);
      });

      respetarVista = true;
      cargarMarcadores();
    });
  });

  document.getElementById("btnMiUbicacionMapa").addEventListener("click", function () {
    if (!navigator.geolocation) {
      alert("Tu navegador no permite obtener la ubicación.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      function (posicion) {
        mapa.setView([posicion.coords.latitude, posicion.coords.longitude], 14);
      },
      function () {
        alert(
          "No se pudo obtener tu ubicación. Revisa que le hayas dado permiso al navegador."
        );
      }
    );
  });

  // Panel de filtros en celular
  var botonFiltros = document.getElementById("btnAbrirFiltros");
  var panel = document.getElementById("panelMapa");
  if (botonFiltros && panel) {
    botonFiltros.addEventListener("click", function () {
      panel.classList.toggle("panel-abierto");
    });
  }

  cargarMarcadores();
})();
