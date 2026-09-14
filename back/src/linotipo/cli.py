"""CLI de Linotipo. Un comando por etapa, idempotente, pensado para invocarse desde cron."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Annotated

import typer

from linotipo.pipeline import runner
from linotipo.pipeline.cluster import run_cluster
from linotipo.pipeline.ingest import run_ingest
from linotipo.pipeline.publish import run_publish
from linotipo.pipeline.render import export_schema, run_render
from linotipo.pipeline.select import run_select
from linotipo.pipeline.write import run_write
from linotipo.settings import get_settings

app = typer.Typer(
    name="linotipo",
    help="Pipeline que genera la edición diaria de Linotipo.",
    no_args_is_help=True,
    add_completion=False,
)
schema_app = typer.Typer(help="Contrato JSON Schema entre back y front.")
app.add_typer(schema_app, name="schema")

DateOpt = Annotated[
    str | None,
    typer.Option("--date", "-d", help="Fecha de la edición (YYYY-MM-DD). Por defecto, hoy (UTC)."),
]
LLMOpt = Annotated[str | None, typer.Option("--llm", help="Proveedor de LLM: fake | anthropic.")]
SourceOpt = Annotated[str | None, typer.Option("--source", help="Fuente de noticias: fake | rss.")]
SelectVersionOpt = Annotated[str | None, typer.Option(help="Versión del prompt select (vN).")]
WriteVersionOpt = Annotated[str | None, typer.Option(help="Versión del prompt write (vN).")]


def _parse_date(value: str | None) -> date:
    if value is None:
        return datetime.now(tz=UTC).date()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(f"fecha inválida: {value!r}, usa YYYY-MM-DD") from exc


def _ctx(
    date_value: str | None,
    llm: str | None = None,
    source: str | None = None,
    select_version: str | None = None,
    write_version: str | None = None,
) -> runner.Context:
    settings = get_settings()
    return runner.build_context(
        settings,
        _parse_date(date_value),
        llm=_choice(llm, ("fake", "anthropic"), "--llm"),  # type: ignore[arg-type]
        news=_choice(source, ("fake", "rss"), "--source"),  # type: ignore[arg-type]
        select_version=select_version,
        write_version=write_version,
    )


def _choice(value: str | None, allowed: tuple[str, ...], flag: str) -> str | None:
    if value is None:
        return None
    if value not in allowed:
        raise typer.BadParameter(f"{flag} debe ser uno de {', '.join(allowed)}")
    return value


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Log detallado.")] = False,
) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command()
def ingest(date: DateOpt = None, source: SourceOpt = None) -> None:
    """Recoge piezas de la fuente de noticias → .work/<fecha>/ingest.json."""
    ctx = _ctx(date, source=source)
    result = run_ingest(ctx.work, ctx.source, max_sources=ctx.settings.max_sources)
    typer.echo(f"ingest: {len(result.sources)} fuentes → {ctx.work.file('ingest')}")


@app.command()
def cluster(date: DateOpt = None, llm: LLMOpt = None) -> None:
    """Agrupa piezas por tema → .work/<fecha>/cluster.json."""
    ctx = _ctx(date, llm=llm)
    result = run_cluster(ctx.work, ctx.llm)
    typer.echo(f"cluster: {len(result.clusters)} grupos → {ctx.work.file('cluster')}")


@app.command()
def select(
    date: DateOpt = None, llm: LLMOpt = None, select_version: SelectVersionOpt = None
) -> None:
    """El LLM elige grupos y secciones → .work/<fecha>/select.json."""
    ctx = _ctx(date, llm=llm, select_version=select_version)
    result = run_select(ctx.work, ctx.llm, ctx.select_prompt)
    picks = sum(len(s.picks) for s in result.sections)
    typer.echo(
        f"select: {picks} temas en {len(result.sections)} secciones → {ctx.work.file('select')}"
    )


@app.command()
def write(date: DateOpt = None, llm: LLMOpt = None, write_version: WriteVersionOpt = None) -> None:
    """El LLM redacta los artículos → .work/<fecha>/write.json."""
    ctx = _ctx(date, llm=llm, write_version=write_version)
    result = run_write(ctx.work, ctx.llm, ctx.write_prompt)
    typer.echo(f"write: {len(result.drafts)} artículos → {ctx.work.file('write')}")


@app.command()
def render(date: DateOpt = None) -> None:
    """Ensambla la edición y la exporta a editions/<fecha>.json."""
    ctx = _ctx(date)
    edition = run_render(ctx.work, ctx.repo, locale=ctx.settings.locale, region=ctx.settings.region)
    typer.echo(f"render: edición nº {edition.number} → {ctx.repo.path_for(edition.date)}")


@app.command()
def publish(date: DateOpt = None) -> None:
    """Valida la edición exportada y la publica (webhook si está configurado)."""
    ctx = _ctx(date)
    edition = run_publish(ctx.work, ctx.repo, ctx.publisher)
    typer.echo(f"publish: edición {edition.date} nº {edition.number} publicada")


@app.command("run-all")
def run_all(
    date: DateOpt = None,
    llm: LLMOpt = None,
    source: SourceOpt = None,
    select_version: SelectVersionOpt = None,
    write_version: WriteVersionOpt = None,
) -> None:
    """Ejecuta todas las etapas en orden: ingest → cluster → select → write → render → publish."""
    ctx = _ctx(date, llm, source, select_version, write_version)
    edition = runner.run_all(ctx)
    articles = sum(len(s.articles) for s in edition.sections)
    typer.echo(
        f"run-all: edición {edition.date} nº {edition.number}, "
        f"{len(edition.sections)} secciones, {articles} artículos, "
        f"{len(edition.sources)} fuentes → {ctx.repo.path_for(edition.date)}"
    )


@schema_app.command("export")
def schema_export() -> None:
    """Escribe schema/edition.schema.json a partir del modelo Pydantic."""
    settings = get_settings()
    target = export_schema(settings.schema_path / "edition.schema.json")
    typer.echo(f"schema: {target}")


if __name__ == "__main__":
    app()
