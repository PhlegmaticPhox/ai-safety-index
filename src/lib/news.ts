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
      "which is common for funding announcements and ministerial visits.",
  },
];

export const CATEGORY_BY_SLUG = new Map(CATEGORIES.map((c) => [c.slug, c]));

export function labelFor(slug: string): string {
  return CATEGORY_BY_SLUG.get(slug)?.label ?? slug;
}

/** The only URL schemes that may reach an href. Mirrors SAFE_SCHEMES in etl/fetch_news.py. */
const SAFE_SCHEMES: ReadonlySet<string> = new Set(["http:", "https:"]);

/**
 * Is this a URL we are willing to put in an href?
 *
 * The render-side half of the check in `etl/fetch_news.py:_safe_url`. Both ends,
 * for the same reason the licence guard has both ends: `data/processed/news-feed.json`
 * is a committed file, it can be hand-edited, and a future importer might not run
 * the ETL at all.
 *
 * The thing this is actually stopping: Astro escapes an attribute's VALUE, which
 * leaves "javascript:alert(1)" completely intact, because there is no character
 * in it that escaping touches. A feed item carrying one would be live script in
 * this site's own origin as soon as a reader clicked the headline.
 *
 * `new URL()` is the parser here rather than a regex, because it is the same
 * parsing the browser will do, and a regex that disagrees with the browser is
 * the whole bug class. Plain http: stays allowed: a good many primary sources
 * are published over it, and the risk being managed is the scheme, not the
 * transport.
 */
export function isSafeUrl(raw: string | null | undefined): boolean {
  if (!raw) return false;
  try {
    // No base argument on purpose: a relative or protocol-relative URL must
    // throw rather than silently resolving against some assumed origin.
    const url = new URL(raw.trim());
    return SAFE_SCHEMES.has(url.protocol) && url.host !== "";
  } catch {
    return false;
  }
}

/** Newest first, with a stable tiebreak so the order does not churn between builds. */
export function byDateDesc(a: NewsRecord, b: NewsRecord): number {
  return b.date.localeCompare(a.date) || a.title.localeCompare(b.title);
}
