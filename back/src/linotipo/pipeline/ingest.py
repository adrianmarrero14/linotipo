"""Etapa 1: recoge piezas de la fuente de noticias y las persiste en `ingest.json`."""

from __future__ import annotations

from linotipo.domain.models import Source
from linotipo.domain.ports import NewsSource
from linotipo.pipeline.artifacts import IngestResult
from linotipo.pipeline.workdir import WorkDir


def run_ingest(work: WorkDir, source: NewsSource, *, max_sources: int = 200) -> IngestResult:
    seen: set[str] = set()
    unique: list[Source] = []
    for item in source.fetch():
        if item.id in seen:
            continue
        seen.add(item.id)
        unique.append(item)
    unique.sort(key=lambda s: (s.published_at, s.id), reverse=True)
    result = IngestResult(date=work.date, sources=unique[:max_sources])
    work.write("ingest", result)
    return result
