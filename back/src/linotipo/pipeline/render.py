"""Etapa 5: ensambla la `Edition` y la exporta a `editions/YYYY-MM-DD.json`.

También exporta el JSON Schema del contrato (`linotipo schema export`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from linotipo import __version__
from linotipo.domain.models import SECTION_ORDER, Edition, Section, Source
from linotipo.domain.ports import EditionRepository
from linotipo.pipeline.artifacts import IngestResult, WriteResult
from linotipo.pipeline.workdir import WorkDir


def run_render(
    work: WorkDir,
    repo: EditionRepository,
    *,
    locale: str = "es-ES",
    region: str = "ES",
    now: datetime | None = None,
) -> Edition:
    ingest = work.read("ingest", IngestResult)
    written = work.read("write", WriteResult)
    sources_by_id = {s.id: s for s in ingest.sources}

    sections: dict[str, Section] = {}
    cited: dict[str, Source] = {}
    for draft in written.drafts:
        section = sections.get(draft.section_key)
        if section is None:
            section = Section(key=draft.section_key, name=draft.section_name, articles=[])
            sections[draft.section_key] = section
        section.articles.append(draft.article)
        for citation in draft.article.citations:
            cited[citation.source_id] = sources_by_id[citation.source_id]

    ordered = sorted(
        sections.values(),
        key=lambda s: SECTION_ORDER.index(s.key) if s.key in SECTION_ORDER else len(SECTION_ORDER),
    )
    edition = Edition(
        date=work.date,
        number=edition_number(repo, work),
        locale=locale,
        region=region,
        sections=[Section.model_validate(s.model_dump()) for s in ordered],
        sources=sorted(cited.values(), key=lambda s: (s.published_at, s.id), reverse=True),
        generated_at=now or datetime.now(tz=UTC),
        pipeline_version=__version__,
        prompt_version=written.prompt_version,
    )
    work.write("render", edition)
    repo.save(edition)
    return edition


def edition_number(repo: EditionRepository, work: WorkDir) -> int:
    """Número de edición: correlativo por fecha. Si la edición ya existe, conserva el suyo."""
    if repo.exists(work.date):
        return repo.load(work.date).number
    previous = [d for d in repo.list_dates() if d < work.date]
    return len(previous) + 1


def export_schema(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(Edition.json_schema(), indent=2, ensure_ascii=False) + "\n"
    if not (target.is_file() and target.read_text(encoding="utf-8") == payload):
        target.write_text(payload, encoding="utf-8")
    return target
