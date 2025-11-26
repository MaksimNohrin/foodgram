#!/bin/sh
# entrypoint.sh

echo "Применение миграций базы данных"
python manage.py migrate

echo "Сбор статики"
python manage.py collectstatic --noinput
cp -r /app/backend_static/. /static/static/

echo "Запуск сервера"
exec "$@"
