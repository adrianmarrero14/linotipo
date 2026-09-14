"""Directorio de trabajo de una fecha: `back/.work/YYYY-MM-DD/<etapa>.json`."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class WorkDir:
    def __init__(self, root: Path, edition_date: date) -> None:
        self.path = root / edition_date.isoformat()
        self.date = edition_date

    def file(self, stage: str) -> Path:
        return self.path / f"{stage}.json"

    def write(self, stage: str, artifact: BaseModel) -> Path:
        self.path.mkdir(parents=True, exist_ok=True)
        target = self.file(stage)
        target.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return target

    def read(self, stage: str, model: type[T]) -> T:
        target = self.file(stage)
        if not target.is_file():
            raise FileNotFoundError(
                f"no existe {target}; ejecuta antes la etapa `{stage}` para {self.date}"
            )
        return model.model_validate_json(target.read_text(encoding="utf-8"))
