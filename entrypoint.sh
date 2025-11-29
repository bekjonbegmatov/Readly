#!/bin/sh
set -e

# Apply migrations and collect static assets
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Start Gunicorn (через python -m, чтобы избежать проблем с PATH)
exec python -m gunicorn server.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile - \
  --error-logfile - 
