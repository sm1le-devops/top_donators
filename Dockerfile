FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные зависимости для сборки (без distutils)
RUN apt-get update && apt-get install -y build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем Poetry файлы
COPY pyproject.toml poetry.lock ./

# Устанавливаем pip и Poetry
RUN pip install --upgrade pip \
    && pip install poetry

# Устанавливаем зависимости проекта
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Копируем проект
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
