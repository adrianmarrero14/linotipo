"""Fábrica de adaptadores según `Settings` y ejecución encadenada de las etapas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from linotipo.adapters.fake_llm import FakeLLM
from linotipo.adapters.fake_source import FakeNewsSource
from linotipo.adapters.json_edition_repo import JsonEditionRepository
from linotipo.adapters.publishers import LocalPublisher, WebhookPublisher
from linotipo.domain.models import Edition
from linotipo.domain.ports import LLM, NewsSource, Publisher
from linotipo.pipeline.cluster import run_cluster
from linotipo.pipeline.ingest import run_ingest
from linotipo.pipeline.publish import run_publish
from linotipo.pipeline.render import run_render
from linotipo.pipeline.select import run_select
from linotipo.pipeline.workdir import WorkDir
from linotipo.pipeline.write import run_write
from linotipo.prompts import Prompt, load_prompt
from linotipo.settings import LLMProvider, NewsProvider, Settings


@dataclass
class Context:
    settings: Settings
    work: WorkDir
    repo: JsonEditionRepository
    source: NewsSource
    llm: LLM
    publisher: Publisher
    select_prompt: Prompt
    write_prompt: Prompt


def build_context(
    settings: Settings,
    edition_date: date,
    *,
    llm: LLMProvider | None = None,
    news: NewsProvider | None = None,
    select_version: str | None = None,
    write_version: str | None = None,
) -> Context:
    return Context(
        settings=settings,
        work=WorkDir(settings.work_path, edition_date),
        repo=JsonEditionRepository(settings.editions_path),
        source=build_source(settings, news or settings.news_source, edition_date),
        llm=build_llm(settings, llm or settings.llm_provider),
        publisher=build_publisher(settings),
        select_prompt=load_prompt(settings.prompts_path, "select", select_version),
        write_prompt=load_prompt(settings.prompts_path, "write", write_version),
    )


def build_llm(settings: Settings, provider: LLMProvider) -> LLM:
    if provider == "fake":
        return FakeLLM()
    if not settings.anthropic_api_key:
        raise RuntimeError("falta ANTHROPIC_API_KEY para usar el proveedor anthropic")
    from linotipo.adapters.anthropic_llm import AnthropicLLM

    return AnthropicLLM(
        settings.anthropic_api_key,
        model=settings.anthropic_model,
        max_tokens=settings.anthropic_max_tokens,
    )


def build_source(settings: Settings, provider: NewsProvider, edition_date: date) -> NewsSource:
    if provider == "fake":
        return FakeNewsSource(edition_date)
    from linotipo.adapters.rss_source import RssNewsSource

    return RssNewsSource(settings.rss_feed_list or None, max_sources=settings.max_sources)


def build_publisher(settings: Settings) -> Publisher:
    if settings.publish_webhook_url:
        return WebhookPublisher(settings.publish_webhook_url)
    return LocalPublisher()


def run_all(ctx: Context) -> Edition:
    run_ingest(ctx.work, ctx.source, max_sources=ctx.settings.max_sources)
    run_cluster(ctx.work, ctx.llm)
    run_select(ctx.work, ctx.llm, ctx.select_prompt)
    run_write(ctx.work, ctx.llm, ctx.write_prompt)
    run_render(ctx.work, ctx.repo, locale=ctx.settings.locale, region=ctx.settings.region)
    return run_publish(ctx.work, ctx.repo, ctx.publisher)
