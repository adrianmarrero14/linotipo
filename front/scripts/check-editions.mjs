#!/usr/bin/env node
/**
 * Valida cada `editions/*.json` contra `schema/edition.schema.json` (exportado desde
 * Pydantic). Si esto pasa y `astro build` (Zod) también, ambos esquemas siguen alineados.
 */
import { readdirSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const schemaPath = resolve(root, "schema", "edition.schema.json");
const editionsDir = resolve(root, "editions");

const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
const validate = ajv.compile(schema);

const files = readdirSync(editionsDir)
  .filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f))
  .sort();

if (files.length === 0) {
  console.error(`No hay ediciones en ${editionsDir}`);
  process.exit(1);
}

/**
 * Reglas que JSON Schema no puede expresar y que Pydantic y Zod sí comprueban:
 * citas a fuentes del catálogo, slugs únicos y como máximo un lead por sección.
 */
function crossChecks(edition) {
  const problems = [];
  const ids = new Set();
  for (const source of edition.sources ?? []) {
    if (ids.has(source.id)) problems.push(`id de fuente duplicado: ${source.id}`);
    ids.add(source.id);
  }
  const slugs = new Set();
  for (const section of edition.sections ?? []) {
    const leads = (section.articles ?? []).filter((a) => a.lead).length;
    if (leads > 1) problems.push(`la sección '${section.key}' tiene ${leads} artículos lead`);
    for (const article of section.articles ?? []) {
      if (slugs.has(article.slug)) problems.push(`slug duplicado: ${article.slug}`);
      slugs.add(article.slug);
      for (const citation of article.citations ?? []) {
        if (!ids.has(citation.source_id)) {
          problems.push(`'${article.slug}' cita una fuente fuera del catálogo: ${citation.source_id}`);
        }
      }
    }
  }
  return problems;
}

let failures = 0;
for (const file of files) {
  const data = JSON.parse(readFileSync(resolve(editionsDir, file), "utf8"));
  const expectedDate = file.replace(/\.json$/, "");
  const problems = [];
  if (!validate(data)) {
    problems.push(...validate.errors.map((e) => `${e.instancePath || "/"} ${e.message}`));
  }
  if (data.date !== expectedDate) {
    problems.push(`el campo date (${data.date}) no coincide con el nombre del fichero`);
  }
  problems.push(...crossChecks(data));
  if (problems.length === 0) {
    console.log(`ok   ${file}`);
  } else {
    failures += 1;
    console.error(`FAIL ${file}`);
    for (const p of problems) console.error(`     ${p}`);
  }
}

if (failures > 0) {
  console.error(`${failures} de ${files.length} ediciones no validan contra ${schemaPath}`);
  process.exit(1);
}
console.log(`${files.length} edición(es) válidas contra schema/edition.schema.json`);
