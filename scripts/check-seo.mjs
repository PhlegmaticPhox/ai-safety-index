/**
 * Search-facing invariants, against the BUILT site.
 *
 * Two tiers, and the split is the point. FATAL is structure: things that are
 * either right or broken, with no editorial judgement in them, and every one of
 * which silently costs the page its place in an index. WARNING is editorial:
 * title and description length, a one-word title, a repeated h1. Those are
 * opinions with a defensible range, and a build that fails on an opinion is a
 * build somebody switches off.
 *
 * check-internal-links.mjs already covers links, anchors, dashes, href schemes,
 * script tags, canonical ORIGIN, the old name, noindex and table boxes. This
 * file does not repeat any of them.
 *
 *     node scripts/check-seo.mjs
 *
 * Verify it bites: change one page's canonical href to another route and confirm
 * the self-reference assertion names that page; copy one page's <title> onto a
 * second and confirm the uniqueness assertion fires. Then revert both.
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";

const DIST = "dist";

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (full.endsWith(".html")) out.push(full);
  }
  return out;
}

/* The URL path a built file is served at. 404.html is the one file Cloudflare
   serves from an unmatched path rather than from its own, so it is exempt from
   the self-reference rule below and from the sitemap comparison. */
const pathOf = (file) =>
  "/" + relative(DIST, file).split("\\").join("/").replace(/index\.html$/, "");

const meta = (html, re) => [...html.matchAll(re)].map((m) => m[1]);

const pages = walk(DIST).map((file) => {
  const html = readFileSync(file, "utf8");
  /* Every head-level matcher below runs against the head alone, and the reason
     is <title>. SVG has a <title> element too, used here as the accessible name
     of a map shape, and /map/ carries 581 of them across its three maps and the
     scatter: matching the whole document reports "Chad: not in this dataset" as
     a duplicate page title. Scoping to the head is also strictly correct for the
     rest, since a meta or a canonical in the body is not one the parser
     honours. */
  const head = html.slice(0, html.indexOf("</head>"));
  return {
    name: relative(DIST, file).split("\\").join("/"),
    path: pathOf(file),
    is404: file.endsWith("404.html"),
    titles: meta(head, /<title>([^<]*)<\/title>/g),
    descriptions: meta(head, /<meta name="description" content="([^"]*)"/g),
    canonicals: meta(head, /<link rel="canonical" href="([^"]+)"/g),
    ogUrls: meta(head, /<meta property="og:url" content="([^"]+)"/g),
    ogImages: meta(head, /<meta property="og:image" content="([^"]+)"/g),
    twitterCards: meta(head, /<meta name="twitter:card" content="([^"]+)"/g),
    h1s: [...html.matchAll(/<h1[^>]*>([\s\S]*?)<\/h1>/g)].map((m) =>
      m[1].replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim(),
    ),
    ld: [...head.matchAll(/<script[^>]*application\/ld\+json[^>]*>([\s\S]*?)<\/script>/g)].map(
      (m) => m[1],
    ),
  };
});

const fatal = [];
const warn = [];
const seen = (key) => {
  const map = new Map();
  for (const page of pages) {
    for (const value of page[key]) {
      if (!value) continue;
      map.set(value, [...(map.get(value) ?? []), page.name]);
    }
  }
  return map;
};

for (const page of pages) {
  if (page.titles.length !== 1 || !page.titles[0].trim())
    fatal.push(`${page.name}: ${page.titles.length} <title> element(s)`);
  if (page.descriptions.length !== 1 || !page.descriptions[0].trim())
    fatal.push(`${page.name}: ${page.descriptions.length} meta description(s)`);
  if (page.canonicals.length !== 1)
    fatal.push(`${page.name}: ${page.canonicals.length} canonical link(s)`);
  if (page.ogUrls.length !== 1)
    fatal.push(`${page.name}: ${page.ogUrls.length} og:url meta element(s)`);
  if (page.ogImages.length !== 1)
    fatal.push(`${page.name}: ${page.ogImages.length} og:image meta element(s)`);
  if (page.twitterCards.length !== 1)
    fatal.push(`${page.name}: ${page.twitterCards.length} twitter:card meta element(s)`);
  if (page.ld.length !== 1)
    fatal.push(`${page.name}: ${page.ld.length} head-level JSON-LD block(s)`);
  if (page.h1s.length !== 1) fatal.push(`${page.name}: ${page.h1s.length} <h1> element(s)`);

  /* A canonical must name its own page. One pointing at a sibling deindexes this
     page while looking perfectly correct in the markup, and the origin check in
     check-internal-links.mjs passes it without complaint. */
  if (page.canonicals.length === 1 && !page.is404) {
    const { pathname } = new URL(page.canonicals[0]);
    if (pathname !== page.path)
      fatal.push(`${page.name}: canonical points at ${pathname}, not ${page.path}`);
  }
  if (
    page.ogUrls.length === 1 &&
    page.canonicals.length === 1 &&
    page.ogUrls[0] !== page.canonicals[0]
  )
    fatal.push(`${page.name}: og:url and canonical disagree`);

  /* An og:image naming a file that is not deployed is a broken card everywhere
     it is shared, and nothing else in the build would notice. */
  for (const src of page.ogImages) {
    const { pathname } = new URL(src);
    if (!existsSync(join(DIST, pathname.slice(1))))
      fatal.push(`${page.name}: og:image ${pathname} is not in dist`);
    if (page.twitterCards[0] !== "summary_large_image")
      fatal.push(`${page.name}: og:image present but twitter:card is "${page.twitterCards[0]}"`);
  }

  /* JSON-LD that does not parse is worse than none: it is a block a validator
     reports and a reader never sees. */
  for (const block of page.ld) {
    try {
      JSON.parse(block);
    } catch (error) {
      fatal.push(`${page.name}: JSON-LD does not parse (${error.message})`);
    }
  }

  const title = page.titles[0] ?? "";
  const description = page.descriptions[0] ?? "";
  if (title.length > 60 || title.length < 20)
    warn.push(`${page.name}: title is ${title.length} chars (aim 20 to 60)`);
  if (description.length > 160 || description.length < 70)
    warn.push(`${page.name}: description is ${description.length} chars (aim 70 to 160)`);
  if (!/\s/.test(title.split(" | ")[0]))
    warn.push(`${page.name}: title is one word before the site name ("${title}")`);
}

for (const [title, where] of seen("titles"))
  if (where.length > 1) fatal.push(`title "${title}" is used by ${where.join(", ")}`);
for (const [description, where] of seen("descriptions"))
  if (where.length > 1)
    fatal.push(`description "${description.slice(0, 50)}..." is used by ${where.join(", ")}`);
for (const [h1, where] of seen("h1s"))
  if (where.length > 1) warn.push(`h1 "${h1}" is used by ${where.join(", ")}`);

/* The sitemap is the crawl budget. A page missing from it is a page found only
   by link, and a page in it that is not built is a 404 advertised to Google. */
const sitemap = readFileSync(join(DIST, "sitemap-0.xml"), "utf8");
const listed = new Set(
  [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => new URL(m[1]).pathname),
);
const indexable = new Set(pages.filter((p) => !p.is404).map((p) => p.path));
for (const path of indexable)
  if (!listed.has(path)) fatal.push(`${path} is built but not in the sitemap`);
for (const path of listed)
  if (!indexable.has(path)) fatal.push(`${path} is in the sitemap but not built`);

/* robots.txt is the one file whose absence is invisible from inside the build:
   every page renders perfectly and the sitemap is simply never found. */
const robotsPath = join(DIST, "robots.txt");
assert.ok(existsSync(robotsPath), "dist/robots.txt is missing");
const robots = readFileSync(robotsPath, "utf8");
const sitemapLine = robots.match(/^Sitemap:\s*(\S+)/im);
if (!sitemapLine) fatal.push("robots.txt names no Sitemap");
else if (!existsSync(join(DIST, new URL(sitemapLine[1]).pathname.slice(1))))
  fatal.push(`robots.txt points at ${sitemapLine[1]}, which is not in dist`);

if (warn.length > 0) console.warn(`check-seo.mjs, ${warn.length} warning(s):\n  ${warn.join("\n  ")}`);

assert.deepEqual(
  fatal,
  [],
  `${fatal.length} search-facing defect(s):\n  ${fatal.join("\n  ")}\n` +
    `Each of these costs a page its place in an index while the page itself renders perfectly.`,
);

console.log(
  `check-seo.mjs passed: ${pages.length} pages, unique titles and descriptions, ` +
    `self-referential canonicals on ${indexable.size} indexable pages, ` +
    `required social metadata and JSON-LD present, sitemap matches the build, robots.txt names it, ` +
    `${warn.length} warning(s)`,
);
