"""Configuración del pipeline. Se lee de variables de entorno y de `.env`."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["fake", "anthropic"]
NewsProvider = Literal["fake", "rss"]


def _default_repo_root() -> Path:
    """Raíz del monorepo: el directorio que contiene `prompts/` y `editions/`.

    Se busca hacia arriba desde el cwd; si no se encuentra, se asume la ruta
    relativa al paquete (`back/src/linotipo/settings.py` → `../../..`).
    """
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "prompts").is_dir() and (candidate / "editions").is_dir():
            return candidate
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LINOTIPO_",
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    locale: str = "es-ES"
    region: str = "ES"

    llm_provider: LLMProvider = "fake"
    news_source: NewsProvider = "fake"

    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "LINOTIPO_ANTHROPIC_API_KEY"),
    )
    anthropic_model: str = "claude-sonnet-5"
    anthropic_max_tokens: int = 4096

    rss_feeds: str = Field(default="", description="URLs de feeds separadas por coma.")
    max_sources: int = 200

    publish_webhook_url: str | None = None

    repo_root: Path = Field(default_factory=_default_repo_root)
    work_dir: Path | None = None
    editions_dir: Path | None = None
    prompts_dir: Path | None = None
    schema_dir: Path | None = None

    @property
    def work_path(self) -> Path:
        return self.work_dir or self.repo_root / "back" / ".work"

    @property
    def editions_path(self) -> Path:
        return self.editions_dir or self.repo_root / "editions"

    @property
    def prompts_path(self) -> Path:
        return self.prompts_dir or self.repo_root / "prompts"

    @property
    def schema_path(self) -> Path:
        return self.schema_dir or self.repo_root / "schema"

    @property
    def rss_feed_list(self) -> list[str]:
        return [u.strip() for u in self.rss_feeds.split(",") if u.strip()]


def get_settings() -> Settings:
    return Settings()
