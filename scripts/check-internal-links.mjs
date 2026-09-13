/**
 * Every internal link must point at a page that exists.
 *
 * Runs against dist/ after a build. A dead internal link is the failure mode
 * this site is least able to afford: the whole argument is that you can click
 * through to where a number came from, and a provenance popover linking to a
 * 404 is worse than one linking nowhere.
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

console.log(`check-internal-links.mjs passed: ${checked} internal links across ${pages.length} pages`);
