"""Etapa 3: el LLM elige qué clusters entran en la edición y en qué sección."""

from __future__ import annotations

import json
from typing import Any

from linotipo.domain.models import SECTION_NAMES, SECTION_ORDER
from linotipo.domain.ports import LLM
from linotipo.pipeline.artifacts import ClusterResult, IngestResult, Pick, SectionPlan, SelectResult
from linotipo.pipeline.llm_json import parse_json_response
from linotipo.pipeline.workdir import WorkDir
from linotipo.prompts import Prompt


def run_select(work: WorkDir, llm: LLM, prompt: Prompt) -> SelectResult:
    ingest = work.read("ingest", IngestResult)
    clusters = work.read("cluster", ClusterResult)
    sources_by_id = {s.id: s for s in ingest.sources}

    user_payload = {
        "date": work.date.isoformat(),
        "clusters": [
            {
                "id": c.id,
                "topic": c.topic,
                "source_ids": c.source_ids,
                "sources": [
                    _source_view(sources_by_id[sid]) for sid in c.source_ids if sid in sources_by_id
                ],
            }
            for c in clusters.clusters
        ],
    }
    raw = llm.complete(system=prompt.text, user=json.dumps(user_payload, ensure_ascii=False))
    data = parse_json_response(raw)

    known_clusters = {c.id for c in clusters.clusters}
    sections = _coerce_sections(data, known_clusters)
    result = SelectResult(date=work.date, prompt_version=prompt.version, sections=sections)
    work.write("select", result)
    return result


def _coerce_sections(data: dict[str, Any], known_clusters: set[str]) -> list[SectionPlan]:
    sections: list[SectionPlan] = []
    used: set[str] = set()
    for raw_section in data.get("sections", []):
        key = str(raw_section.get("key", "")).strip().lower()
        if key not in SECTION_NAMES:
            continue
        picks: list[Pick] = []
        for raw_pick in raw_section.get("picks", []):
            cluster_id = str(raw_pick.get("cluster_id", "")).strip()
            if cluster_id not in known_clusters or cluster_id in used:
                continue
            used.add(cluster_id)
            picks.append(
                Pick(
                    cluster_id=cluster_id,
                    lead=bool(raw_pick.get("lead", False)),
                    angle=str(raw_pick.get("angle", "")).strip(),
                )
            )
        if not picks:
            continue
        # Como máximo un lead por sección: se queda el primero marcado, o el primero a secas.
        lead_seen = False
        for pick in picks:
            if pick.lead and not lead_seen:
                lead_seen = True
            else:
                pick.lead = False
        if not lead_seen:
            picks[0].lead = True
        sections.append(
            SectionPlan(key=key, name=raw_section.get("name") or SECTION_NAMES[key], picks=picks)
        )
    sections.sort(key=lambda s: SECTION_ORDER.index(s.key))
    return sections


def _source_view(source: Any) -> dict[str, Any]:
    return {
        "id": source.id,
        "outlet": source.outlet,
        "title": source.title,
        "url": str(source.url),
        "published_at": source.published_at.isoformat(),
    }
