"""Etapa 2: agrupa piezas que hablan de lo mismo.

Implementación mínima por similitud de titulares (Jaccard sobre palabras
significativas). El puerto `LLM` se acepta para poder sustituir la heurística
por una agrupación semántica sin cambiar la firma.
"""

from __future__ import annotations

import re
import unicodedata

from linotipo.domain.ports import LLM
from linotipo.pipeline.artifacts import Cluster, ClusterResult, IngestResult
from linotipo.pipeline.workdir import WorkDir

SIMILARITY_THRESHOLD = 0.3

_STOPWORDS = frozenset(
    [
        "a",
        "al",
        "algo",
        "ante",
        "antes",
        "como",
        "con",
        "contra",
        "de",
        "del",
        "desde",
        "donde",
        "durante",
        "e",
        "el",
        "ella",
        "ellas",
        "ellos",
        "en",
        "entre",
        "es",
        "esa",
        "ese",
        "eso",
        "esta",
        "este",
        "esto",
        "estos",
        "estas",
        "ha",
        "hace",
        "hacia",
        "han",
        "hasta",
        "hay",
        "la",
        "las",
        "le",
        "les",
        "lo",
        "los",
        "mas",
        "más",
        "me",
        "mi",
        "mis",
        "muy",
        "ni",
        "no",
        "nos",
        "o",
        "os",
        "otra",
        "otro",
        "para",
        "pero",
        "por",
        "que",
        "qué",
        "se",
        "ser",
        "si",
        "sí",
        "sin",
        "sobre",
        "su",
        "sus",
        "también",
        "te",
        "tras",
        "tu",
        "tus",
        "un",
        "una",
        "uno",
        "unos",
        "unas",
        "y",
        "ya",
    ]
)


def run_cluster(work: WorkDir, llm: LLM | None = None) -> ClusterResult:
    del llm  # reservado para agrupación semántica; la heurística actual no lo usa
    ingest = work.read("ingest", IngestResult)
    clusters: list[Cluster] = []
    token_sets: list[set[str]] = []
    for source in ingest.sources:
        tokens = _tokens(source.title)
        target = _find_similar(tokens, token_sets)
        if target is None:
            clusters.append(Cluster(id="", topic=source.title, source_ids=[source.id]))
            token_sets.append(tokens)
        else:
            clusters[target].source_ids.append(source.id)
            token_sets[target] |= tokens
    clusters.sort(key=lambda c: (-len(c.source_ids), c.topic))
    for index, cluster in enumerate(clusters, start=1):
        cluster.id = f"c-{index:03d}"
    result = ClusterResult(date=work.date, clusters=clusters)
    work.write("cluster", result)
    return result


def _find_similar(tokens: set[str], existing: list[set[str]]) -> int | None:
    best_index: int | None = None
    best_score = 0.0
    for index, other in enumerate(existing):
        union = tokens | other
        if not union:
            continue
        score = len(tokens & other) / len(union)
        if score >= SIMILARITY_THRESHOLD and score > best_score:
            best_index, best_score = index, score
    return best_index


def _tokens(title: str) -> set[str]:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z0-9]+", ascii_title.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}
