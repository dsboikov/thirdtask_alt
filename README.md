# Учебный проект "Интернет-магазин на Django/DRF"

## Описание
Учебный проект, реализующий функционал интернет-магазина, использующий Python в качестве бэкенда, Django в качестве фрэймворка и стек html-js-css для фронтэнда.
За маршрутизацию отвечает Django.
За хранение информации о сохранённых файлах отвечает PostgreSQL

**Требования**
- Docker
- Docker-compose
- Python3.13
- Git

**Установка и запуск**

- Клонируйте репозиторий: `git clone https://github.com/dsboikov/thirdtask_alt.git`
- Установите Poetry: `pip install poetry`
- Установите зависимости: `poetry install`
- Запустите через Docker: `docker-compose up --build -d`
- Миграции: `docker-compose exec web python manage.py migrate`
- Создайте суперюзера: `docker-compose exec web python manage.py createsuperuser`
- Доступ: http://localhost:8000 (веб), /api/docs/ (Swagger), /graphql/ (GraphQL)

**JWT и API-примеры**

- Регистрация: POST /api/users/register/ {"username": "user", "password": "pass"}
- Логин: POST /api/users/login/ -> {"access": "...", "refresh": "..."}
- Пример: GET /api/products/ с header Authorization: Bearer <access_token>
- Обновление токена: POST /api/users/refresh/ {"refresh": "..."}

**Запуск тестов и линтеров**

- Тесты: `poetry run pytest`
- Линтеры: `poetry run flake8 .` и `poetry run mypy .`

**Структура проекта**

См. раздел 5 ТЗ — модульная структура с apps для products, orders и т.д.

**Чек-лист реализации**

- [x] Проект запускается через Docker Compose на чистой копии.
- [x] PostgreSQL используется.
- [x] Каталог: фильтры, поиск, пагинация.
- [x] Страница товара: детали, отзывы, добавление в корзину.
- [x] Корзина: управление, расчёт, проверка остатков.
- [x] Оформление заказа: создание, email, валидация.
- [x] Личный кабинет: регистрация, вход, история, редактирование.
- [x] REST API: JWT, документация, права.
- [x] Админка: аналитика, фильтры, управление.
- [x] Swagger/OpenAPI работает.
- [x] Типизация и докстринги.
- [x] Линтеры (flake8/mypy) без критичных ошибок.
- [x] Базовые тесты проходят.
- [x] README полон и понятен.
- [x] Коммиты осмысленные, ветки используются.
- [x] Чек-лист приложен.
- Бонусы: Poetry, GraphQL, тесты >80%.


**Роли и права**
Добавлена группа "Content Managers", которая может управлять контентом (категории, товары, отзывы), но не пользователями.
Участникам группы "Content Managers" нужно поставить is_staff=True (галочку "Статус персонала"), чтобы они могли входить в админку. Группа сама это не меняет.
Группе не даем прав на auth.user, auth.group и т.п.

**Аналитика**
Аналитика по просмотрам и заказам представлена в разделе /admin/orders/order/analytics/
Либо Заказы -> кнопка Аналитика справа сверху
