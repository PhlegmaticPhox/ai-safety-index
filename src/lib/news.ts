/**
 * Category vocabulary for the news feed.
 *
 * Mirrors CATEGORY_ORDER and CATEGORY_LABELS in etl/fetch_news.py. Two copies of
 * a list is a drift risk, so scripts/check-lib.mjs asserts that every category
 * appearing in the data has an entry here and fails the build if one does not.
 */

export interface NewsRecord {
  title: string;
  snippet: string;
  url: string;
  date: string;
  publisher: string;
  jurisdiction: string;
  /** Coarse class: government publication, research preprint, reported incident. */
  kind: string;
  /** The source's own document type, where it has one. Federal Register only today. */
  doc_type: string;
  categories: string[];
  matched_terms: Record<string, string[]>;
  source_id: string;
}

export interface Category {
  slug: string;
  label: string;
  /** What this category means, shown at the head of its own page. */
  blurb: string;
}

export const CATEGORIES: Category[] = [
  {
    slug: "safety",
    label: "AI Safety",
    blurb:
      "Risk, harm, misuse, evaluation and things that have already gone wrong. Includes " +
      "reported incidents, which are reported rather than sampled: an absence of incidents " +
      "in a country usually means an absence of reporting.",
  },
  {
    slug: "alignment",
    label: "AI Alignment",
    blurb:
      "Getting a model to do what was intended: interpretability, reward modelling, " +
      "oversight, deception and specification. Mostly preprints, which are not peer " +
      "reviewed.",
  },
  {
    slug: "policy",
    label: "AI Policy",
    blurb:
      "Law being made or applied. Bills, statutes, consultations, executive orders, " +
      "enforcement and court decisions. Departmental communications are political " +
      "statements about policy, not neutral descriptions of it.",
  },
  {
    slug: "governance",
    label: "AI Governance",
    blurb:
      "The machinery around the law: standards, frameworks, audits, assurance, " +
      "procurement, institutes and who supervises whom.",
  },
  {
    slug: "progress",
    label: "AI Progress",
    blurb:
      "Capability and how it is built. Benchmarks, training, compute, scaling, releases " +
      "and what models can newly do.",
  },
  {
    slug: "general",
    label: "AI",
    blurb:
      "About AI and nothing narrower. Items land here when no category rule matched, " +
      "which is common for funding announcements and ministerial visits. It is a real " +
      "answer, not a failure to classify.",
  },
];

export const CATEGORY_BY_SLUG = new Map(CATEGORIES.map((c) => [c.slug, c]));

export function labelFor(slug: string): string {
  return CATEGORY_BY_SLUG.get(slug)?.label ?? slug;
}

/** Newest first, with a stable tiebreak so the order does not churn between builds. */
export function byDateDesc(a: NewsRecord, b: NewsRecord): number {
  return b.date.localeCompare(a.date) || a.title.localeCompare(b.title);
}
