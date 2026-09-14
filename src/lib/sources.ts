// The import attribute is required by Node's own ESM loader, and is what lets
// scripts/check-lib.mjs import this module directly to test the licence guard.
// Vite honours it too, so the site build is unaffected.
import sourcesFile from "../../data/sources.json" with { type: "json" };

export type Redistribution =
  | "permitted"
  | "permitted-with-attribution"
  | "share-alike"
  | "no-derivatives"
  | "prohibited";

export interface Source {
  name: string;
  publisher: string;
  publisher_url: string;
  landing_page: string;
  url: string | null;
  format: string | null;
  licence: string;
  licence_url: string;
  attribution: string;
  redistribution: Redistribution;
  cadence: string | null;
  caveats: string;
}

export interface Dataset<T = Record<string, unknown>> {
  dataset: string;
  generated: string;
  retrieved: string;
  sources: string[];
  unit: string | null;
  notes: string | null;
  count: number;
  records: T[];
}

const sources = sourcesFile.sources as unknown as Record<string, Source>;

/** Licence states that must never reach a rendered chart. Mirrors etl/common.py. */
const BLOCKED: ReadonlySet<Redistribution> = new Set(["prohibited", "no-derivatives"]);

export function getSource(id: string): Source {
  const source = sources[id];
  if (!source) {
    throw new Error(
      `Unknown source_id "${id}". Register it in data/sources.json so its licence ` +
        `travels with its data.`,
    );
  }
  return source;
}

/**
 * Fails the build if a dataset would be rendered in breach of its source licence.
 *
 * The Python ETL guards the write; this guards the render. Both ends, because a
 * dataset can also be hand-authored or imported without passing through the ETL.
 */
export function assertRenderable(...ids: string[]): void {
  for (const id of ids) {
    const source = getSource(id);
    if (BLOCKED.has(source.redistribution)) {
      throw new Error(
        `Source "${id}" (${source.publisher}) is marked redistribution=` +
          `"${source.redistribution}" and must not be rendered.\n` +
          `  Licence: ${source.licence}\n  ${source.caveats}\n` +
          `Link out to ${source.landing_page} instead.`,
      );
    }
  }
}

/** Every source a page cites, deduplicated, for the page footer. */
export function attributionsFor(...ids: string[]): Array<Source & { id: string }> {
  return [...new Set(ids)].map((id) => ({ id, ...getSource(id) }));
}

/** "3 days ago" - so a reader can see staleness without doing date arithmetic. */
export function freshness(iso: string): { label: string; stale: boolean } {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  const stale = days > 45;
  if (days <= 0) return { label: "today", stale };
  if (days === 1) return { label: "yesterday", stale };
  if (days < 30) return { label: `${days} days ago`, stale };
  const months = Math.floor(days / 30);
  return { label: months === 1 ? "a month ago" : `${months} months ago`, stale };
}

export { sources };
