// The import attribute is required by Node's own ESM loader, and is what lets
// scripts/check-lib.mjs import this module directly to test the licence guard.
// Vite honours it too, so the site build is unaffected.
import sourcesFile from "../../data/sources.json" with { type: "json" };
import statusFile from "../../data/processed/_status.json" with { type: "json" };

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

/**
 * The oldest retrieval date among the datasets a page renders.
 *
 * A masthead date is a floor, not an average: nothing on the page is older than
 * this. Taking the newest would let one freshly refreshed dataset hide a stale
 * one behind it, including past the 45-day stale threshold, which is how
 * /policy/ came to read "reviewed today" above governance scores four days
 * older. Per-dataset dates stay on each figure's own Provenance marker.
 *
 * Lexical sort is safe because every envelope stamp is ISO 8601 written by
 * etl/common.py:utcnow() with a literal +00:00 offset.
 */
export function oldestRetrieved(...datasets: Array<{ retrieved: string }>): string {
  return datasets.map((d) => d.retrieved).sort()[0];
}

/**
 * When the pipeline last confirmed each dataset, from etl/run_all.py.
 *
 * A dataset file is only rewritten when its records change, so its envelope says
 * when the data last MOVED. A source that publishes annually therefore aged on
 * the page every day it was fetched and found identical: /adoption/ read
 * "retrieved 12 days ago" over Eurostat figures fetched that morning. The status
 * file carries the later fact, and the page shows whichever is later.
 */
const confirmedAt: Record<string, string> =
  (statusFile as { datasets?: Record<string, string> }).datasets ?? {};

/**
 * A dataset with `retrieved` moved forward to its last confirmation, if that is
 * later. Never moved back: a confirmation older than the file is ignored.
 * Hand-coded indexes are confirmed at their review date, so this cannot make a
 * review look more recent than it was.
 */
export function confirmed<T>(dataset: Dataset<T>, seen: Record<string, string> = confirmedAt): Dataset<T> {
  const at = seen[dataset.dataset];
  return at && at > dataset.retrieved ? { ...dataset, retrieved: at } : dataset;
}

export { sources };
