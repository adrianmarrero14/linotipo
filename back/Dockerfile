# Imagen para ejecutar el CLI desde un cron (Coolify).
# Construir desde la raíz del monorepo, porque prompts/ y editions/ viven fuera de back/:
#   docker build -f back/Dockerfile -t linotipo-back .
# Ejecutar la edición del día:
#   docker run --rm --env-file .env -v "$PWD/editions:/app/editions" linotipo-back run-all
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    LINOTIPO_REPO_ROOT=/app \
    LINOTIPO_LLM_PROVIDER=anthropic \
    LINOTIPO_NEWS_SOURCE=rss

WORKDIR /app/back

COPY back/pyproject.toml back/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY back/src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

COPY prompts /app/prompts
COPY editions /app/editions

ENV PATH="/app/back/.venv/bin:$PATH"
WORKDIR /app
ENTRYPOINT ["linotipo"]
CMD ["--help"]
