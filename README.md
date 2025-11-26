Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

# Запуск локально
### Бэкенд
python manage.py data_import

# Настройка окружения

# API

# Тестирование

# Деплой

# Временно, для разработки
сделать дамп данных (в контейнере)
docker container exec -it foodgram-backend-1 python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --indent 2 > ./sqlite_db/data_dump.json

загрузить данные из дампа
docker container exec -it foodgram-backend-1 python manage.py loaddata ./sqlite_db/data_dump.json
