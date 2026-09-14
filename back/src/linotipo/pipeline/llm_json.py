"""Extrae el JSON de una respuesta de LLM que puede venir envuelta en ```json ... ```."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    match = _FENCE_RE.search(text)
    if match:
        text = match.group(1).strip()
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"la respuesta del LLM no contiene JSON: {raw[:200]!r}")
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("la respuesta del LLM no es un objeto JSON")
    return data
