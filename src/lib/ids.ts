/**
 * Deterministic element ids for components that need one per instance.
 *
 * Why this exists rather than Math.random():
 *
 * Provenance and Sparkline each need an id that is unique within a page - a
 * popovertarget that points at two elements does nothing, and two SVG gradients
 * sharing an id make the second chart borrow the first one's fill. Both used
 * Math.random(), which solved uniqueness and broke something more valuable:
 * every build produced different bytes from identical input.
 *
 * That matters here more than it would elsewhere. The site's entire argument is
 * that a reader can check where a number came from. Nondeterministic output
 * removed the only mechanical check on the deployed site itself: you could not
 * hash what Cloudflare serves and compare it against what the repository builds,
 * so a tampered deploy and an ordinary rebuild looked exactly alike. Two clean
 * builds of the same commit should be byte-identical, and now are.
 *
 * A counter is sufficient because Astro renders pages sequentially and renders
 * each page in a single pass, so components are reached in source order and the
 * sequence is fixed by the source rather than by timing. The counter is shared
 * across the whole build, so ids continue rather than restarting per page; that
 * is fine, because uniqueness is only required within a page and continuing is
 * just as deterministic as restarting.
 *
 * What would break it: setting `build.concurrency` above 1 in astro.config.mjs,
 * which would let pages render in parallel and interleave the sequence. Ids
 * would stay unique but would stop being stable between builds. The check that
 * would catch it is two clean builds and a diff of dist/, which is worth running
 * after any build-configuration change.
 */

let counter = 0;

/** Next id in the build-wide sequence. Stable across clean builds of one commit. */
export function nextId(): number {
  return ++counter;
}
