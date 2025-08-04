# Базовый образ
FROM python:3.12-slim

# Обновляем pip и создаём рабочую директорию
RUN pip install --upgrade pip
WORKDIR /app

# Копируем зависимости и код
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Старт
CMD ["python3", "main.py"]

