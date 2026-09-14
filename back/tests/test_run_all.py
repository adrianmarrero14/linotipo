from __future__ import annotations

import json

from conftest import EDITION_DATE
from linotipo.adapters.fake_llm import FakeLLM
from linotipo.domain.models import SECTION_ORDER, Edition
from linotipo.pipeline import runner
from linotipo.settings import Settings


def test_run_all_with_fake_llm_produces_valid_edition(settings: Settings) -> None:
    ctx = runner.build_context(settings, EDITION_DATE)
    assert isinstance(ctx.llm, FakeLLM)

    edition = runner.run_all(ctx)

    path = settings.editions_path / "2026-09-14.json"
    assert path.is_file()
    reloaded = Edition.model_validate_json(path.read_text(encoding="utf-8"))
    assert reloaded == edition
    assert reloaded.number == 1
    assert reloaded.prompt_version == "select=v1;write=v1"
    assert reloaded.pipeline_version == "0.1.0"

    # Contenido razonable: varias secciones, cada una con un lead, y fuentes citadas.
    assert len(reloaded.sections) >= 4
    assert [s.key for s in reloaded.sections] == sorted(
        (s.key for s in reloaded.sections), key=SECTION_ORDER.index
    )
    for section in reloaded.sections:
        assert sum(a.lead for a in section.articles) == 1
        for article in section.articles:
            assert article.citations
            assert all(reloaded.source_by_id(c.source_id) for c in article.citations)

    # Ningún token gastado: el LLM falso registró llamadas para select y write.
    assert len(ctx.llm.calls) >= 2

    # Cada etapa dejó su artefacto para poder relanzarla por separado.
    for stage in ("ingest", "cluster", "select", "write", "render"):
        assert ctx.work.file(stage).is_file(), stage


def test_run_all_is_idempotent_and_numbering_is_sequential(settings: Settings) -> None:
    first = runner.run_all(runner.build_context(settings, EDITION_DATE))
    again = runner.run_all(runner.build_context(settings, EDITION_DATE))
    assert again.number == first.number == 1
    assert again.sections == first.sections
    assert again.sources == first.sources

    later = runner.run_all(runner.build_context(settings, EDITION_DATE.replace(day=15)))
    assert later.number == 2
    earlier = runner.run_all(runner.build_context(settings, EDITION_DATE.replace(day=13)))
    assert earlier.number == 1  # numeración por fecha, no por orden de generación


def test_cluster_groups_similar_headlines(settings: Settings) -> None:
    ctx = runner.build_context(settings, EDITION_DATE)
    runner.run_ingest(ctx.work, ctx.source)
    result = runner.run_cluster(ctx.work, ctx.llm)
    ingest = json.loads(ctx.work.file("ingest").read_text(encoding="utf-8"))
    assert len(result.clusters) < len(ingest["sources"])
    assert any(len(c.source_ids) >= 2 for c in result.clusters)
    ids = [c.id for c in result.clusters]
    assert ids == sorted(ids)
