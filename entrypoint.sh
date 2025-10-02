
set -e

# variables por defecto
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-placacenter.settings}
export DJANGO_DEBUG=${DJANGO_DEBUG:-False}
export DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS:-*}

# migraciones sqlite
python manage.py migrate --noinput

# cargar seed con json
if [ "${LOAD_SEED:-false}" = "true" ] && [ -f "seed.json" ]; then
  python manage.py loaddata seed.json || true
fi

# arrancar con Gunicorn
exec gunicorn placacenter.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
