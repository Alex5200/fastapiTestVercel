FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY . /app

RUN uv sync --locked

CMD ["uv", "run", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
