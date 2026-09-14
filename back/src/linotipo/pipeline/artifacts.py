"""Artefactos intermedios que cada etapa persiste en `back/.work/<fecha>/<etapa>.json`.

No forman parte del contrato con `front/`; solo sirven para relanzar etapas sueltas.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from linotipo.domain.models import Article, Source


class IngestResult(BaseModel):
    date: date
    sources: list[Source]


class Cluster(BaseModel):
    id: str
    topic: str
    source_ids: list[str] = Field(min_length=1)


class ClusterResult(BaseModel):
    date: date
    clusters: list[Cluster]


class Pick(BaseModel):
    cluster_id: str
    lead: bool = False
    angle: str = ""


class SectionPlan(BaseModel):
    key: str
    name: str
    picks: list[Pick]


class SelectResult(BaseModel):
    date: date
    prompt_version: str
    sections: list[SectionPlan]


class Draft(BaseModel):
    cluster_id: str
    section_key: str
    section_name: str
    article: Article


class WriteResult(BaseModel):
    date: date
    prompt_version: str
    drafts: list[Draft]
