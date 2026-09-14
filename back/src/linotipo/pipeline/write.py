"""Etapa 4: el LLM redacta un artículo por cada cluster seleccionado."""

from __future__ import annotations

import json
from typing import Any

from linotipo.domain.models import Article, Citation, Source, slugify
from linotipo.domain.ports import LLM
from linotipo.pipeline.artifacts import (
    Cluster,
    ClusterResult,
    Draft,
    IngestResult,
    SelectResult,
    WriteResult,
)
from linotipo.pipeline.llm_json import parse_json_response
from linotipo.pipeline.workdir import WorkDir
from linotipo.prompts import Prompt


def run_write(work: WorkDir, llm: LLM, prompt: Prompt) -> WriteResult:
    ingest = work.read("ingest", IngestResult)
    clusters = work.read("cluster", ClusterResult)
    selection = work.read("select", SelectResult)

    sources_by_id = {s.id: s for s in ingest.sources}
    clusters_by_id = {c.id: c for c in clusters.clusters}
    used_slugs: set[str] = set()
    drafts: list[Draft] = []

    for section in selection.sections:
        for pick in section.picks:
            cluster = clusters_by_id[pick.cluster_id]
            cluster_sources = [
                sources_by_id[sid] for sid in cluster.source_ids if sid in sources_by_id
            ]
            if not cluster_sources:
                continue
            payload = {
                "date": work.date.isoformat(),
                "topic": cluster.topic,
                "angle": pick.angle,
                "section": section.key,
                "sources": [_source_view(s) for s in cluster_sources],
            }
            raw = llm.complete(system=prompt.text, user=json.dumps(payload, ensure_ascii=False))
            article = _coerce_article(
                parse_json_response(raw), cluster, cluster_sources, pick.lead, used_slugs
            )
            drafts.append(
                Draft(
                    cluster_id=cluster.id,
                    section_key=section.key,
                    section_name=section.name,
                    article=article,
                )
            )

    result = WriteResult(
        date=work.date,
        prompt_version=f"select={selection.prompt_version};{prompt.label}",
        drafts=drafts,
    )
    work.write("write", result)
    return result


def _coerce_article(
    data: dict[str, Any],
    cluster: Cluster,
    sources: list[Source],
    lead: bool,
    used_slugs: set[str],
) -> Article:
    headline = str(data.get("headline") or cluster.topic).strip()
    body = [str(p).strip() for p in data.get("body", []) if str(p).strip()]
    if not body:
        body = [cluster.topic]

    allowed = {s.id for s in sources}
    citations: list[Citation] = []
    for raw in data.get("citations", []):
        source_id = str(raw.get("source_id", "")).strip()
        if source_id in allowed and all(c.source_id != source_id for c in citations):
            quote = raw.get("quote")
            citations.append(Citation(source_id=source_id, quote=str(quote) if quote else None))
    if not citations:
        citations = [Citation(source_id=s.id) for s in sources]

    slug = _unique_slug(slugify(headline), used_slugs)
    topics = [str(t).strip().lower() for t in data.get("topics", []) if str(t).strip()][:4]
    subhead = data.get("subhead")
    dateline = data.get("dateline")
    return Article(
        slug=slug,
        headline=headline,
        subhead=str(subhead).strip() if subhead else None,
        dateline=str(dateline).strip() if dateline else None,
        body=body,
        citations=citations,
        topics=topics,
        lead=lead,
    )


def _unique_slug(base: str, used: set[str]) -> str:
    slug = base
    counter = 2
    while slug in used:
        slug = f"{base}-{counter}"
        counter += 1
    used.add(slug)
    return slug


def _source_view(source: Source) -> dict[str, Any]:
    return {
        "id": source.id,
        "outlet": source.outlet,
        "title": source.title,
        "url": str(source.url),
        "published_at": source.published_at.isoformat(),
    }
