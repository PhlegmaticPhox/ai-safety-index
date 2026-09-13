/**
 * Checks that run against the BUILT site, because some things are only wrong
 * once rendered.
 *
 * 1. Every internal link and same-page anchor must resolve. A dead internal
 *    link is the failure this site is least able to afford: the whole argument
 *    is that you can click through to where a number came from, and a
 *    provenance popover pointing at a 404 is worse than one pointing nowhere.
 *
 * 2. No em or en dashes anywhere in the output. The house rule is that the only
 *    permitted dash is the hyphen, and it applies to data as much as to prose.
 *    This caught an en dash inside an Epoch organisation name that had reached a
 *    chart tooltip, which no amount of reading the source would have found.
 *
 *     node scripts/check-internal-links.mjs
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = "dist";

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

const files = walk(DIST);
const pages = files.filter((f) => f.endsWith(".html"));

/** Every path dist can actually serve, as a set of URL paths. */
const served = new Set();
for (const file of files) {
  const url = "/" + relative(DIST, file).split("\\").join("/");
  served.add(url);
  // Astro emits directory-style routes as <route>/index.html.
  if (url.endsWith("/index.html")) {
    served.add(url.replace(/index\.html$/, ""));
    served.add(url.replace(/\/index\.html$/, ""));
  }
}

const HREF = /href="([^"]+)"/g;
const broken = [];
let checked = 0;

for (const page of pages) {
  const html = readFileSync(page, "utf8");
  const from = "/" + relative(DIST, page).split("\\").join("/");

  // Fragment targets present on this page, for same-page anchor checking.
  const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]));

  for (const [, raw] of html.matchAll(HREF)) {
    if (/^(https?:|mailto:|tel:|data:|#)/.test(raw)) {
      // A bare fragment must exist on the page that carries it.
      if (raw.startsWith("#") && raw.length > 1 && !ids.has(raw.slice(1))) {
        broken.push(`${from} -> ${raw} (no such id on this page)`);
      }
      continue;
    }
    if (!raw.startsWith("/")) continue; // relative asset paths resolve by position

    checked += 1;
    const [path] = raw.split("#");
    if (path === "" || served.has(path) || served.has(path + "index.html")) continue;
    broken.push(`${from} -> ${raw}`);
  }
}

assert.deepEqual(
  broken,
  [],
  `${broken.length} internal link(s) point at nothing:\n  ${broken.join("\n  ")}`,
);

/* Dash audit. Written as escapes rather than literal characters, for the same
   reason the Python side does: a text-level sweep must not be able to reach the
   thing that detects the problem. */
const EM = "—";
const EN = "–";
const dashed = [];
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  const count = html.split(EM).length - 1 + (html.split(EN).length - 1);
  if (count > 0) {
    const index = Math.max(html.indexOf(EM), html.indexOf(EN));
    const context = html.slice(Math.max(0, index - 50), index + 20);
    dashed.push(`${relative(DIST, page)}: ${count} (near "${context}")`);
  }
}
assert.deepEqual(
  dashed,
  [],
  "em or en dashes in the built site:\n  " +
    dashed.join("\n  ") +
    "\nThe only permitted dash is the hyphen. If this came from source data, " +
    "normalise it in the ETL rather than in the page.",
);

console.log(
  `check-internal-links.mjs passed: ${checked} internal links, 0 forbidden dashes, ` +
    `${pages.length} pages`,
);
