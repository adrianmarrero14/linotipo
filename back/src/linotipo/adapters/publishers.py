"""Implementaciones del puerto `Publisher`."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from linotipo.domain.models import Edition

log = logging.getLogger(__name__)


class LocalPublisher:
    """No hace nada más allá de registrar la ruta: el JSON en `editions/` ya es público
    en cuanto el front se reconstruye."""

    def publish(self, edition: Edition, path: Path) -> None:
        log.info("edición %s (nº %d) publicada en %s", edition.date, edition.number, path)


class WebhookPublisher:
    """Llama a un webhook (p. ej. el deploy hook de Coolify) para reconstruir el front."""

    def __init__(self, url: str, *, timeout: float = 30.0) -> None:
        self.url = url
        self.timeout = timeout

    def publish(self, edition: Edition, path: Path) -> None:
        response = httpx.post(
            self.url,
            json={"date": edition.date.isoformat(), "number": edition.number, "path": str(path)},
            timeout=self.timeout,
        )
        response.raise_for_status()
        log.info("webhook de publicación respondió %s para %s", response.status_code, edition.date)
