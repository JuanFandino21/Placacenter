#!/usr/bin/env bash
set -e

# Variables por defecto si no vienen del entorno
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-placacenter.settings}
export DJANGO_DEBUG=${DJANGO_DEBUG:-False}
export DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS:-*}

# Migraciones (SQLite)
python manage.py migrate --noinput

# Cargar seed si lo pides con LOAD_SEED=true y existe seed.json
if [ "${LOAD_SEED:-false}" = "true" ] && [ -f "seed.json" ]; then
  python manage.py loaddata seed.json || true
fi

# Arrancar app con Gunicorn
exec gunicorn placacenter.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
