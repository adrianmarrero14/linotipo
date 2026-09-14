# CLAUDE.md

Guía para trabajar en este repositorio con Claude Code. Léela entera antes de tocar nada.

## Qué es Linotipo

Periódico diario generado por un agente de IA (linotipo.news). Una única edición al día, igual para todos, con diseño de periódico clásico en blanco y negro y fuentes citadas. Sin personalización, sin feed, sin tiempo real. Primera fase: español, España.

Arquitectura: **pipeline batch** en `back/` que produce un artefacto inmutable (`editions/YYYY-MM-DD.json`) y **sitio estático** en `front/` que lo renderiza en build time. No hay backend en runtime, ni base de datos, ni colas, ni auth en el camino del lector.

## Idioma

Todo en **español**: código (nombres de variables y funciones pueden ser en inglés cuando sea lo natural, pero comentarios, docstrings, mensajes de error, salida del CLI, tests, README y CI en español), interfaz del periódico, prompts y conversación.

## Estructura

```
back/       pipeline Python (uv, Typer, Pydantic). Hexagonal ligero.
  src/linotipo/domain/     modelos y puertos. NO importa nada de infraestructura.
  src/linotipo/pipeline/   etapas: ingest, cluster, select, write, render, publish
  src/linotipo/adapters/   rss_source, anthropic_llm, fake_llm, fake_source, json_edition_repo, publishers
  src/linotipo/api/        FastAPI opcional y fina. Importa el pipeline, nunca al revés.
  tests/
front/      Astro + TypeScript estricto + CSS plano. Sin framework UI, sin Tailwind.
editions/   una edición por día. Es el contrato. Nunca se edita a mano.
prompts/    prompts versionados: prompts/<etapa>/vN.md
schema/     edition.schema.json exportado desde Pydantic. No se edita a mano.
```

## Comandos

```sh
# back (desde back/)
uv sync --all-extras
uv run pytest
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy                                   # estricto sobre domain/
uv run linotipo run-all --date YYYY-MM-DD     # fake por defecto: sin red ni tokens
uv run linotipo schema export                 # regenera schema/edition.schema.json

# front (desde front/)
npm install
npm run dev                                   # http://localhost:4321
npm run check:editions                        # editions/*.json contra schema/
npm run check                                 # astro check
npm run build
```

Antes de dar algo por terminado: `uv run pytest`, `uv run ruff check`, `uv run mypy`, `npm run check:editions`, `npm run check` y `npm run build` en verde.

## Reglas

- **No añadas dependencias** en `back/pyproject.toml` ni en `front/package.json` sin preguntar antes.
- **El contrato cambia en tres sitios a la vez:** `back/src/linotipo/domain/models.py` (Pydantic), `front/src/schemas/edition.ts` (Zod) y `schema/edition.schema.json` (regenerar con `linotipo schema export`). La CI del back falla si el schema exportado no está al día.
- **Dominio puro:** `domain/` no importa de `adapters/`, `pipeline/`, `settings` ni librerías de infraestructura. Los adaptadores implementan los `Protocol` de `domain/ports.py`.
- **Idempotencia:** cada etapa lee su entrada de `back/.work/<fecha>/` y sobrescribe su salida. Relanzar una etapa no debe cambiar el resultado si la entrada no cambió.
- **Fake por defecto:** `Settings` usa `llm_provider=fake` y `news_source=fake`. Los tests y la edición de ejemplo nunca deben llamar a la API de Anthropic ni a la red.
- **Prompts:** cambios de comportamiento del LLM se hacen creando `vN+1.md`, no editando `vN.md`. La edición registra qué versión la generó.
- **Front sin JavaScript en cliente** salvo necesidad justificada. CSS plano en `front/src/styles/global.css`. Tipografías autoalojadas en `front/public/fonts/` (OFL).
- **Ediciones inmutables:** no se corrigen ni se regeneran ediciones ya publicadas en `editions/` salvo petición explícita.
- `astro/zod` es **Zod 4**: usar `z.iso.date()`, `z.iso.datetime()`, `z.url()`, `code: "custom"`.

## Commits

Conventional Commits, en español, en imperativo, sin punto final en el título:

```
<tipo>(<ámbito opcional>): <resumen en minúsculas>

<cuerpo opcional: qué y por qué, no cómo>
```

Tipos: `feat` (funcionalidad nueva), `fix` (corrección), `chore` (mantenimiento, dependencias, configuración), `docs`, `refactor`, `test`, `ci`, `style`.
Ámbitos habituales: `back`, `front`, `domain`, `pipeline`, `prompts`, `schema`, `editions`.

Ejemplos:

```
feat(pipeline): agrupa titulares por similitud semántica
fix(front): corrige el salto de columnas en móvil
chore(back): actualiza pydantic a 2.14
docs: documenta el webhook de publicación
```

Un cambio del contrato que rompa ediciones anteriores lleva `!` tras el tipo y un pie `BREAKING CHANGE:`.

Commitea solo cuando se pida. Cada commit debe dejar la CI en verde. Rama por defecto: `main`. Remoto por SSH.

## Estado y decisiones

- Las etapas `cluster`, `select` y `write` tienen lógica mínima que funciona con `fake_llm`. `cluster` usa Jaccard sobre titulares y no llama al LLM todavía.
- El `Dockerfile` de `back/` se construye desde la raíz del monorepo (`docker build -f back/Dockerfile .`) porque necesita `prompts/` y `editions/`. Está pensado para un cron en Coolify.
- Números de edición: correlativos por fecha; si la edición existe, conserva su número.
- Más adelante: otros idiomas y geografías. No diseñar todavía para ello, pero no cerrarlo (por eso `locale` y `region` van en la edición).
