/**
 * Mini mapa de las paginas de detalle.
 *
 * Muestra un unico marcador en la ubicacion del registro. No permite editar.
 */
(function () {
  "use strict";

  var contenedor = document.getElementById("mapaDetalle");
  if (!contenedor) {
    return;
  }

  var lat = parseFloat(contenedor.dataset.lat);
  var lng = parseFloat(contenedor.dataset.lng);
  if (isNaN(lat) || isNaN(lng)) {
    return;
  }

  var mapa = L.map("mapaDetalle", {
    scrollWheelZoom: false,
  }).setView([lat, lng], 16);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; colaboradores de <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mapa);

  var marcador = L.marker([lat, lng]).addTo(mapa);

  // El titulo llega ya escapado por escapejs desde la plantilla, y aqui se
  // inserta como texto en el popup, no como HTML.
  var titulo = contenedor.dataset.titulo;
  if (titulo) {
    marcador.bindPopup(document.createTextNode(titulo).textContent);
  }

  setTimeout(function () {
    mapa.invalidateSize();
  }, 300);
})();
