# Linotipo

**[linotipo.news](https://linotipo.news)** es un periódico diario generado por un agente de IA. Una única edición al día, igual para todos los lectores, con diseño de periódico clásico en blanco y negro, organizada por secciones y con las fuentes citadas al pie de cada artículo. Sin personalización, sin feed, sin tiempo real. La primera edición es en español y está centrada en España.

## Arquitectura

Linotipo no es una aplicación con backend en runtime: es un **pipeline batch** que produce un artefacto inmutable (la edición del día) más un **sitio estático** que lo renderiza. `back/` (Python, Typer, Pydantic) ejecuta cada mañana las etapas `ingest → cluster → select → write → render → publish`, con un diseño hexagonal ligero: dominio puro, puertos (`NewsSource`, `LLM`, `EditionRepository`, `Publisher`) y adaptadores intercambiables (RSS, Anthropic, un LLM falso para desarrollo). Los prompts viven versionados en `prompts/`, fuera del código. `front/` (Astro, TypeScript, CSS plano) lee las ediciones en build time y genera HTML puro. En el camino del lector no hay base de datos, ni colas, ni autenticación: solo ficheros.

## El contrato: `editions/`

Un fichero por edición, `editions/YYYY-MM-DD.json`. Lo escribe Python y lo lee Astro. Es la única frontera entre ambos mundos y está validado por partida doble:

- **Pydantic** en `back/src/linotipo/domain/models.py` (fuente de verdad; exporta `schema/edition.schema.json` con `linotipo schema export`).
- **Zod** en `front/src/schemas/edition.ts` (equivalente; Astro lo aplica al cargar la colección).
- `npm run check:editions` valida cada edición contra el JSON Schema en CI, así se detecta si Pydantic y Zod se desalinean.

Forma resumida:

```
Edition
  date, number, locale, region, generated_at, pipeline_version, prompt_version
  sections[]: { key, name, articles[] }
    Article: { slug, headline, subhead?, dateline?, body[] (párrafos en texto plano), citations[], topics[], lead }
      Citation: { source_id, quote? }
  sources[]: { id (sha256 corto de la URL), outlet, title, url, published_at }   ← catálogo único
```

Invariantes: toda `citation.source_id` existe en `sources`, los `slug` son únicos en la edición y hay como máximo un `lead` por sección. Una edición nunca se modifica una vez publicada.

Etapas intermedias: cada una persiste su salida en `back/.work/YYYY-MM-DD/<etapa>.json`, de modo que se puede relanzar una etapa suelta sin repetir las anteriores.

## Estructura

```
back/          pipeline Python (uv, Typer, Pydantic). Dockerfile para el cron.
front/         sitio Astro. Lee ../editions en build.
editions/      una edición por día (el contrato).
prompts/       prompts versionados: prompts/<etapa>/vN.md
schema/        JSON Schema exportado desde Pydantic.
```

## Ejecutar en local

Requisitos: [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por sí solo) y Node 22+.

```sh
cp .env.example .env        # opcional: por defecto todo funciona en modo fake, sin red ni tokens
```

### Back

```sh
cd back
uv sync --all-extras        # dependencias + extra [api] + grupo dev
uv run pytest
uv run ruff check src tests && uv run mypy
uv run linotipo --help
```

### Front

```sh
cd front
npm install
npm run dev                 # http://localhost:4321
npm run check:editions      # editions/*.json contra schema/edition.schema.json
npm run check               # astro check
npm run build               # genera front/dist
```

## Generar una edición: `run-all`

```sh
cd back
uv run linotipo run-all --date 2026-09-14
```

Sin más configuración usa la fuente de noticias y el LLM **falsos** (`LINOTIPO_NEWS_SOURCE=fake`, `LINOTIPO_LLM_PROVIDER=fake`), determinista y sin red, y deja `editions/2026-09-14.json` listo para que el front lo renderice. Para una edición real:

```sh
ANTHROPIC_API_KEY=sk-... uv run linotipo run-all --llm anthropic --source rss
```

Cada etapa también existe como comando propio (`ingest`, `cluster`, `select`, `write`, `render`, `publish`), idempotente y con la misma opción `--date`, para relanzar solo la parte que falló. `--select-version v2` o `--write-version v2` eligen otra versión de prompt. Si `LINOTIPO_PUBLISH_WEBHOOK_URL` está definida, `publish` la llama (por ejemplo el deploy hook de Coolify) para reconstruir el front.

### Cron en Coolify

La imagen se construye desde la raíz del monorepo porque necesita `prompts/` y `editions/`:

```sh
docker build -f back/Dockerfile -t linotipo-back .
docker run --rm --env-file .env -v "$PWD/editions:/app/editions" linotipo-back run-all
```

La imagen fija `LINOTIPO_LLM_PROVIDER=anthropic` y `LINOTIPO_NEWS_SOURCE=rss`; el cron solo tiene que aportar `ANTHROPIC_API_KEY` y montar `editions/`.

### API opcional

Capa fina sobre el pipeline, solo para uso interno (nunca en el camino del lector):

```sh
cd back && uv run --extra api uvicorn linotipo.api.app:app
```

## CI

- `.github/workflows/back.yml` (cambios en `back/`, `schema/`, `prompts/`): ruff, mypy, pytest y comprobación de que `schema/edition.schema.json` está al día.
- `.github/workflows/front.yml` (cambios en `front/`, `editions/`, `schema/`): `check:editions`, `astro check` y `astro build`.

## Licencias de tipografías

Playfair Display y Source Serif 4, autoalojadas en `front/public/fonts/`, bajo SIL Open Font License 1.1 (ver `OFL-*.txt` en ese directorio).
