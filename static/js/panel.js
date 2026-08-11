/**
 * Graficos del panel de administracion.
 *
 * Los datos llegan desde el servidor mediante json_script, que los serializa
 * de forma segura: no se construye JSON interpolando texto en la plantilla.
 */
(function () {
  "use strict";

  if (typeof Chart === "undefined") {
    return;
  }

  /** Lee un bloque json_script por id. Devuelve null si no existe. */
  function leerDatos(id) {
    var elemento = document.getElementById(id);
    if (!elemento) {
      return null;
    }
    try {
      return JSON.parse(elemento.textContent);
    } catch (error) {
      return null;
    }
  }

  Chart.defaults.font.family =
    "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
  Chart.defaults.plugins.legend.labels.boxWidth = 14;

  var PALETA = [
    "#e63946", "#1d6fb8", "#2a9d8f", "#f4a261",
    "#7b4397", "#e9c46a", "#457b9d", "#8d99ae",
    "#c1121f", "#588157", "#6d597a",
  ];

  // --- Necesidades por tipo de ayuda ---
  var datosTipos = leerDatos("datosTipos");
  var lienzoTipos = document.getElementById("graficoTipos");
  if (datosTipos && lienzoTipos && datosTipos.valores.length) {
    new Chart(lienzoTipos, {
      type: "doughnut",
      data: {
        labels: datosTipos.etiquetas,
        datasets: [
          {
            data: datosTipos.valores,
            backgroundColor: PALETA,
            borderWidth: 2,
            borderColor: "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { padding: 10, font: { size: 11 } } },
        },
      },
    });
  } else if (lienzoTipos) {
    lienzoTipos.parentNode.insertAdjacentHTML(
      "beforeend",
      '<p class="text-muted small text-center mt-3">Todavía no hay solicitudes activas.</p>'
    );
  }

  // --- Necesidades por urgencia ---
  var datosUrgencia = leerDatos("datosUrgencia");
  var lienzoUrgencia = document.getElementById("graficoUrgencia");
  if (datosUrgencia && lienzoUrgencia && datosUrgencia.valores.length) {
    new Chart(lienzoUrgencia, {
      type: "bar",
      data: {
        labels: datosUrgencia.etiquetas,
        datasets: [
          {
            label: "Necesidades",
            data: datosUrgencia.valores,
            backgroundColor: ["#e63946", "#f4a261", "#2a9d8f"],
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  } else if (lienzoUrgencia) {
    lienzoUrgencia.parentNode.insertAdjacentHTML(
      "beforeend",
      '<p class="text-muted small text-center mt-3">Todavía no hay solicitudes activas.</p>'
    );
  }

  // --- Actividad de los ultimos 7 dias ---
  var datosActividad = leerDatos("datosActividad");
  var lienzoActividad = document.getElementById("graficoActividad");
  if (datosActividad && lienzoActividad) {
    new Chart(lienzoActividad, {
      type: "line",
      data: {
        labels: datosActividad.etiquetas,
        datasets: [
          {
            label: "Necesidades",
            data: datosActividad.solicitudes,
            borderColor: "#e63946",
            backgroundColor: "rgba(230,57,70,0.12)",
            tension: 0.3,
            fill: true,
          },
          {
            label: "Ayudas",
            data: datosActividad.ayudas,
            borderColor: "#2a9d8f",
            backgroundColor: "rgba(42,157,143,0.12)",
            tension: 0.3,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }
})();
