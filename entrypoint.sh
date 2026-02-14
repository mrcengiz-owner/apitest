#!/bin/bash
set -e

echo "=== Running Migrations ==="
python manage.py migrate --noinput

echo "=== Creating Superuser (if not exists) ==="
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
    User.objects.create_superuser(
        username='${DJANGO_SUPERUSER_USERNAME:-admin}',
        email='${DJANGO_SUPERUSER_EMAIL:-admin@nexkasa.com}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin123}'
    )
    print('Superuser created.')
else:
    print('Superuser already exists. Skipping.')
"

echo "=== Collecting Static Files ==="
python manage.py collectstatic --noinput

echo "=== Starting Gunicorn ==="
exec gunicorn --bind 0.0.0.0:${PORT:-8000} nexkasa_debug.wsgi:application
