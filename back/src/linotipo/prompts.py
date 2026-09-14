"""Carga de prompts versionados desde `prompts/<nombre>/v<N>.md`."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_VERSION_RE = re.compile(r"^v(\d+)\.md$")


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    text: str

    @property
    def label(self) -> str:
        return f"{self.name}={self.version}"


def list_versions(prompts_dir: Path, name: str) -> list[str]:
    folder = prompts_dir / name
    if not folder.is_dir():
        return []
    versions: list[tuple[int, str]] = []
    for path in folder.iterdir():
        match = _VERSION_RE.match(path.name)
        if match:
            versions.append((int(match.group(1)), f"v{match.group(1)}"))
    return [label for _, label in sorted(versions)]


def load_prompt(prompts_dir: Path, name: str, version: str | None = None) -> Prompt:
    """Carga `prompts/<name>/<version>.md`. Sin `version`, usa la más alta."""
    if version is None:
        versions = list_versions(prompts_dir, name)
        if not versions:
            raise FileNotFoundError(f"no hay prompts en {prompts_dir / name}")
        version = versions[-1]
    if not version.startswith("v"):
        version = f"v{version}"
    path = prompts_dir / name / f"{version}.md"
    if not path.is_file():
        raise FileNotFoundError(f"prompt no encontrado: {path}")
    return Prompt(name=name, version=version, text=path.read_text(encoding="utf-8").strip())


def combined_version(*prompts: Prompt) -> str:
    """Etiqueta única para `Edition.prompt_version`, p. ej. `select=v1;write=v1`."""
    return ";".join(p.label for p in prompts)
