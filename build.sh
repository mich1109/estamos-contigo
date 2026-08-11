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

echo "==> Listo"
