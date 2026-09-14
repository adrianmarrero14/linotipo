"""Fuente de noticias basada en feeds RSS/Atom (feedparser)."""

from __future__ import annotations

import calendar
import logging
from datetime import UTC, datetime, timedelta

import feedparser

from linotipo.domain.models import Source, source_id_from_url

log = logging.getLogger(__name__)

DEFAULT_FEEDS: tuple[str, ...] = (
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml",
    "https://www.eldiario.es/rss/",
    "https://www.20minutos.es/rss/",
    "https://api2.rtve.es/rss/temas_noticias.xml",
)


class RssNewsSource:
    def __init__(
        self,
        feeds: list[str] | None = None,
        *,
        max_age: timedelta = timedelta(hours=36),
        max_sources: int = 200,
    ) -> None:
        self.feeds = list(feeds) if feeds else list(DEFAULT_FEEDS)
        self.max_age = max_age
        self.max_sources = max_sources

    def fetch(self) -> list[Source]:
        now = datetime.now(tz=UTC)
        cutoff = now - self.max_age
        seen: set[str] = set()
        sources: list[Source] = []
        for feed_url in self.feeds:
            parsed = feedparser.parse(feed_url)
            if parsed.bozo and not parsed.entries:
                log.warning("feed ilegible: %s (%s)", feed_url, parsed.get("bozo_exception"))
                continue
            outlet = (parsed.feed.get("title") or feed_url).strip()
            for entry in parsed.entries:
                link = (entry.get("link") or "").strip()
                title = (entry.get("title") or "").strip()
                if not link or not title:
                    continue
                published = _entry_datetime(entry) or now
                if published < cutoff:
                    continue
                source_id = source_id_from_url(link)
                if source_id in seen:
                    continue
                seen.add(source_id)
                try:
                    sources.append(
                        Source(
                            id=source_id,
                            outlet=outlet,
                            title=title,
                            url=link,  # type: ignore[arg-type]
                            published_at=published,
                        )
                    )
                except ValueError as exc:
                    log.debug("entrada descartada %s: %s", link, exc)
        sources.sort(key=lambda s: s.published_at, reverse=True)
        return sources[: self.max_sources]


def _entry_datetime(entry: feedparser.FeedParserDict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime.fromtimestamp(calendar.timegm(value), tz=UTC)
    return None
