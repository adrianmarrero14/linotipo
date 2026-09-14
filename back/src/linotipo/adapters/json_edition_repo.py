"""Repositorio de ediciones como ficheros `editions/YYYY-MM-DD.json`."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from linotipo.domain.models import Edition

_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")


class JsonEditionRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def path_for(self, edition_date: date) -> Path:
        return self.directory / f"{edition_date.isoformat()}.json"

    def save(self, edition: Edition) -> Path:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.path_for(edition.date)
        payload = edition.model_dump_json(indent=2, exclude_none=False) + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == payload:
            return target
        target.write_text(payload, encoding="utf-8")
        return target

    def load(self, edition_date: date) -> Edition:
        target = self.path_for(edition_date)
        if not target.is_file():
            raise FileNotFoundError(f"no existe la edición {target}")
        return Edition.model_validate_json(target.read_text(encoding="utf-8"))

    def exists(self, edition_date: date) -> bool:
        return self.path_for(edition_date).is_file()

    def list_dates(self) -> list[date]:
        if not self.directory.is_dir():
            return []
        dates: list[date] = []
        for path in self.directory.iterdir():
            match = _FILENAME_RE.match(path.name)
            if match:
                dates.append(date.fromisoformat(match.group(1)))
        return sorted(dates)
