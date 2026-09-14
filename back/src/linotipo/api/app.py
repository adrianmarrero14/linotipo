"""API HTTP opcional y fina. Importa el pipeline; el pipeline nunca importa esto.

Arranque: `uv run --extra api uvicorn linotipo.api.app:app`.
"""

from __future__ import annotations

from datetime import date

try:
    from fastapi import FastAPI, HTTPException
except ImportError as exc:  # pragma: no cover - solo sin el extra [api]
    raise ImportError("instala el extra `[api]`: uv sync --extra api") from exc

from linotipo import __version__
from linotipo.adapters.json_edition_repo import JsonEditionRepository
from linotipo.domain.models import Edition
from linotipo.pipeline import runner
from linotipo.settings import get_settings

app = FastAPI(title="Linotipo", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/editions")
def list_editions() -> list[str]:
    repo = JsonEditionRepository(get_settings().editions_path)
    return [d.isoformat() for d in repo.list_dates()]


@app.get("/editions/{edition_date}")
def get_edition(edition_date: date) -> Edition:
    repo = JsonEditionRepository(get_settings().editions_path)
    if not repo.exists(edition_date):
        raise HTTPException(status_code=404, detail="edición no encontrada")
    return repo.load(edition_date)


@app.post("/runs/{edition_date}", status_code=201)
def run_pipeline(edition_date: date) -> Edition:
    """Lanza `run-all` de forma síncrona. Pensado para uso interno, no para lectores."""
    ctx = runner.build_context(get_settings(), edition_date)
    return runner.run_all(ctx)
