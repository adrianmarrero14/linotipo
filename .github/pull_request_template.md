## Qué cambia

<!-- Qué y por qué, en dos o tres frases. El cómo ya está en el diff. -->

## Tipo

- [ ] `feat` funcionalidad nueva
- [ ] `fix` corrección
- [ ] `chore` mantenimiento, dependencias, configuración
- [ ] `docs` / `refactor` / `test` / `ci`

## Comprobaciones

Back (si has tocado `back/`, `prompts/` o `schema/`):

- [ ] `uv run pytest`
- [ ] `uv run ruff check src tests && uv run ruff format --check src tests`
- [ ] `uv run mypy`

Front (si has tocado `front/`, `editions/` o `schema/`):

- [ ] `npm run check:editions`
- [ ] `npm run check`
- [ ] `npm run build`

Contrato (si has tocado `domain/models.py`):

- [ ] `front/src/schemas/edition.ts` actualizado en paralelo
- [ ] `schema/edition.schema.json` regenerado con `uv run linotipo schema export`
- [ ] Las ediciones ya publicadas en `editions/` siguen validando

## Notas

<!-- Dependencias nuevas (deben haberse acordado antes), decisiones que convenga recordar, capturas si cambia el diseño. -->
