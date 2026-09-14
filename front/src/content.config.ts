import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { EditionSchema } from "./schemas/edition";

/** Cada `editions/YYYY-MM-DD.json` es una entrada cuyo id es la fecha. */
const editions = defineCollection({
  loader: glob({
    pattern: "*.json",
    base: "../editions",
    generateId: ({ entry }) => entry.replace(/\.json$/, ""),
  }),
  schema: EditionSchema,
});

export const collections = { editions };
