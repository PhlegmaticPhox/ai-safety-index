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
import { createHash } from "node:crypto";
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
  /* Astro emits directory-style routes as <route>/index.html, and the slashed
     form is the only one registered here. Cloudflare does serve the unslashed
     form, but by 307 to this one, so registering it too made every internal
     link to a redirect look served: that tolerance is what let 31 hrefs to
     /methodology/governance-readiness ship without tripping CI. */
  if (url.endsWith("/index.html")) {
    served.add(url.replace(/index\.html$/, ""));
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
const EM = "\u2014";
const EN = "\u2013";
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

/* Where an outbound link may land: a publisher's page or its document, never a
   spreadsheet or a shared-document host.

   Epoch AI's site download carries a Google Sheets link per data centre, its
   working calculations, and the /datacentres/ list linked all 93 of them. A
   reader clicking a site's name landed in a spreadsheet editor. The link now
   goes to Epoch's page for the site, and this is what stops a column like that
   one being wired to an href again, from any source, on any page. */
const DOCUMENT_HOSTS = /^https?:\/\/(?:[^/]+\.)?(?:docs\.google\.com|drive\.google\.com|sheets\.google\.com|onedrive\.live\.com|1drv\.ms|sharepoint\.com|dropbox\.com|airtable\.com)(?:[/:?#]|$)/i;
const SPREADSHEET_FILE = /\.(?:xlsx?|xlsm|ods|csv|tsv)(?:[?#]|$)/i;
const documentHrefs = [];
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const [, raw] of html.matchAll(HREF)) {
    if (DOCUMENT_HOSTS.test(raw) || SPREADSHEET_FILE.test(raw)) {
      documentHrefs.push(`${relative(DIST, page)}: ${raw.slice(0, 100)}`);
    }
  }
}
assert.deepEqual(
  documentHrefs,
  [],
  `${documentHrefs.length} href(s) in the built site open a spreadsheet or a shared ` +
    `document:\n  ${documentHrefs.slice(0, 20).join("\n  ")}\n` +
    `Link the publisher's page for the record instead.`,
);

/* Zero client JavaScript in OUR OWN output, asserted rather than assumed.

   It is a design rule, and the Content-Security-Policy in public/_headers is
   built on it: script-src names exactly one external origin and nothing else, so
   a script this build emitted would be refused in production and nowhere else.

   The one script on a live page is Cloudflare's analytics beacon, which is
   injected at the edge AFTER the build and therefore never appears in dist. That
   is the reason this check reads dist rather than the live site, and also the
   reason it could not have caught that beacon: it was missed for exactly as long
   as it was, because nothing in this repository puts it there. If that ever
   matters again, the check is `curl` with a browser User-Agent, not this file. */
/* One exception, and it is not JavaScript. A type="application/ld+json" block is
   data: the parser never prepares it as script, nothing in it executes, and CSP's
   script-src does not reach it, so the policy in public/_headers is unchanged.
   Matched by its type attribute rather than by the whole opening tag, so an
   attribute reordering in a future Astro release cannot silently fail the build.
   Base.astro escapes < to \u003c inside the JSON, so no <script can hide in the
   payload, and scripts/check-seo.mjs asserts every such block parses. */
const LD_JSON = /<script\b[^>]*\btype="application\/ld\+json"[^>]*>[\s\S]*?<\/script>/gi;

/* And one script that is JavaScript: ZoomMap's mouse controls, added on the
   owner's instruction. It is inline, and public/_headers allows it by the
   SHA-256 of its exact text, so the rule is now "every executable script in
   dist is inline and its hash is in the policy". A script with a src, or an
   inline one whose hash the policy does not carry, fails here: in production
   the browser would refuse it, and the page would lose the behaviour silently.
   The hash is computed over the bytes between the tags, which is what a
   browser hashes. */
const HEADERS = readFileSync("public/_headers", "utf8");
const cspLine = HEADERS.split("\n").find((line) => /^\s*Content-Security-Policy:/.test(line)) ?? "";
const scriptSrc = (cspLine.match(/script-src([^;]*)/) ?? ["", ""])[1];
const allowedHashes = new Set([...scriptSrc.matchAll(/'sha256-([A-Za-z0-9+/=]+)'/g)].map((m) => m[1]));
const SCRIPT = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
const scripted = [];
const hashesUsed = new Set();
for (const page of pages) {
  const html = readFileSync(page, "utf8").replace(LD_JSON, "");
  for (const [, attrs, body] of html.matchAll(SCRIPT)) {
    const hash = createHash("sha256").update(body, "utf8").digest("base64");
    if (/\bsrc=/i.test(attrs)) {
      scripted.push(`${relative(DIST, page)}: a script with a src (${attrs.trim()})`);
    } else if (!allowedHashes.has(hash)) {
      scripted.push(`${relative(DIST, page)}: an inline script whose hash 'sha256-${hash}' is not in script-src`);
    } else {
      hashesUsed.add(hash);
    }
  }
}
/* A hash left in the policy after its script changed is an allowance for code
   that no longer exists, and would let that old text run if it ever came back. */
const staleHashes = [...allowedHashes].filter((h) => !hashesUsed.has(h));
assert.deepEqual(
  staleHashes,
  [],
  `script-src in public/_headers allows ${staleHashes.length} hash(es) no script in dist has:\n  ` +
    `${staleHashes.map((h) => `'sha256-${h}'`).join("\n  ")}\nRemove them.`,
);

/* The other half of the same rule, and until now it was only ever asserted by
   the comment in public/_headers that claims this file asserts it. A script tag
   is how JavaScript gets onto a page; a .js file in dist is how it gets into the
   deployment, and a build tool can emit one without any page referencing it yet. */
const emittedJs = files
  .filter((file) => /\.(js|mjs|map)$/.test(file))
  .map((file) => relative(DIST, file));

assert.deepEqual(
  emittedJs,
  [],
  `${emittedJs.length} JavaScript file(s) in dist:\n  ${emittedJs.join("\n  ")}\n` +
    `The build is supposed to emit none, and public/_headers cites that fact as the ` +
    `reason default-src is 'none'.`,
);

assert.deepEqual(
  scripted,
  [],
  `${scripted.length} script(s) the Content-Security-Policy would refuse:\n  ${scripted.join("\n  ")}\n` +
    `The build may emit only inline scripts whose SHA-256 is listed in script-src in ` +
    `public/_headers (ld+json data blocks excepted), and /privacy/ and /about/ ` +
    `describe the one that is. If this is ZoomMap's script after an edit, put the ` +
    `hash printed above into public/_headers in place of the old one. Anything ` +
    `else is accidental, or the policy, this check and those pages change together.`,
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

/* Every table sits inside a .scroll-x box.

   A table is the one thing on this site whose width is set by its content rather
   than by its container, so a table outside a scroll box does not clip, wrap or
   shrink: it widens the document. On a phone that is not a scrollbar, it is the
   whole page zooming out and panning under two fingers, which is how it was
   reported and why it went unnoticed for so long - every page looks correct on a
   laptop, where there is room.

   /adoption/ shipped four of them. Three carried `wrap-cell`, a class that was
   only ever styled inside .grid-table, so the cells silently kept nowrap and one
   NACE activity label set a 1060px column inside a 390px screen.

   Structural, not visual: it cannot know how wide a table renders, only that the
   box which would contain it is there. That is the part that was missing, and it
   is the part a new page forgets. */
const TAG = /<(\/?)(div|table)\b([^>]*)>/gi;
const unboxed = [];
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  const stack = [];
  for (const [, closing, tag, attrs] of html.matchAll(TAG)) {
    const name = tag.toLowerCase();
    if (name === "table") {
      if (!stack.some(Boolean)) unboxed.push(relative(DIST, page));
      continue;
    }
    if (closing) stack.pop();
    // Self-closing divs are not a thing in HTML, so every <div> opens a level.
    else stack.push(/\bclass="[^"]*\bscroll-x\b/.test(attrs));
  }
}

assert.deepEqual(
  [...new Set(unboxed)],
  [],
  `${new Set(unboxed).size} page(s) render a <table> outside a .scroll-x box:\n  ` +
    [...new Set(unboxed)].join("\n  ") +
    `\nWide content scrolls inside its own box; the body never scrolls sideways. ` +
    `Wrap the table in <div class="scroll-x">.`,
);

/* Every SVG is either decorative or named.

   Charts here render to SVG at build time, so a figure's meaning is path
   geometry that nothing can read. The site's rule is that a chart carries
   role="img" with an aria-label and anything decorative carries
   aria-hidden="true". All 328 of them already follow it and nothing enforced
   it, so a new chart could ship nameless and look perfect. */
const SVG_TAG = /<svg\b[^>]*>/gi;
const namelessSvg = [];
for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const [tag] of html.matchAll(SVG_TAG)) {
    if (/aria-hidden="true"/.test(tag)) continue;
    if (/role="(img|presentation)"/.test(tag) && !/role="img"/.test(tag)) continue;
    if (/role="img"/.test(tag) && /aria-label="[^"]+"/.test(tag)) continue;
    namelessSvg.push(`${relative(DIST, page)}: ${tag.slice(0, 120)}`);
  }
}

assert.deepEqual(
  namelessSvg,
  [],
  `${namelessSvg.length} <svg> element(s) are neither hidden from assistive technology ` +
    `nor role="img" with an aria-label:\n  ${namelessSvg.join("\n  ")}\n` +
    `A chart with no accessible name is a picture of numbers that nothing can read.`,
);

console.log(
  `check-internal-links.mjs passed: ${checked} internal links, 0 forbidden dashes, ` +
    `${pages.length} pages, canonical origin ${origin}, no stale name, no noindex, ` +
    `no unsafe href schemes, no spreadsheet or shared-document links, no script the CSP would refuse (${hashesUsed.size} hashed inline), ` +
    `no JavaScript files, every table in a scroll box, ` +
    `every SVG either hidden or named`,
);
