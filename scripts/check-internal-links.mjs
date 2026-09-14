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

/* Href scheme audit, against the BUILT pages.

   Most hrefs on this site are ours. A few hundred are not: the news feed prints
   a link supplied by somebody else's RSS, and "javascript:alert(1)" passes
   through HTML attribute escaping completely unaltered, because there is no
   character in it that escaping touches.

   etl/fetch_news.py checks the scheme on the way in, and each component checks
   again on the way out. This is the check that does not care how many components
   there are. It exists because the per-component version was written first and
   was wrong: NewsList.astro was guarded while the homepage and /alignment/ both
   rendered the same records with their own markup and their own unguarded href.
   A sabotage test found it; this is what would have found it at build time. A
   fourth renderer added next year is covered without anyone remembering. */
const SAFE_SCHEMES = /^(https?:\/\/|\/|#|mailto:)/;
const unsafeHrefs = [];
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const [, raw] of html.matchAll(HREF)) {
    if (raw === "" || SAFE_SCHEMES.test(raw)) continue;
    // A relative path with no scheme is fine; anything with a colon before the
    // first slash is claiming to be a scheme, and only http(s) and mailto may.
    const colon = raw.indexOf(":");
    const slash = raw.indexOf("/");
    if (colon === -1 || (slash !== -1 && slash < colon)) continue;
    unsafeHrefs.push(`${relative(DIST, page)}: ${raw.slice(0, 80)}`);
  }
}
assert.deepEqual(
  unsafeHrefs,
  [],
  `${unsafeHrefs.length} href(s) in the built site use a scheme that is not http, ` +
    `https or mailto:\n  ${unsafeHrefs.join("\n  ")}\n` +
    `A javascript: or data: URL here is script running in this site's origin. ` +
    `If it came from the news feed, the scheme check in the renderer is missing ` +
    `on whichever page this is.`,
);

/* Zero client JavaScript, asserted rather than assumed.

   It is a design rule, it is stated on /privacy/, and the Content-Security-Policy
   in public/_headers is built on it: default-src 'none' is only safe to ship
   because nothing here needs a script. If a dependency or an integration ever
   starts emitting one, the page would silently break under that policy in
   production and nowhere else. Cheaper to fail here. */
const scripted = pages
  .filter((page) => /<script[\s>]/i.test(readFileSync(page, "utf8")))
  .map((page) => relative(DIST, page));

assert.deepEqual(
  scripted,
  [],
  `${scripted.length} page(s) contain a <script> tag:\n  ${scripted.join("\n  ")}\n` +
    `The site ships no client JavaScript, /privacy/ says so, and the CSP in ` +
    `public/_headers sends default-src 'none'. Either this is accidental, or all ` +
    `three of those need to change together.`,
);

/* Canonical origin.

   Every canonical link, og:url and sitemap entry is built from one configured
   origin, and if that origin is malformed every one of them is wrong at once
   while the page itself renders perfectly. It shipped: a build variable holding
   the scheme twice produced `https://https/` on every page of the live site, and
   a sitemap advertising thirty-two URLs on a host that does not exist.

   The test is deliberately weak on purpose. It does not know the real domain, so
   it checks the only thing that is knowable from the output alone: that the host
   is a plausible hostname, and that every page agrees on it. `https://https/`
   fails because "https" is a single label with no dot. localhost passes, because
   a local build is not a deployment. */
const origins = new Map();
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const [, raw] of html.matchAll(
    /(?:rel="canonical" href|property="og:url" content)="([^"]+)"/g,
  )) {
    let url;
    try {
      url = new URL(raw);
    } catch {
      origins.set(`unparseable: ${raw}`, relative(DIST, page));
      continue;
    }
    origins.set(url.origin, relative(DIST, page));
  }
}

assert.equal(
  origins.size,
  1,
  `pages disagree about this site's own origin, which means one of them is wrong:\n  ` +
    [...origins].map(([origin, page]) => `${origin}  (e.g. ${page})`).join("\n  "),
);

const [origin] = [...origins.keys()];
const { hostname } = new URL(origin);
assert.ok(
  hostname === "localhost" || (hostname.includes(".") && !hostname.endsWith(".")),
  `every canonical link and sitemap entry on this build points at "${origin}", and ` +
    `"${hostname}" is not a hostname. The site origin in astro.config.mjs is malformed; ` +
    `a value carrying the scheme twice produces exactly this.`,
);

/* The old name.

   The site was renamed from AI Safety Index to AI Safety Tracker, partly for the
   domain and partly because the Future of Life Institute publishes an
   established annual report under the old name. A rename that misses one footer
   or one og:site_name is the kind of thing nobody notices for months.

   The word "index" on its own is fine and deliberate: it describes what the site
   is, and our own datasets are still called indexes. Only the full former name is
   banned. If a page ever needs to cite FLI's report by name, this check is what
   will stop it, and the right fix then is to narrow the check, not to delete it. */
const OLD_NAME = "AI Safety Index";
const stale = pages
  .filter((page) => readFileSync(page, "utf8").includes(OLD_NAME))
  .map((page) => relative(DIST, page));

assert.deepEqual(
  stale,
  [],
  `${stale.length} page(s) still carry the old site name "${OLD_NAME}":\n  ` +
    stale.join("\n  ") +
    `\nThe site is called AI Safety Tracker.`,
);

/* The noindex meta is gone and robots.txt invites crawlers, so a stray noindex
   would now silently deindex a live site. */
const noindexed = pages
  .filter((page) => /<meta[^>]+name="robots"[^>]+noindex/i.test(readFileSync(page, "utf8")))
  .map((page) => relative(DIST, page));

assert.deepEqual(
  noindexed,
  [],
  `${noindexed.length} page(s) carry a noindex robots meta:\n  ` +
    noindexed.join("\n  ") +
    `\nThe site is live and meant to be indexed.`,
);

console.log(
  `check-internal-links.mjs passed: ${checked} internal links, 0 forbidden dashes, ` +
    `${pages.length} pages, canonical origin ${origin}, no stale name, no noindex, ` +
    `no unsafe href schemes, no client JavaScript`,
);
