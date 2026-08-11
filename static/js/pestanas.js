/**
 * Pestanas de la portada: "Necesitan ayuda" y "Ofrecen ayuda".
 *
 * El cambio de pestana ocurre sin recargar. Si este script no carga, el
 * servidor ya decidio cual pestana viene abierta segun el parametro ?ver=,
 * asi que la pagina sigue siendo utilizable.
 */
(function () {
  "use strict";

  var pestanas = document.querySelectorAll(".pestana");
  var campoVer = document.getElementById("campoVer");

  if (!pestanas.length) {
    return;
  }

  /** Muestra el panel indicado y marca su pestana como activa. */
  function abrir(idPanel, nombre) {
    pestanas.forEach(function (p) {
      var suya = p.dataset.panel === idPanel;
      p.classList.toggle("activa", suya);
      p.setAttribute("aria-selected", suya ? "true" : "false");
    });

    document.querySelectorAll(".panel-pestana").forEach(function (panel) {
      panel.classList.toggle("visible", panel.id === idPanel);
    });

    // Para que al filtrar se conserve la pestana abierta.
    if (campoVer) {
      campoVer.value = nombre;
    }

    // Se refleja en la URL sin recargar, para poder compartir el enlace.
    if (window.history && window.history.replaceState) {
      var url = new URL(window.location.href);
      url.searchParams.set("ver", nombre);
      window.history.replaceState({}, "", url);
    }
  }

  pestanas.forEach(function (pestana) {
    pestana.addEventListener("click", function () {
      var idPanel = pestana.dataset.panel;
      var nombre = idPanel === "panel-ayudas" ? "ayudas" : "necesidades";
      abrir(idPanel, nombre);
    });
  });

  // Navegacion con teclado entre pestanas.
  document.querySelector(".pestanas").addEventListener("keydown", function (e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") {
      return;
    }
    var lista = Array.prototype.slice.call(pestanas);
    var actual = lista.findIndex(function (p) {
      return p.classList.contains("activa");
    });
    var siguiente = e.key === "ArrowRight" ? actual + 1 : actual - 1;
    if (siguiente < 0) {
      siguiente = lista.length - 1;
    }
    if (siguiente >= lista.length) {
      siguiente = 0;
    }
    lista[siguiente].click();
    lista[siguiente].focus();
  });
})();
