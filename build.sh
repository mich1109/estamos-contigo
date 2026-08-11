#!/usr/bin/env bash
# Pasos que Render ejecuta cada vez que publica el sitio.
#
# Si algo falla aqui, el despliegue se detiene y el sitio anterior sigue
# funcionando: no se publica una version rota.
set -o errexit

echo "==> Instalando dependencias"
pip install -r requirements.txt

echo "==> Recolectando archivos estaticos (CSS, JS, imagenes)"
python manage.py collectstatic --no-input

echo "==> Aplicando cambios de la base de datos"
python manage.py migrate

echo "==> Preparando el sitio (administrador y directorio de puntos)"
# Solo actua la primera vez: no duplica puntos ni cambia contrasenas ya
# establecidas. Necesario porque el plan gratuito de Render no da terminal.
python manage.py preparar_sitio

echo "==> Listo"
