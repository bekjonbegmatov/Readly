#!/bin/sh
set -e

# Apply migrations and collect static assets
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Gunicorn
exec gunicorn server.wsgi:application --bind 0.0.0.0:8000 --workers 3

