/**
 * Every class used on a page must have a rule the page can actually see.
 *
 * Astro scopes a page's <style> to that page. A class defined inside one page
 * and used by a second has no rule at all on the second, and the failure is
 * silent: the element renders with its initial values and nothing in the markup
 * looks wrong. An SVG <text> that way renders black, which on this site's ground
 * is invisible. That is exactly how the capability page's axis labels went
 * missing, and it is the reason the house rule says shared furniture belongs in
 * global.css.
 *
 * So: for every .astro file, collect the classes its markup uses, subtract the
 * ones its own <style> defines, subtract the ones global.css defines, and report
 * whatever is left. Classes that are only ever set from data are not knowable
 * here, so a small allowlist carries them.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

/* fileURLToPath, not .pathname: this repo's directory has a space in it, and a
   URL pathname keeps it percent-encoded. */
const ROOT = fileURLToPath(new URL("..", import.meta.url));
const SRC = join(ROOT, "src");

/* Set from data or by another component, so no rule is expected in this file. */
const ALLOW = new Set([
  "astro-route-announcer",
  /* Structural hooks with nothing to style: they group children for the markup's
     sake and inherit everything. Listed rather than given an empty rule, so the
     absence is deliberate and visible. */
  "feed__body",
  "prov__val",
]);

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith(".astro") ? [p] : [];
  });
}

/** Class names a stylesheet defines, from its selectors only. */
function defined(css) {
  const out = new Set();
  // Strip declaration blocks so property values cannot look like selectors.
  const selectorsOnly = css.replace(/\{[^{}]*\}/g, "{}");
  for (const m of selectorsOnly.matchAll(/\.(-?[_a-zA-Z][\w-]*)/g)) out.add(m[1]);
  return out;
}

/** Class names markup uses, including every branch of a class:list or template. */
function used(markup) {
  const out = new Set();
  const attr = /\bclass(?:=|:list=)\s*(?:"([^"]*)"|'([^']*)'|\{([^}]*)\})/g;
  for (const m of markup.matchAll(attr)) {
    const raw = m[1] ?? m[2] ?? m[3] ?? "";
    // Inside an expression, only bare quoted strings are real class names.
    // A quoted string on the right of a comparison is a value being tested,
    // not a class name, so drop those before collecting.
    const text = m[3] !== undefined
      ? [...raw.replace(/[=!]==?\s*["'`][^"'`]*["'`]/g, "").matchAll(/["'`]([^"'`]*)["'`]/g)]
          .map((q) => q[1])
          .join(" ")
      : raw;
    for (const cls of text.split(/[\s{}?:,()]+/)) {
      if (/^-?[_a-zA-Z][\w-]*$/.test(cls)) out.add(cls);
    }
  }
  return out;
}

/* Own file plus global.css, and nothing else. A component's scoped style applies
   to that component alone, so it must not satisfy a class used on a page: that
   is the exact mistake this check exists to catch. */
const globalCss = defined(readFileSync(join(SRC, "styles", "global.css"), "utf8"));

let orphans = 0;
for (const file of walk(SRC)) {
  const text = readFileSync(file, "utf8");
  const styleBlocks = [...text.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)]
    .map((m) => m[1])
    .join("\n");
  const markup = text.replace(/<style[^>]*>[\s\S]*?<\/style>/g, "");

  const own = defined(styleBlocks);
  const missing = [...used(markup)].filter(
    (c) => !own.has(c) && !globalCss.has(c) && !ALLOW.has(c),
  );

  if (missing.length) {
    orphans += missing.length;
    console.error(`  ${relative(ROOT, file)}: ${missing.sort().join(", ")}`);
  }
}

if (orphans) {
  console.error(
    `\ncheck-orphan-classes.mjs FAILED: ${orphans} class(es) used with no rule in scope.\n` +
      `Move shared furniture to src/styles/global.css.`,
  );
  process.exit(1);
}
console.log("check-orphan-classes.mjs passed: every class used has a rule in scope");
