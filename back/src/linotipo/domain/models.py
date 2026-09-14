"""Modelo de dominio de una edición de Linotipo.

Es el contrato entre `back/` (que lo escribe) y `front/` (que lo lee). Cualquier
cambio aquí debe reflejarse en `front/src/schemas/edition.ts` y regenerar
`schema/edition.schema.json` con `linotipo schema export`.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date as date_type
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

SECTION_ORDER: tuple[str, ...] = (
    "portada",
    "espana",
    "internacional",
    "economia",
    "sociedad",
    "cultura",
    "deportes",
    "ciencia",
)

SECTION_NAMES: dict[str, str] = {
    "portada": "Portada",
    "espana": "España",
    "internacional": "Internacional",
    "economia": "Economía",
    "sociedad": "Sociedad",
    "cultura": "Cultura",
    "deportes": "Deportes",
    "ciencia": "Ciencia",
}


def source_id_from_url(url: str) -> str:
    """Identificador estable de una fuente: sha256 corto de la URL normalizada."""
    normalized = url.strip().rstrip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def slugify(text: str, max_length: int = 80) -> str:
    """Convierte un titular en un slug ASCII apto para URL."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_length].rstrip("-") or "articulo"


class Source(BaseModel):
    """Una pieza publicada por un medio, tal como llegó al pipeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, description="Hash estable (sha256 corto) de la URL.")
    outlet: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: HttpUrl
    published_at: datetime


class Citation(BaseModel):
    """Referencia de un artículo a una fuente del catálogo de la edición."""

    source_id: str = Field(min_length=1)
    quote: str | None = None


class Article(BaseModel):
    """Un artículo de la edición, en texto plano."""

    model_config = ConfigDict(str_strip_whitespace=True)

    slug: str = Field(min_length=1, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    headline: str = Field(min_length=1)
    subhead: str | None = None
    dateline: str | None = None
    body: list[str] = Field(min_length=1, description="Párrafos en texto plano, sin markdown.")
    citations: list[Citation]
    topics: list[str] = []
    lead: bool = False


class Section(BaseModel):
    """Una sección del periódico con sus artículos en orden de aparición."""

    key: str = Field(min_length=1, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1)
    articles: list[Article]

    @model_validator(mode="after")
    def _at_most_one_lead(self) -> Section:
        leads = [a.slug for a in self.articles if a.lead]
        if len(leads) > 1:
            raise ValueError(
                f"la sección '{self.key}' tiene más de un artículo lead: {', '.join(leads)}"
            )
        return self


class Edition(BaseModel):
    """La edición diaria completa. Es un artefacto inmutable."""

    date: date_type
    number: int = Field(ge=1)
    locale: str = "es-ES"
    region: str = "ES"
    sections: list[Section]
    sources: list[Source] = Field(
        description="Catálogo único de fuentes; los artículos las referencian por id."
    )
    generated_at: datetime
    pipeline_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _check_integrity(self) -> Edition:
        source_ids = [s.id for s in self.sources]
        duplicated_sources = _duplicates(source_ids)
        if duplicated_sources:
            raise ValueError(f"ids de fuente duplicados: {', '.join(duplicated_sources)}")

        known = set(source_ids)
        slugs: list[str] = []
        for section in self.sections:
            for article in section.articles:
                slugs.append(article.slug)
                for citation in article.citations:
                    if citation.source_id not in known:
                        raise ValueError(
                            f"el artículo '{article.slug}' cita la fuente "
                            f"'{citation.source_id}', que no está en el catálogo"
                        )

        duplicated_slugs = _duplicates(slugs)
        if duplicated_slugs:
            raise ValueError(f"slugs duplicados en la edición: {', '.join(duplicated_slugs)}")
        return self

    def source_by_id(self, source_id: str) -> Source | None:
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        """JSON Schema del contrato, listo para escribir en `schema/edition.schema.json`."""
        schema = cls.model_json_schema()
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://linotipo.news/schema/edition.schema.json",
            **schema,
        }


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    repeated: list[str] = []
    for value in values:
        if value in seen and value not in repeated:
            repeated.append(value)
        seen.add(value)
    return repeated
