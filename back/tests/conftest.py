from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from linotipo.domain.models import Article, Citation, Edition, Section, Source, source_id_from_url
from linotipo.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITION_DATE = date(2026, 9, 14)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings aislados: trabajo y ediciones en tmp_path, prompts reales del repo."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        llm_provider="fake",
        news_source="fake",
        repo_root=REPO_ROOT,
        work_dir=tmp_path / ".work",
        editions_dir=tmp_path / "editions",
        schema_dir=tmp_path / "schema",
    )


def make_source(url: str, outlet: str = "El País", title: str = "Titular") -> Source:
    return Source(
        id=source_id_from_url(url),
        outlet=outlet,
        title=title,
        url=url,  # type: ignore[arg-type]
        published_at=datetime(2026, 9, 14, 6, 0, tzinfo=UTC),
    )


def make_article(slug: str, source: Source, *, lead: bool = False) -> Article:
    return Article(
        slug=slug,
        headline=slug.replace("-", " ").capitalize(),
        body=["Primer párrafo.", "Segundo párrafo."],
        citations=[Citation(source_id=source.id, quote="cita")],
        topics=["prueba"],
        lead=lead,
    )


def make_edition(sections: list[Section], sources: list[Source]) -> Edition:
    return Edition(
        date=EDITION_DATE,
        number=1,
        sections=sections,
        sources=sources,
        generated_at=datetime(2026, 9, 14, 7, 0, tzinfo=UTC),
        pipeline_version="0.1.0",
        prompt_version="select=v1;write=v1",
    )
