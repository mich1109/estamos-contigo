/**
 * Selector de ubicacion para los formularios publicos.
 *
 * Permite marcar un punto tocando el mapa o usando la ubicacion del navegador,
 * y guarda las coordenadas en los campos ocultos latitud/longitud.
 */
(function () {
  "use strict";

  var contenedor = document.getElementById("mapaSelector");
  if (!contenedor) {
    return;
  }

  var campoLat = document.getElementById("id_latitud");
  var campoLng = document.getElementById("id_longitud");
  var estado = document.getElementById("estadoUbicacion");

  // Centro por defecto: Colombia completa.
  var centroInicial = [4.5709, -74.2973];
  var zoomInicial = 6;

  // Si el formulario ya trae coordenadas (por ejemplo tras un error de
  // validacion), arrancamos ahi para no perder lo que el usuario marco.
  var latPrevia = campoLat && campoLat.value ? parseFloat(campoLat.value) : null;
  var lngPrevia = campoLng && campoLng.value ? parseFloat(campoLng.value) : null;
  var hayPrevia = latPrevia !== null && lngPrevia !== null && !isNaN(latPrevia) && !isNaN(lngPrevia);

  if (hayPrevia) {
    centroInicial = [latPrevia, lngPrevia];
    zoomInicial = 15;
  }

  var mapa = L.map("mapaSelector").setView(centroInicial, zoomInicial);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; colaboradores de <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mapa);

  var marcador = null;

  /** Coloca el marcador y guarda las coordenadas en el formulario. */
  function marcar(lat, lng) {
    if (marcador) {
      marcador.setLatLng([lat, lng]);
    } else {
      marcador = L.marker([lat, lng], { draggable: true }).addTo(mapa);
      marcador.on("dragend", function () {
        var pos = marcador.getLatLng();
        guardar(pos.lat, pos.lng);
      });
    }
    guardar(lat, lng);
  }

  /** Escribe las coordenadas en los campos ocultos. */
  function guardar(lat, lng) {
    if (campoLat) {
      campoLat.value = lat.toFixed(6);
    }
    if (campoLng) {
      campoLng.value = lng.toFixed(6);
    }
    if (estado) {
      estado.textContent =
        "✅ Ubicación marcada. Puedes arrastrar el marcador para ajustarla.";
      estado.className = "text-success small mt-2";
    }
  }

  if (hayPrevia) {
    marcar(latPrevia, lngPrevia);
  }

  mapa.on("click", function (evento) {
    marcar(evento.latlng.lat, evento.latlng.lng);
  });

  var boton = document.getElementById("btnMiUbicacion");
  if (boton) {
    boton.addEventListener("click", function () {
      if (!navigator.geolocation) {
        if (estado) {
          estado.textContent =
            "Tu navegador no permite obtener la ubicación. Marca el punto tocando el mapa.";
          estado.className = "text-danger small mt-2";
        }
        return;
      }

      if (estado) {
        estado.textContent = "Buscando tu ubicación…";
        estado.className = "text-muted small mt-2";
      }

      navigator.geolocation.getCurrentPosition(
        function (posicion) {
          var lat = posicion.coords.latitude;
          var lng = posicion.coords.longitude;
          mapa.setView([lat, lng], 16);
          marcar(lat, lng);
        },
        function () {
          if (estado) {
            estado.textContent =
              "No se pudo obtener tu ubicación. Marca el punto tocando el mapa.";
            estado.className = "text-danger small mt-2";
          }
        }
      );
    });
  }

  // El mapa a veces se dibuja mal si el contenedor cambia de tamano al cargar.
  setTimeout(function () {
    mapa.invalidateSize();
  }, 300);
})();
