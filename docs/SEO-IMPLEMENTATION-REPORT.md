# AI Safety Tracker SEO Implementation Report

Report date: 19 September 2026

## Executive Summary

The site now has search-specific page titles, unique descriptions, canonical URLs, complete Open Graph and Twitter/X cards, one JSON-LD graph per page, Dataset markup on two first-party dataset landing pages, visible and structured breadcrumbs on 13 deep routes, and automated SEO regression checks. Internal URL forms were normalised, the sitemap was checked against the complete indexable build, and mobile overflow and font-swap layout shift were fixed.

The baseline was already strong: 34 indexable static routes, unique titles and descriptions, one H1 per page, crawlable HTML, a valid robots file and sitemap, accessible SVG naming, no client runtime JavaScript, and citation-first source attribution. No factual dataset values, citations, rankings, methods, licences, retrieval dates, or public URL slugs were changed for SEO.

Production was not changed. Nothing was pushed, merged, deployed, submitted to a search engine, or changed in DNS or Cloudflare. Google Search Console setup, post-deployment structured-data tests, social preview tests, sitemap submission, URL Inspection, and field Core Web Vitals remain manual.

The largest remaining opportunities are editorial and accessibility work, not additional metadata: five named SVG figures still lack a tabular or list equivalent of their plotted series; 18 deep routes have no header or footer inbound link, although every indexable route has at least one body inbound link; and the explainer layer remains thinner than the data layer. The `/policy/` and governance-readiness Dataset nodes point to their registered methodology or index landing pages, while the individual records render on related deep pages. That relationship should be re-evaluated if dedicated downloadable dataset pages are added.

## Page Metadata Matrix

`self` means that the canonical equals the URL in the first column. The 404 is served at `/404`, carries a response-header `noindex`, and currently declares `/404/` as canonical; the indexable-page canonical check deliberately excludes it.

| URL | Title | Description | Canonical | H1 | Indexable | Schema |
| --- | --- | --- | --- | --- | --- | --- |
| `/` | AI Safety Tracker: cited data on AI capability, governance and safety | A cited index of AI capability, governance and safety. Current figures on model progress, adoption, law and incidents, with the source and retrieval date on every number. | self | The numbers behind AI | yes | Organization + WebSite |
| `/404` | Not found \| AI Safety Tracker | That page does not exist on this site. | `/404/` | Not found | no, response header | Organization |
| `/about/` | About \| AI Safety Tracker | An index of AI capability, adoption, governance and safety. Scope, sourcing, limits and construction. | self | About | yes | Organization |
| `/adoption/` | Adoption: enterprise and population use \| AI Safety Tracker | Who is using AI: enterprises by country, size and industry, set against the share of the population using it. | self | Adoption | yes | Organization |
| `/alignment/` | Alignment: frontier safety frameworks \| AI Safety Tracker | The measurable state of AI alignment: which capability tests are solved, what developers have promised about stopping, how much safety research exists, and what has gone wrong. | self | Alignment | yes | Organization |
| `/capability/` | Capability: training compute and cost \| AI Safety Tracker | Training compute, disclosed cost, benchmark saturation, release decisions and who builds frontier models. Every figure carries its source. | self | Capability | yes | Organization |
| `/corrections/` | Corrections \| AI Safety Tracker | How to report an error on this site, how reports are handled, and the list of corrections made. | self | Corrections | yes | Organization |
| `/glossary/` | AI glossary \| AI Safety Tracker | Definitions of the AI capability, governance and safety terms used on this site, each linked to the page that applies it. | self | Glossary | yes | Organization |
| `/map/` | Exposure against governance readiness \| AI Safety Tracker | Where AI use has run ahead of the machinery to govern it, and where it has not. Two maps, one scatter, and the table behind both. | self | Exposure against governance readiness | yes | Organization |
| `/methodology/` | Methodology \| AI Safety Tracker | How the data is fetched, processed, checked and published, and the judgement calls behind it. | self | Methodology | yes | Organization |
| `/methodology/governance-readiness/` | Governance Readiness Index \| AI Safety Tracker | The scoring rubric behind the governance readiness figure: five dimensions, what each measures, and what the score does not mean. | self | Governance Readiness Index | yes | Organization + Dataset + BreadcrumbList |
| `/news/` | News: AI policy, research and incidents \| AI Safety Tracker | Government publications, research preprints and reported incidents on AI, sorted into categories by a rule you can read. | self | News | yes | Organization |
| `/news/alignment/` | AI Alignment news \| AI Safety Tracker | Getting a model to do what was intended: interpretability, reward modelling, oversight, deception and specification. Mostly preprints, which are not peer reviewed. | self | AI Alignment news | yes | Organization |
| `/news/general/` | AI news \| AI Safety Tracker | About AI and nothing narrower. Items land here when no category rule matched, which is common for funding announcements and ministerial visits. | self | AI news | yes | Organization |
| `/news/governance/` | AI Governance news \| AI Safety Tracker | The machinery around the law: standards, frameworks, audits, assurance, procurement, institutes and who supervises whom. | self | AI Governance news | yes | Organization |
| `/news/policy/` | AI Policy news \| AI Safety Tracker | Law being made or applied. Bills, statutes, consultations, executive orders, enforcement and court decisions. Departmental communications are political statements about policy, not neutral descriptions of it. | self | AI Policy news | yes | Organization |
| `/news/progress/` | AI Progress news \| AI Safety Tracker | Capability and how it is built. Benchmarks, training, compute, scaling, releases and what models can newly do. | self | AI Progress news | yes | Organization |
| `/news/safety/` | AI Safety news \| AI Safety Tracker | Risk, harm, misuse, evaluation and things that have already gone wrong. Includes reported incidents, which are reported rather than sampled: an absence of incidents in a country usually means an absence of reporting. | self | AI Safety news | yes | Organization |
| `/policy/` | AI law and policy \| AI Safety Tracker | An index of the law that actually applies to AI across eleven jurisdictions, tagged by how binding each instrument is, with a link to every primary source. | self | AI law and policy | yes | Organization + Dataset |
| `/policy/australia/` | Australia: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in Australia, tagged by how binding it is, with a link to each primary source. | self | Australia | yes | Organization + BreadcrumbList |
| `/policy/brazil/` | Brazil: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in Brazil, tagged by how binding it is, with a link to each primary source. | self | Brazil | yes | Organization + BreadcrumbList |
| `/policy/canada/` | Canada: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in Canada, tagged by how binding it is, with a link to each primary source. | self | Canada | yes | Organization + BreadcrumbList |
| `/policy/china/` | China: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in China, tagged by how binding it is, with a link to each primary source. | self | China | yes | Organization + BreadcrumbList |
| `/policy/european-union/` | European Union: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in European Union, tagged by how binding it is, with a link to each primary source. | self | European Union | yes | Organization + BreadcrumbList |
| `/policy/india/` | India: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in India, tagged by how binding it is, with a link to each primary source. | self | India | yes | Organization + BreadcrumbList |
| `/policy/japan/` | Japan: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in Japan, tagged by how binding it is, with a link to each primary source. | self | Japan | yes | Organization + BreadcrumbList |
| `/policy/singapore/` | Singapore: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in Singapore, tagged by how binding it is, with a link to each primary source. | self | Singapore | yes | Organization + BreadcrumbList |
| `/policy/south-korea/` | South Korea: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in South Korea, tagged by how binding it is, with a link to each primary source. | self | South Korea | yes | Organization + BreadcrumbList |
| `/policy/timeline/` | AI policy timeline \| AI Safety Tracker | Every indexed AI law and policy instrument by year of adoption, newest first, with how binding each one is. | self | Policy timeline | yes | Organization + BreadcrumbList |
| `/policy/united-kingdom/` | United Kingdom: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in United Kingdom, tagged by how binding it is, with a link to each primary source. | self | United Kingdom | yes | Organization + BreadcrumbList |
| `/policy/united-states/` | United States: AI law and policy \| AI Safety Tracker | Every instrument relevant to AI in United States, tagged by how binding it is, with a link to each primary source. | self | United States | yes | Organization + BreadcrumbList |
| `/privacy/` | Privacy \| AI Safety Tracker | What this site collects, which is almost nothing, and what the host logs on its behalf. | self | Privacy | yes | Organization |
| `/progress/` | Progress: AI benchmark scores \| AI Safety Tracker | What AI models can do, grouped by skill and by difficulty: benchmark scores, how long each test stayed useful, and where the current ones are headed. | self | Progress | yes | Organization |
| `/sources/` | Sources \| AI Safety Tracker | Every source behind every figure on this site, with its licence, its update cadence and its known limitations. | self | Sources | yes | Organization |
| `/terms/` | Terms \| AI Safety Tracker | Terms of use: no advice, no warranty, licensing of material published here and of material reproduced from third parties. | self | Terms | yes | Organization |

## Technical SEO

- All 35 built pages have one canonical and matching `og:url`. All 34 indexable pages are self-referential. The non-indexable `/404` exception is described above.
- The canonical origin is fixed to `https://aisafetytracker.org`. No alternate host is emitted. HTTP-to-HTTPS redirection and HSTS are Cloudflare zone settings and were not changed or independently verified by this local audit.
- Directory routes use trailing slashes. All 42 distinct internal route and asset targets returned 200 from the local Worker; no internal link pointed at a redirect. The governance-readiness registry URL was corrected to its trailing-slash form, and a declared JSON URL that returned 404 was removed from the registry.
- Local Worker behaviour: `/about` and `/about/index.html` redirect to `/about/`; an unmatched path returns the custom 404 body; `/404`, `/404.html`, and `/404/` receive `X-Robots-Tag: noindex` through the `/404*` header rule.
- The build contains 34 indexable routes plus the 404. Every indexable route has an inbound anchor and is reachable from `/` in at most two link hops.
- No meta keywords, hreflang, fake FAQ, SearchAction, doorway pages, hidden keyword blocks, cloaking, misleading dates, or PageRank-only links were added.

## Sitemap

Exact URL: `https://aisafetytracker.org/sitemap-index.xml`

The index points to `https://aisafetytracker.org/sitemap-0.xml`, which contains exactly 34 unique, HTTPS, trailing-slash URLs. The set equals the 34 indexable HTML routes in both directions. The generated 404 file is the only HTML file excluded. No `lastmod` is emitted: build time would be misleading because the daily refresh rebuilds every page, and a correct per-route value would require a maintained route-to-dataset map that the page render cannot currently verify.

## Robots.txt

```text
# Everything here is public, cited, and meant to be found. Nothing is behind a
# login, there is no user data, and there are no crawl traps: the whole site is
# static HTML rendered at build time.
#
# This replaces the noindex meta the site carried while it was half-built.

User-agent: *
Allow: /

Sitemap: https://aisafetytracker.org/sitemap-index.xml
```

## Structured Data

Every page emits one JSON-LD `@graph` in the document head. The complete type census is:

- `Organization`: 35, identifying the publisher consistently on every page.
- `WebSite`: 1, on `/`, describing the site. No `SearchAction` is emitted because the site has no search.
- `Dataset`: 2, on the two registered first-party dataset landing pages.
- `BreadcrumbList`: 13, exactly matching the 13 visible two-item breadcrumb trails.
- Nested types: `ListItem` 26, `DataDownload` 2, `PropertyValue` 9, and `Place` 11.

The graphs are built from objects, stringified, and escape `<` as `\u003c`. A hostile `</script>` value was sabotage-tested and remained inert JSON. Local validation parsed all 35 blocks, resolved in-page `@id` references, compared structured breadcrumbs with visible trails, and checked Dataset required properties and date formats. That extended validator is a one-off audit probe; the permanent repository check guarantees one head-level block per page and valid JSON, not every semantic relationship. Google Rich Results Test and Schema.org Validator checks require a deployed URL and remain pending.

## Dataset SEO

`/methodology/governance-readiness/` carries the Governance Readiness Index Dataset node. It uses the registry name and MIT licence, the dataset notes as its 543-character description, `generated` as `dateModified`, the reviewed month as `temporalCoverage`, a 58-economy `spatialCoverage` string, five measured dimensions, the publisher/creator node, and a `DataDownload` URL for the processed JSON.

`/policy/` carries the AI Law and Policy Index Dataset node. It uses the registry name and MIT licence, the dataset notes as its 470-character description, `generated` as `dateModified`, the observed 1914/2026 adoption-year interval, eleven `Place` nodes, force/year/topics variables, publisher/creator, and a processed-JSON `DataDownload` URL.

No `DataCatalog` or `includedInDataCatalog` is emitted. The Dataset `url` values are the registered landing pages where the datasets and methods are described. They are not complete record dumps: governance records render on `/map/`, and policy instrument records render across the eleven jurisdiction routes. Both `DataDownload` URLs returned 200 during validation.

## Images / Figures

- Body image coverage: `dist` contains zero `<img>`, `<picture>`, `<source>`, `srcset`, and SVG `<image>` elements, so there are no body-image alt attributes to audit. Every page references bitmap favicon and Apple touch icon assets from the head.
- SVG accessibility: 328 SVGs comprise 317 decorative SVGs hidden from assistive technology and 11 `role="img"` SVGs with non-empty accessible names. The build check rejects a bare SVG or an empty named SVG. Ten non-SVG `role="img"` elements also have non-empty labels.
- Figure equivalents: the homepage map, all four `/map/` figures, and the alignment research chart have tabular equivalents. Five named figures do not yet have a table or list containing their plotted series: three capability charts, the alignment benchmark matrix, and the policy timeline year distribution. This is deferred accessibility work.
- Figure changes: the homepage map retained hover behaviour but lost 145 duplicate `/adoption/` hrefs, reducing homepage focusables from 232 to 87. The release-cadence graphic now exposes each column label as text. Map coordinate precision was reduced at page call sites and stroke scale was preserved, cutting the heaviest map HTML while keeping the visual readable.
- Social image: `public/og.png` is a 1200 by 630, 44,321-byte brand card. Its source is `scripts/og-card.html`; the source file is not copied to `dist`.

## Social Metadata

The existing `og:title`, `og:description`, `og:type`, `og:site_name`, `og:url`, `og:locale`, `twitter:title`, and `twitter:description` tags remain. This change adds `og:image`, width, height, and alt text, adds `twitter:image`, and changes `twitter:card` from `summary` to `summary_large_image` on all 35 pages.

Exact preview image URL: `https://aisafetytracker.org/og.png`

The local Worker serves the image successfully. The current production site was not deployed in this work, so live social crawlers will not see it until deployment.

## Mobile

The original desktop navigation remained visible until 640px even though its nine non-wrapping links required about 805px, causing all 35 pages to pan horizontally around tablet portrait width. The breakpoint is now 860px. A long homepage metric tag also overflowed at 320px; wrapping was enabled only in the homepage tag row.

All 35 routes were rechecked at 17 distinct widths: 320, 360, 390, 430, 641, 700, 768, 800, 820, 859, 860, 861, 900, 1024, 1280, and 1440px. No route scrolled horizontally. Separate over-wide sabotage elements made every probe report overflow, including the 859/860/861 breakpoint boundary.

## Core Web Vitals

These are Playwright lab measurements using a Lighthouse-like mobile profile: 390 by 844px, 4x CPU slowdown, 1.6Mbps throughput, and 150ms latency. Lighthouse itself was not installed. No CrUX field data exists for this low-traffic domain, and lab data is not field data. INP cannot be produced by this no-interaction lab run; TBT after FCP is the available proxy.

Before the font change, 5 of 35 routes exceeded CLS 0.10, with a worst observed value around 0.25. After replacing the package rules with equivalent `font-display: optional` declarations, all 35 measured 0. The maximum LCP remained 1,044ms before and after within run-to-run variation. Worst TBT was 1ms.

| Page | LCP | INP/TBT | CLS | Notes |
| --- | ---: | ---: | ---: | --- |
| `/` | 960ms | 0ms TBT | 0 | 2,024 DOM nodes, five requests |
| `/map/` | 864ms | 1ms TBT | 0 | data-heavy map route |
| `/capability/` | 920ms | 0ms TBT | 0 | 3,078 DOM nodes |
| `/news/` | 940ms | 0ms TBT | 0 | 3,174 DOM nodes |
| `/policy/australia/` | 872ms | 0ms TBT | 0 | baseline CLS about 0.20 |
| `/methodology/governance-readiness/` | 964ms | 0ms TBT | 0 | Dataset and breadcrumb route |
| `/progress/` | 920ms | 0ms TBT | 0 | 948 DOM nodes |
| `/alignment/` | 924ms | 0ms TBT | 0 | 947 DOM nodes |

The tradeoff is measured: with a cold cache and throttled 1.6Mbps or 9Mbps connection, the first view uses the system fallback while the font downloads; the warm view uses Geist. With a cold cache and no network throttling, Geist renders on the first view. An intercepted `swap` A/B produced total CLS 0.8234 over seven susceptible routes, compared with 0 under `optional`.

## Internal Linking

The built-site checker resolves 1,777 internal hrefs. There are 34 distinct indexable route targets and none lacks an inbound anchor. The crawl graph reaches 15 routes in one hop and the remaining 18 in two; the 404 is intentionally absent. There are no broken internal links and no links to redirects among the 42 distinct route and asset targets tested against the local Worker.

Header and footer chrome reaches only 16 distinct route targets across the build. The 18 routes with zero chrome inbound are six news category routes, eleven jurisdiction routes, and `/policy/timeline/`; all remain reachable through body navigation. `/policy/timeline/` is the thinnest, with one body inbound link from `/policy/`.

Improvements include 13 visible breadcrumbs, body links from every jurisdiction route back to `/policy/`, a direct `/map/` methodology link, two new glossary inbound links, and five more descriptive glossary anchor labels. The source registry now uses the canonical trailing-slash methodology URL. Twenty-two absolute-path fragment links were separately resolved; the permanent checker validates the path for those links but not the fragment. Removing 145 duplicate homepage map hrefs intentionally reduced `/adoption/` body inbound links from 147 to 2. Retargeting ten jurisdiction score links to the methodology intentionally reduced `/map/` body inbound links from 11 to 1.

## URL Changes

No existing public URL slugs were changed.

No redirect map is required. One internal registry URL was normalised from `/methodology/governance-readiness` to `/methodology/governance-readiness/`; it names the same public route after the host's existing redirect.

## Search Console

**MANUAL DNS VERIFICATION REQUIRED**

1. Sign in to Google Search Console and add a Domain property for `aisafetytracker.org`.
2. Copy the TXT record value Google provides.
3. Add that exact TXT record at the domain's DNS provider without changing existing records.
4. Return to Search Console and select Verify after DNS propagation.
5. Submit `https://aisafetytracker.org/sitemap-index.xml` under Sitemaps.
6. After deployment, use URL Inspection on `/`, `/map/`, `/policy/`, and one jurisdiction route and request indexing where appropriate.

No verification token exists in the repository, and no account, DNS, or Search Console change was made.

## SEO Tests

`scripts/check-seo.mjs` adds fatal checks for exactly one non-empty title, description, canonical, H1, `og:url`, `og:image`, Twitter card, and head-level JSON-LD block per page; unique titles and descriptions; self-referential indexable-page canonicals; canonical/`og:url` agreement; deployed social-image files; `summary_large_image`; JSON parsing; sitemap/build set equality; and a real sitemap named by robots.txt. Editorial title and description lengths remain warnings, currently 13, rather than build failures.

`scripts/check-internal-links.mjs` now treats the unslashed directory form as a redirect rather than a served page, exempts only `application/ld+json` data blocks from the zero-JavaScript rule, rejects `.js`, `.mjs`, and `.map` output, and requires every SVG to be decorative or accessibly named. `scripts/check-lib.mjs` asserts that local font declarations still match all 11 Fontsource faces and remain `optional`.

The SEO checker is available as `npm run check:seo`, is included in `npm run check:built`, and therefore runs in the daily refresh workflow before refreshed data can be committed. The Cloudflare dashboard's push-deploy build command is not represented in the repository and was not independently verified.

The new missing-metadata assertions were sabotage-tested by removing `og:url`, `og:image`, `twitter:card`, and the JSON-LD type from a built page; the checker reported all four defects and exited non-zero. Earlier implementation checks were also sabotage-tested for duplicate titles, wrong canonicals, broken social-image paths, malformed JSON-LD, sitemap omissions/additions, missing robots sitemap, executable script, stray JavaScript files, unslashed directory links, forbidden dashes, and bare SVGs.

## Validation

- Build: `npm run build` passed on 19 September 2026; 35 pages generated.
- Library checks: `npm run check:lib` passed.
- Built checks: `npm run check:built` passed. The link checker reported 1,777 internal links and zero broken links, forbidden dashes, unsafe href schemes, executable client JavaScript, unboxed tables, or unnamed SVGs.
- SEO checker: passed with 35 pages, unique titles and descriptions, 34 self-referential indexable canonicals, required social metadata and JSON-LD, sitemap/build equality, and 13 editorial warnings.
- Structured data: 35 blocks parsed; Organization 35, WebSite 1, Dataset 2, BreadcrumbList 13; the extended one-off validator found no problems.
- Sitemap: 34 URLs, exact equality with the indexable build; index and child sitemap both parse.
- Robots: present, allows all, and names the built sitemap index.
- Mobile: all 35 routes passed at 17 distinct widths, with sabotage-confirmed probes.
- Lab performance: 0 of 35 routes over CLS 0.10, worst CLS 0, maximum LCP 1,044ms, worst TBT 1ms. No field data was available.
- Python self-checks: `common.py`, governance, policy, frontier, contrast, news, Eurostat, and Microsoft diffusion checks passed in the implementation verification. The OpenAlex self-check requires network access and is not claimed here as part of the final local rerun.
- Static/privacy regression: zero `.js`, `.mjs`, or `.map` files; zero executable scripts; zero inline event handlers; zero `<img>` elements; 35 non-executable JSON-LD blocks.

The production URL, Google validators, social debuggers, and Search Console were not tested because this change set was deliberately not deployed.

## Deferred / Manual Work

- Review and deploy the local commit, then confirm the live HTML and `https://aisafetytracker.org/og.png`.
- Validate representative deployed URLs with Google Rich Results Test and Schema.org Validator.
- Test the deployed card with the relevant social platform debuggers or share composers.
- Create and DNS-verify the Search Console Domain property, submit the sitemap, and inspect representative URLs.
- Monitor Search Console indexing, queries, click-through rates, and crawl errors after sufficient time.
- Review field Core Web Vitals after enough traffic exists; do not substitute the lab figures for CrUX.
- Add text equivalents for the five named SVG figures identified above.
- Decide whether deep news and jurisdiction routes need more persistent chrome or hub-page links based on actual search and navigation data.
- Revisit the two Dataset landing-page relationships if dedicated record-level dataset pages are introduced.
- Optionally enable GitHub private vulnerability reporting; `SECURITY.md` now accurately states that it is disabled.

## Ranking Reality

Technical SEO has been optimised, but Google ranking cannot be guaranteed. Ranking depends on relevance, content usefulness, authority, external references and links, competition, query intent, and Google's ranking systems.

## Final Git Diff

At report creation, the SEO implementation consisted of 31 modified tracked files and five new implementation files, plus this report. The pre-existing untracked `design-directions/` folder is unrelated and excluded from the summary.

Material changes by file:

- `.github/workflows/refresh-data.yml`: runs the built SEO checks in the daily data workflow and documents the validation boundary.
- `SECURITY.md`: accurately states that private vulnerability reporting is disabled.
- `astro.config.mjs`: documents why sitemap `lastmod` is intentionally omitted.
- `data/sources.json`: fixes the governance-readiness landing-page URL and removes a declared JSON URL that 404s.
- `package.json`: adds `check:seo` and includes it in `check:built`.
- `public/_headers`: adds noindex coverage for every `/404*` form and updates static/CSP documentation.
- `public/apple-touch-icon.png`: adds the 180 by 180 touch icon.
- `public/og.png`: adds the 1200 by 630 social card.
- `scripts/check-internal-links.mjs`: tightens URL, zero-JavaScript, generated-file, dash, and SVG checks.
- `scripts/check-lib.mjs`: validates the local Fontsource declarations and `optional` display mode.
- `scripts/check-seo.mjs`: adds the built-site SEO regression suite.
- `scripts/og-card.html`: provides the reproducible social-card source.
- `src/components/Provenance.astro`: refines accessible/citation markup without changing factual attribution.
- `src/components/Sparkline.astro`: documents the caller's required text-equivalent condition.
- `src/components/TimeMap.astro`: adds page-controlled map precision and stroke scaling.
- `src/components/WorldMap.astro`: adds page-controlled map precision and stroke scaling.
- `src/layouts/Base.astro`: emits canonical social metadata, icons, JSON-LD, `en-GB`, and the measured 860px navigation breakpoint.
- `src/lib/news.ts`: trims the general-news description.
- `src/lib/sources.ts`: adds source lookup and oldest-retrieval helpers used by metadata and visible dates.
- `src/pages/about.astro`: corrects the first-party JavaScript claim and improves metadata.
- `src/pages/adoption/index.astro`: improves the search title and visible machine-readable freshness date.
- `src/pages/alignment/index.astro`: improves metadata, figure naming, and adds a research-chart data table.
- `src/pages/capability/index.astro`: improves the search title and freshness markup.
- `src/pages/glossary.astro`: improves title/description and cross-page anchor text.
- `src/pages/index.astro`: moves the H1 before the heavy map, fixes H1 whitespace and narrow tag wrapping, removes 145 duplicate hrefs, and reduces map-coordinate output.
- `src/pages/map/index.astro`: improves metadata, adds the methodology link, and reduces map-coordinate output.
- `src/pages/methodology/governance-readiness.astro`: adds breadcrumbs, Dataset/BreadcrumbList data, and freshness markup.
- `src/pages/methodology/index.astro`: adds a glossary inbound link.
- `src/pages/news/[category].astro`: gives the general category an explicit news H1 and machine-readable date.
- `src/pages/news/index.astro`: improves the search title and freshness markup.
- `src/pages/policy/[jurisdiction].astro`: adds breadcrumbs, BreadcrumbList data, parent links, and methodology links.
- `src/pages/policy/index.astro`: improves metadata and adds Dataset markup and combined freshness.
- `src/pages/policy/timeline.astro`: adds breadcrumbs, BreadcrumbList data, and title/freshness improvements.
- `src/pages/progress/index.astro`: improves metadata, freshness, and release-cadence accessible text.
- `src/styles/fonts.css`: replaces package imports with equivalent `font-display: optional` face declarations.
- `src/styles/global.css`: adds shared breadcrumb styling and removes the old Fontsource imports.

Commands used for the final local state:

```bash
git status --short
git diff --stat
npm run build
npm run check:lib
npm run check:built
```
