"""Puertos del dominio. Los adaptadores en `linotipo.adapters` los implementan."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Protocol

from linotipo.domain.models import Edition, Source


class NewsSource(Protocol):
    """Proveedor de piezas de noticias (RSS, API, fixtures...)."""

    def fetch(self) -> list[Source]: ...


class LLM(Protocol):
    """Modelo de lenguaje. Recibe un prompt de sistema y uno de usuario; devuelve texto."""

    def complete(self, *, system: str, user: str) -> str: ...


class EditionRepository(Protocol):
    """Almacén de ediciones ya renderizadas (en esta fase, ficheros JSON en `editions/`)."""

    def save(self, edition: Edition) -> Path: ...

    def load(self, edition_date: date) -> Edition: ...

    def exists(self, edition_date: date) -> bool: ...

    def list_dates(self) -> list[date]: ...


class Publisher(Protocol):
    """Hace pública una edición ya guardada (webhook de despliegue, git push, S3...)."""

    def publish(self, edition: Edition, path: Path) -> None: ...
