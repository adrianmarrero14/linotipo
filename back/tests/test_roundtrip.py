from __future__ import annotations

import json
from pathlib import Path

from conftest import make_article, make_edition, make_source
from linotipo.adapters.json_edition_repo import JsonEditionRepository
from linotipo.domain.models import Edition, Section
from linotipo.pipeline.render import export_schema


def _sample() -> Edition:
    a = make_source("https://a.example/1", "El País", "Uno")
    b = make_source("https://b.example/2", "RTVE", "Dos")
    return make_edition(
        [
            Section(key="portada", name="Portada", articles=[make_article("uno", a, lead=True)]),
            Section(key="espana", name="España", articles=[make_article("dos", b)]),
        ],
        [a, b],
    )


def test_json_roundtrip_is_lossless() -> None:
    edition = _sample()
    payload = edition.model_dump_json(indent=2)
    restored = Edition.model_validate_json(payload)
    assert restored == edition
    assert restored.model_dump_json(indent=2) == payload


def test_repository_save_load_list_is_idempotent(tmp_path: Path) -> None:
    repo = JsonEditionRepository(tmp_path / "editions")
    edition = _sample()
    path = repo.save(edition)
    first_mtime = path.stat().st_mtime_ns
    assert repo.save(edition) == path
    assert path.stat().st_mtime_ns == first_mtime  # contenido idéntico: no reescribe
    assert repo.exists(edition.date)
    assert repo.load(edition.date) == edition
    assert repo.list_dates() == [edition.date]


def test_schema_export_describes_edition(tmp_path: Path) -> None:
    target = export_schema(tmp_path / "schema" / "edition.schema.json")
    schema = json.loads(target.read_text(encoding="utf-8"))
    assert schema["$schema"].startswith("https://json-schema.org/draft/2020-12")
    assert schema["title"] == "Edition"
    assert set(schema["required"]) >= {"date", "number", "sections", "sources", "generated_at"}
    assert {"Article", "Citation", "Section", "Source"} <= set(schema["$defs"])
