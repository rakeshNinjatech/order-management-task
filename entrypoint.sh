#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create superuser if not exists
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser \
      --username "$DJANGO_SUPERUSER_USERNAME" \
      --email "$DJANGO_SUPERUSER_EMAIL" \
      --noinput || true
fi

# Start the Django development server
exec "$@"
