FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
  && poetry install --no-root --no-interaction --no-ansi

COPY . /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]