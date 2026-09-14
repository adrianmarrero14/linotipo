"""LLM determinista, sin red ni tokens.

Inspecciona el JSON del mensaje de usuario para saber qué etapa lo llama:
- si trae `clusters` → responde como la etapa `select`;
- si trae `sources` y `angle` → responde como la etapa `write`.
Devuelve JSON válido conforme a lo que piden los prompts de `prompts/`.
"""

from __future__ import annotations

import json
from typing import Any

from linotipo.domain.models import SECTION_NAMES, SECTION_ORDER

MAX_PICKS = 12


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, user: str) -> str:
        self.calls.append({"system": system, "user": user})
        payload = json.loads(user)
        if "clusters" in payload:
            return json.dumps(_select(payload), ensure_ascii=False)
        if "sources" in payload:
            return json.dumps(_write(payload), ensure_ascii=False)
        raise ValueError("FakeLLM no reconoce la petición: faltan `clusters` o `sources`")


def _select(payload: dict[str, Any]) -> dict[str, Any]:
    clusters = payload["clusters"][:MAX_PICKS]
    # Ordena por tamaño de cluster (más fuentes = más relevante) y reparte en secciones.
    ranked = sorted(clusters, key=lambda c: (-len(c["source_ids"]), c["id"]))
    section_keys = [k for k in SECTION_ORDER if k != "portada"]
    by_section: dict[str, list[dict[str, Any]]] = {}
    for index, cluster in enumerate(ranked):
        key = "portada" if index == 0 else section_keys[(index - 1) % len(section_keys)]
        picks = by_section.setdefault(key, [])
        picks.append(
            {
                "cluster_id": cluster["id"],
                "lead": len(picks) == 0,
                "angle": f"Resumen factual de: {cluster['topic']}",
            }
        )
    return {
        "sections": [
            {"key": key, "name": SECTION_NAMES[key], "picks": by_section[key]}
            for key in SECTION_ORDER
            if key in by_section
        ]
    }


def _write(payload: dict[str, Any]) -> dict[str, Any]:
    sources: list[dict[str, Any]] = payload["sources"]
    topic: str = payload.get("topic") or sources[0]["title"]
    outlets = sorted({s["outlet"] for s in sources})
    first = sources[0]
    others = sources[1:]

    paragraphs = [
        f"{topic}. Así lo recogen este {_weekday(payload.get('date'))} "
        f"{_join(outlets)}, según las piezas consultadas por Linotipo.",
        f"{first['outlet']} titula «{first['title']}». "
        + (
            "Otros medios coinciden en lo esencial: "
            + "; ".join(f"{s['outlet']} habla de «{s['title']}»" for s in others)
            + "."
            if others
            else "Por ahora es el único medio que recoge la noticia."
        ),
        "Este artículo ha sido generado con un modelo de prueba sin acceso al texto completo "
        "de las fuentes; el contenido se limita a lo que indican sus titulares. "
        "Consulte las fuentes citadas al pie para el detalle.",
    ]
    return {
        "headline": _headline(topic),
        "subhead": f"Cobertura de {len(sources)} fuente{'s' if len(sources) != 1 else ''}",
        "dateline": "MADRID",
        "body": paragraphs,
        "citations": [
            {"source_id": s["id"], "quote": s["title"] if i == 0 else None}
            for i, s in enumerate(sources)
        ],
        "topics": [w.lower() for w in topic.split()[:2]],
    }


def _headline(topic: str) -> str:
    words = topic.split()
    return " ".join(words[:12]).rstrip(".,;:")


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else "la prensa"
    return ", ".join(items[:-1]) + " y " + items[-1]


def _weekday(value: str | None) -> str:
    from datetime import date

    names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    if not value:
        return "día"
    try:
        return names[date.fromisoformat(value).weekday()]
    except ValueError:
        return "día"
