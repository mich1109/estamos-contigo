/**
 * Selector de foto de AYUDA COLOMBIA.
 *
 * Conecta los dos botones (galeria y camara) con el campo real del formulario,
 * y muestra una vista previa de lo que la persona eligio.
 *
 * Si este script no carga, el formulario sigue siendo usable: el campo de
 * archivo original queda visible y funciona como siempre.
 */
(function () {
  "use strict";

  // Tope absoluto. Por encima de 5 MB el servidor reduce la foto solo, asi
  // que aqui solo se avisa de archivos verdaderamente enormes.
  var MAX_MB = 40;

  document.querySelectorAll("[data-selector-foto]").forEach(function (caja) {
    var campo = caja.querySelector('input[type="file"][name]');
    var camara = caja.querySelector(".entrada-camara");
    var btnGaleria = caja.querySelector(".btn-galeria");
    var btnCamara = caja.querySelector(".btn-camara");
    var previa = caja.querySelector(".selector-foto-previa");
    var imagen = previa.querySelector("img");
    var nombre = previa.querySelector(".previa-nombre");
    var btnQuitar = previa.querySelector(".btn-quitar-foto");
    var error = caja.querySelector(".selector-foto-error");

    if (!campo) {
      return;
    }

    // Con los botones puestos, el input original sobra visualmente.
    // Solo se oculta si el navegador soporta lo que necesitamos.
    var soportaDataTransfer = typeof DataTransfer !== "undefined";
    caja.classList.add("con-botones");

    function mostrarError(mensaje) {
      error.textContent = mensaje;
      error.hidden = false;
    }

    function limpiarError() {
      error.textContent = "";
      error.hidden = true;
    }

    /** Muestra la miniatura de la foto elegida. */
    function mostrarPrevia(archivo) {
      var lector = new FileReader();
      lector.onload = function (evento) {
        imagen.src = evento.target.result;
        nombre.textContent =
          archivo.name + " · " + (archivo.size / 1024 / 1024).toFixed(1) + " MB";
        previa.hidden = false;
      };
      lector.readAsDataURL(archivo);
    }

    /** Comprueba el archivo antes de enviarlo, para avisar cuanto antes. */
    function revisar(archivo) {
      limpiarError();

      if (!archivo.type || archivo.type.indexOf("image/") !== 0) {
        mostrarError(
          "Ese archivo no es una imagen. Elige una foto de tu galería."
        );
        return false;
      }

      if (archivo.size > MAX_MB * 1024 * 1024) {
        mostrarError(
          "El archivo pesa " +
            (archivo.size / 1024 / 1024).toFixed(1) +
            " MB, demasiado para subirlo. Toma la foto con la cámara normal " +
            "de tu celular."
        );
        return false;
      }

      return true;
    }

    function alElegir() {
      var archivo = campo.files && campo.files[0];
      if (!archivo) {
        previa.hidden = true;
        return;
      }
      if (revisar(archivo)) {
        mostrarPrevia(archivo);
      } else {
        campo.value = "";
        previa.hidden = true;
      }
    }

    campo.addEventListener("change", alElegir);

    // El boton de galeria abre el campo real: el sistema muestra el carrete.
    btnGaleria.addEventListener("click", function () {
      campo.click();
    });

    // El de camara abre el input auxiliar y luego copia el archivo al real.
    if (soportaDataTransfer) {
      btnCamara.addEventListener("click", function () {
        camara.click();
      });

      camara.addEventListener("change", function () {
        var archivo = camara.files && camara.files[0];
        if (!archivo) {
          return;
        }
        var transferencia = new DataTransfer();
        transferencia.items.add(archivo);
        campo.files = transferencia.files;
        alElegir();
      });
    } else {
      // Navegador viejo: sin DataTransfer no se puede copiar entre inputs.
      // Se deja un solo camino en lugar de un boton que no haria nada.
      btnCamara.hidden = true;
    }

    btnQuitar.addEventListener("click", function () {
      campo.value = "";
      camara.value = "";
      imagen.src = "";
      previa.hidden = true;
      limpiarError();
    });
  });
})();
