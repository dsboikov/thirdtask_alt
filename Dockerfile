FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry
RUN pip install djangorestframework-stubs
RUN pip install django-stubs

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --without dev --verbose

COPY . .

# Сбор статики (без доступа к БД)
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
