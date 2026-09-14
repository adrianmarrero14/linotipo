from __future__ import annotations

import pytest
from pydantic import ValidationError

from conftest import make_article, make_edition, make_source
from linotipo.domain.models import Citation, Section, slugify, source_id_from_url


def test_source_id_is_stable_and_short() -> None:
    assert source_id_from_url("https://a.example/x") == source_id_from_url("https://a.example/x/")
    assert len(source_id_from_url("https://a.example/x")) == 12


def test_slugify_strips_accents_and_symbols() -> None:
    assert slugify("El Gobierno aprueba la reforma: ¡ya!") == "el-gobierno-aprueba-la-reforma-ya"
    assert slugify("¿¿??") == "articulo"


def test_valid_edition_passes() -> None:
    src = make_source("https://a.example/1")
    edition = make_edition(
        [Section(key="portada", name="Portada", articles=[make_article("uno", src, lead=True)])],
        [src],
    )
    assert edition.sections[0].articles[0].lead is True
    assert edition.source_by_id(src.id) is src


def test_citation_must_reference_catalogue() -> None:
    src = make_source("https://a.example/1")
    article = make_article("uno", src)
    article.citations.append(Citation(source_id="nope"))
    with pytest.raises(ValidationError, match="no está en el catálogo"):
        make_edition([Section(key="portada", name="Portada", articles=[article])], [src])


def test_slugs_must_be_unique_across_edition() -> None:
    src = make_source("https://a.example/1")
    with pytest.raises(ValidationError, match="slugs duplicados"):
        make_edition(
            [
                Section(key="portada", name="Portada", articles=[make_article("uno", src)]),
                Section(key="espana", name="España", articles=[make_article("uno", src)]),
            ],
            [src],
        )


def test_at_most_one_lead_per_section() -> None:
    src = make_source("https://a.example/1")
    with pytest.raises(ValidationError, match="más de un artículo lead"):
        Section(
            key="portada",
            name="Portada",
            articles=[make_article("uno", src, lead=True), make_article("dos", src, lead=True)],
        )


def test_duplicate_sources_rejected() -> None:
    src = make_source("https://a.example/1")
    with pytest.raises(ValidationError, match="ids de fuente duplicados"):
        make_edition([], [src, src])


def test_slug_pattern_enforced() -> None:
    src = make_source("https://a.example/1")
    with pytest.raises(ValidationError):
        make_article("Con Mayúsculas", src)
