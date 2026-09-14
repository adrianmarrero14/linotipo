import { getCollection, type CollectionEntry } from "astro:content";
import type { Edition, Source } from "../schemas/edition";

export type EditionEntry = CollectionEntry<"editions">;

/** Todas las ediciones, de la más reciente a la más antigua. */
export async function getEditions(): Promise<EditionEntry[]> {
  const entries = await getCollection("editions");
  return entries.sort((a, b) => (a.data.date < b.data.date ? 1 : -1));
}

export async function getLatestEdition(): Promise<EditionEntry | undefined> {
  const [latest] = await getEditions();
  return latest;
}

export function sourceMap(edition: Edition): Map<string, Source> {
  return new Map(edition.sources.map((s) => [s.id, s]));
}

export function articleCount(edition: Edition): number {
  return edition.sections.reduce((n, s) => n + s.articles.length, 0);
}

const longDate = new Intl.DateTimeFormat("es-ES", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const shortDate = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

const dateTime = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Europe/Madrid",
});

/** "lunes, 14 de septiembre de 2026" */
export function formatLongDate(isoDate: string): string {
  return longDate.format(new Date(`${isoDate}T00:00:00Z`));
}

/** "14 de septiembre de 2026" */
export function formatShortDate(isoDate: string): string {
  return shortDate.format(new Date(`${isoDate}T00:00:00Z`));
}

/** "14 sept, 06:00" (hora peninsular) */
export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso));
}

export function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}
