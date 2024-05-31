FROM python:3.10-slim-bookworm

WORKDIR /semantic-cache

COPY poetry.lock pyproject.toml /semantic-cache/

RUN pip install poetry==1.5.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN poetry install --without linting --no-root && rm -rf $POETRY_CACHE_DIR

COPY . /semantic-cache/
COPY .env.example .env

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]