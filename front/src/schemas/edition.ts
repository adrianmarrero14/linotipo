/**
 * Esquema Zod del contrato `editions/YYYY-MM-DD.json`.
 *
 * Debe mantenerse equivalente a `back/src/linotipo/domain/models.py`. La CI valida
 * `editions/*.json` contra `schema/edition.schema.json` (exportado desde Pydantic)
 * con `npm run check:editions`, y Astro valida con este esquema en build.
 */
import { z } from "astro/zod";

const slug = z.string().min(1).regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
const isoDate = z.iso.date();
const isoDateTime = z.iso.datetime({ offset: true });

export const SourceSchema = z.object({
  id: z.string().min(1),
  outlet: z.string().min(1),
  title: z.string().min(1),
  url: z.url().min(1).max(2083),
  published_at: isoDateTime,
});

export const CitationSchema = z.object({
  source_id: z.string().min(1),
  quote: z.string().nullable().default(null),
});

export const ArticleSchema = z.object({
  slug,
  headline: z.string().min(1),
  subhead: z.string().nullable().default(null),
  dateline: z.string().nullable().default(null),
  body: z.array(z.string()).min(1),
  citations: z.array(CitationSchema),
  topics: z.array(z.string()).default([]),
  lead: z.boolean().default(false),
});

export const SectionSchema = z
  .object({
    key: slug,
    name: z.string().min(1),
    articles: z.array(ArticleSchema),
  })
  .superRefine((section, ctx) => {
    const leads = section.articles.filter((a) => a.lead);
    if (leads.length > 1) {
      ctx.addIssue({
        code: "custom",
        message: `la sección '${section.key}' tiene más de un artículo lead`,
        path: ["articles"],
      });
    }
  });

export const EditionSchema = z
  .object({
    date: isoDate,
    number: z.number().int().min(1),
    locale: z.string().default("es-ES"),
    region: z.string().default("ES"),
    sections: z.array(SectionSchema),
    sources: z.array(SourceSchema),
    generated_at: isoDateTime,
    pipeline_version: z.string().min(1),
    prompt_version: z.string().min(1),
  })
  .superRefine((edition, ctx) => {
    const ids = new Set<string>();
    for (const source of edition.sources) {
      if (ids.has(source.id)) {
        ctx.addIssue({
          code: "custom",
          message: `id de fuente duplicado: ${source.id}`,
          path: ["sources"],
        });
      }
      ids.add(source.id);
    }
    const slugs = new Set<string>();
    edition.sections.forEach((section, si) => {
      section.articles.forEach((article, ai) => {
        if (slugs.has(article.slug)) {
          ctx.addIssue({
            code: "custom",
            message: `slug duplicado en la edición: ${article.slug}`,
            path: ["sections", si, "articles", ai, "slug"],
          });
        }
        slugs.add(article.slug);
        article.citations.forEach((citation, ci) => {
          if (!ids.has(citation.source_id)) {
            ctx.addIssue({
              code: "custom",
              message: `el artículo '${article.slug}' cita una fuente que no está en el catálogo: ${citation.source_id}`,
              path: ["sections", si, "articles", ai, "citations", ci, "source_id"],
            });
          }
        });
      });
    });
  });

export type Source = z.infer<typeof SourceSchema>;
export type Citation = z.infer<typeof CitationSchema>;
export type Article = z.infer<typeof ArticleSchema>;
export type Section = z.infer<typeof SectionSchema>;
export type Edition = z.infer<typeof EditionSchema>;
