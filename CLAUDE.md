# AI Safety Tracker

An independent, cited index of AI capability, governance and safety.
Live at **https://aisafetytracker.org**.

The GitHub repository and the Cloudflare Worker are both still named `ai-safety-index`, from before
the rename. Neither was renamed and neither should be; see Deployment.

**`aisafetyindex.org` is not this site.** It is an unrelated third party's "Open LLM Safety Index",
a 1-to-5 safety leaderboard for open-weight models, hosted on Vercel. It shares no code, no sources
and no infrastructure with this project. The near-collision with our repository and Worker name has
already caused one external reviewer to treat the two as one deployment and report a discrepancy
that does not exist. This site is **only** `aisafetytracker.org`, and that domain is the only one
in scope for anything, security testing very much included.

## What it is for

The field's data is fragmented. Epoch AI has the best capability data and almost no policy. OECD
and IAPP have policy and no capability data. AI Safety Atlas has explainers and no live data.
Nobody joins them.

Two audiences, on the same pages, through progressive disclosure rather than two sites:

- a lay reader who wants to understand what is actually happening in AI
- a technical reader who wants current, sourced numbers without visiting eight sites

**Non-goals, deliberately:** no forecasts of our own, no accounts, no comments, no newsletter, no
tracking, no revenue model. It is a personal portfolio project and an experiment in agentic AI.

**The ethos, in one line the whole project answers to:** every number here tells you where it came
from.

## The one architectural rule

Citation-first. Everything else follows from it.

1. Every source is declared once in `data/sources.json` with its licence, attribution, cadence and
   known limitations.
2. Every processed record carries a `source_id`. Licence and attribution are resolved by joining
   that registry at render time, so attribution is a join rather than a habit.
3. Both ends guard the licence. `etl/common.py:guard()` refuses to *write* a dataset whose source
   forbids republication; `src/lib/sources.ts:assertRenderable()` refuses to *render* one. Two
   checks, because data can also arrive hand-authored.
4. `<Provenance source={...}>` turns a `source_id` into a click-through popover on any figure.

**Adding a source is exactly three steps:** register it in `data/sources.json`, write an ETL module
that stamps `source_id` on every record, pass `source` to `<Provenance>`. Nothing else.

## The site

Nav order runs outward from the models themselves. Every page is a masthead, then sections of
figures, each figure carrying a `<Provenance>` marker and a caveat where it could mislead.

| Route | What is on it |
|---|---|
| `/` | Banner stating the site's purpose, then `What is on this site` (one line per section), then `Explore metrics`: one panel per section with that section's headline figures, heading as the way in. Full-width choropleth of AI use with a scrubber that steps through reporting periods with no JavaScript (`TimeMap`), plus the ranked table behind it. |
| `/progress/` | **Outputs.** Benchmark scores by category and by difficulty tier (both our own classification), how long each test stayed useful, straight-line extrapolations of open benchmarks, a rail of per-benchmark frontier lines, the most recent notable models, release cadence by quarter. |
| `/capability/` | **Inputs.** Training compute over time with the fitted frontier, disclosed cost, how models ship (open weights / API / unreleased), how far behind the open-weight frontier is, who builds them, and the compute thresholds written into law against the models that cross them. |
| `/alignment/` | How close is AGI, answered only from measured quantities. Published frontier safety frameworks side by side. Safety research against capability research from OpenAlex. Reported incidents. A section on what the page cannot show. |
| `/adoption/` | Population use against enterprise use, by size, by industry, by technology, by country. |
| `/map/` | Exposure against governance readiness: a divergence map, the two layers separately, a scatter, and the table behind all three. |
| `/policy/` + 11 jurisdiction routes | The law that actually applies to AI, tagged by how binding each instrument is, with a link to every primary source. |
| `/policy/timeline/` | The same instruments ordered by year of adoption, with a per-year distribution split binding against everything else. Most applicable law predates AI. |
| `/news/` + 6 category routes | Official publications, preprints and reported incidents. Every item prints the keyword terms that filed it where it is. |
| `/sources/` | Every registered source, its licence, what it is used for, and what it cannot tell you. Usage is derived from the processed data, not hand-written. |
| `/glossary/` | Every term the data pages use, defined as this site applies it, linked to the page that applies it. |
| `/about/`, `/methodology/`, `/methodology/governance-readiness/`, `/corrections/`, `/privacy/`, `/terms/` | Scope, method, rubric, and the legal pages. |

**The split between `/progress/` and `/capability/` is outputs against inputs.** Benchmarks live on
progress. Do not move them back.

**Components** (`src/components/`): `Provenance` (the citation popover), `StatTile` (a bento cell),
`BarTable` (ranked list, ten rows plus a disclosure), `TimeMap` (choropleth with a period stepper),
`WorldMap` (static choropleth), `Sparkline`, `NewsList`.
**Library** (`src/lib/`): `sources.ts` (registry, licence guard, freshness), `geo.ts` (projection,
country joins, percentile ranks), `news.ts` (category vocabulary).

## The pipeline

Python stdlib plus `certifi`, one module per source in `etl/`, orchestrated by `run_all.py`. One
source failing must not take the others down: a partial refresh with a loud warning beats a green
build with no data.

**Every module exposes `run(offline: bool)` and `--self-check`.** Fetchers pull to `data/raw/` via
`common.fetch()`, which serves a cached copy when fresh, when offline, or when the network fails.
Hand-coded indexes ignore `offline` because there is nothing to fetch.

**Everything writes through `common.write_dataset()`**, which calls `guard()` first and is
idempotent: it skips the write when records are unchanged, so a commit in the history means the
data actually moved rather than that a timestamp did. Last-checked time lives in `_status.json`.

Current modules: `fetch_epoch` (5 datasets), `fetch_microsoft_diffusion`, `fetch_eurostat` (4),
`fetch_news` (8 feeds), `fetch_openalex`, `build_governance`, `build_policy_index`
(+ `policy_jurisdictions.py`, the instrument lists), `build_frontier_index` (2).

Four datasets are our own work, all MIT licensed like the code: **Governance Readiness Index**,
**AI Law and Policy Index**, **Frontier Safety Framework Index**, **Compute Threshold Index**. They exist because the
established trackers are protected databases; coding primary instruments ourselves sidesteps that
and makes the result ours to license.

```bash
npm install
npm run etl          # fetch and process every source
npm run etl:offline  # rebuild from cache, no network
npm run dev          # http://localhost:4321
npm run build
npm run check:lib    # render-side logic: path rounding, ranks, country joins, category drift
npm run check:built  # against dist/: links, anchors, dashes, canonical origin, stale name, noindex,
                     # unsafe href schemes, zero client JS, every table inside a .scroll-x box

python etl/common.py                                  # licence guard, idempotence, dash rule
python etl/fetch_news.py --self-check                 # snippet cap, relevance, categories, language
python etl/fetch_eurostat.py --self-check             # JSON-stat decoder, aggregate filter
python etl/fetch_openalex.py --self-check             # query narrowing and year range (needs network)
python etl/fetch_microsoft_diffusion.py --self-check  # source encoding
python etl/build_governance.py --self-check           # scoring rubric
python etl/build_policy_index.py --self-check         # schema and coverage
python etl/build_frontier_index.py --self-check       # frameworks and compute thresholds
python etl/check_contrast.py                          # palette against WCAG AA

python etl/build_governance.py --check-links          # probe every cited instrument
python etl/build_policy_index.py --check-links        # same, for the law index
python etl/build_frontier_index.py --check-links      # same, for frameworks and thresholds
```

Every self-check runs in CI before any data is written; `check:built` runs after the build. The
`--check-links` probes are run by hand, not in CI, because they hit other people's servers.

## House rules

Each of these cost real time. They are rules, not suggestions.

**Verification**

- **Read the rendered output, not only the source.** Almost every real bug here was found in built
  HTML or live ETL output, not in code. Check `dist/`, or the live site, before believing a change.
- **Verify a check by sabotaging it, and confirm the sabotage actually bit.** A check that still
  passes when the logic is broken is worse than no check.
- **A citation that cannot be verified is not published.** If no URL resolves, state the fact in
  prose without an entry rather than citing something that 404s.
- **Distinguish blocked from dead when probing links.** Only 404 and 410 mean a citation is wrong.
  Government sites refuse HEAD and refuse non-browsers; never spoof a browser to get past a bot wall.

**Editing**

- **Never run a bulk regex over source files.** Edit deliberately and assert that every string
  replacement actually matched. A sweep can rewrite a rule and the assertion guarding it into a
  matching pair that passes while doing nothing.
- **Use the Write or Edit tools for anything containing escapes.** Multi-layer heredoc quoting
  mangles `\b`, `\n` and friends silently.
- **Shared furniture belongs in `global.css`.** A class scoped inside one page loses all styling the
  moment a second page uses it and the first stops.

**Python / ETL**

- **Pass `encoding=` to `read_csv` when the publisher's encoding is known.** A fallback chain can
  decode wrongly without erroring.
- **Feeds carry invisible characters.** Zero-width spaces are not whitespace to Python; `_clean`
  strips category Cf.
- **`float(10 ** n) == value`,** not `10 ** n == value`. One is an exact integer, the other a double.
- **A running maximum can never have a negative slope.** Say the series is monotone wherever a fit
  through one is shown.
- **Write dash characters as escape sequences,** never literally, so a text sweep cannot reach them.

**Front end**

- **`Provenance.astro` must emit phrasing content only.** Spans, never `div`/`p`/`dl`: the marker
  sits inside `<p>` and a block-level tag silently hoists the panel out of it.
- **Always `var(--x, fallback)`** when a custom property may be absent. An unresolvable `var()` is
  invalid, not transparent, and the property falls back to its initial value.
- **Check the production build before debugging CSS.** The dev server serves stale scoped styles
  after component edits.
- **A scroll container only contains what it is the containing block for.** `overflow-x: auto` does
  not clip an absolutely positioned descendant unless the box is also positioned, so
  `.scroll-x` carries `position: relative` and `.visually-hidden` pins `inset-inline-start: 0`.
  Without either, the hidden label in a bar-column header was laid out at its static position 800px
  along a table, escaped the scroll box, and stretched the *document* instead: the page then panned
  sideways into empty ground on a phone while looking perfect on a laptop.
- **Every table goes inside `<div class="scroll-x">`.** A table is the one element whose width is
  set by its content, so an unwrapped one widens the page rather than scrolling. `check:built`
  enforces it.
- **Equal specificity means source order decides.** A `@media` override written *above* the rule it
  overrides parses, matches, and does nothing. `.bar-col`'s phone width had to move below the base
  rule to take effect; it was silently inert for a build first.
- **`getComputedStyle` during a transition returns the animated value.** Disable the transition
  before asserting on a state change.
- **To test for horizontal overflow,** `window.scrollTo({left: 5000, behavior: "instant"})` and see
  whether `scrollX` moves, having first set `document.documentElement.style.scrollBehavior = "auto"`.
  Both halves are load-bearing and both were learned the hard way. `global.css` sets
  `scroll-behavior: smooth` on `html`, which makes a plain `scrollTo` **asynchronous**: `scrollX`
  read on the next line is still 0, so the test passes on every page whatever the layout does. It
  reported all 33 pages clean while three of them scrolled sideways by up to 853px.
  Then check the check: append a 900px `div` to `body` and confirm the probe now fails.
- **Do not run that probe under Playwright's `isMobile: true`.** Mobile emulation honours the
  viewport meta, so an over-wide page *zooms out* instead of scrolling and `scrollX` stays 0 even
  with the fix above. That zoom-out is the bug as a reader meets it, not the absence of one. Probe
  in a normal context at phone width; use `isMobile` for screenshots.
  `documentElement.scrollWidth` counts clipped descendant overflow, so it can report a page broken
  when a `.scroll-x` box is doing its job. Trust it only when it agrees with the scroll probe.

## Design lock

Set from the tasteskill brief at `DESIGN_VARIANCE 7 / MOTION_INTENSITY 4 / VISUAL_DENSITY 7`.
**Where the skill and the user's instruction conflict, the user's instruction wins.**

- **One theme, semi-dark.** No section inverts. Tokens in `src/styles/global.css`.
- **One accent,** amber `#f2a950`, on a blue-slate ground. `--accent-2`, blue, is a DATA hue and not
  a second accent: it encodes governance wherever governance is plotted, and appears nowhere else.
  `--ok` and `--warn` are for genuine state, never decoration.
- **Density over whitespace.** If a change makes the page taller without adding information, it is
  the wrong change.
- **The ground is graph paper,** not flat colour: a grid on `body`, a dot grid on `.section--sunk`,
  a diagonal hatch on `.section--hatch`. All CSS gradients.
- **Copy on a data page describes the figure and stops.** What it shows, over what period, from
  whom, and a notable number if there is one. Do not draw the implication for the reader: the legend
  and the key are the explanation.
- **Register: formal, declarative, and shorter than feels natural.** Set by the owner and applying
  to every reader-facing string on the site, the legal pages included.
  - State what the data is and what it measures. Do not argue for it, and do not persuade the
    reader that the site is worth reading.
  - Cut any sentence a reader can infer from the figure itself. "Step through the reporting
    periods" describes the control they are looking at.
  - No "not X, but Y" or "X rather than Y" as rhetoric, no second person, no imperatives to the
    reader, no asides about how the site was built or why a decision was made. Those belong in
    source comments, which is where the reasoning in this repository lives.
  - `/about/`, `/terms/`, `/privacy/` and `/corrections/` are reference documents. They should be
    dull, and a reader should be able to find one fact in them without reading a paragraph.
  - On authorship the site says exactly one thing: AI was used to help build it.
- **Long ranked lists show ten rows and put the tail in a disclosure.** Use `BarTable`.
- **One radius system.** `--r` containers and controls, `--r-pill` tags, `--r-mark` data marks.
- **Zero em-dashes and en-dashes anywhere,** including source data, normalised at ETL time by
  `normalise_dashes`. The permitted dash is the hyphen; `check:built` fails the build otherwise.
- **No images and no hand-rolled SVG icons,** no decorative dots, no eyebrows above headings, no
  scroll cues, no version labels. Icons come from the project's Phosphor set through `astro-icon`.
- **The homepage banner is the one exception to "no hero",** added on the owner's instruction,
  which the design lock defers to. It keeps the rest of the rule: the background is four CSS
  gradients in the existing graph-paper language and there is still no image anywhere on the site.
- **Zero client JavaScript.** Charts and maps render to SVG at build time; interactivity is CSS
  (`<details>`, `:checked`, the native Popover API). Keep it that way.
- Run `python etl/check_contrast.py` after any colour change.

## Data sources

Full registry with licences in `data/sources.json`; 26 registered, 16 in use.

**Backbone:** Epoch AI (models, benchmarks, clusters, CC BY 4.0), Microsoft AI Diffusion (147
economies, MIT), Eurostat enterprise adoption (Decision 2011/833/EU), OpenAlex (research volume,
CC0), Natural Earth (map geometry, public domain).
**News feed, eight:** US Federal Register and NIST (public domain), GOV.UK (OGL v3.0), European
Commission (Decision 2011/833/EU), Government of Canada (OGL Canada), arXiv cs.AI and cs.CY
(metadata CC0), AI Incident Database (ODbL, display only).

**Ruled out, and registered so that using them fails the build:**

- **Artificial Analysis**: free tier forbids redistribution.
- **Stanford AI Index**: CC BY-NC-ND, so its figures cannot be re-plotted.
- **METR time horizons**: their analysis repository carries no LICENSE file, so no reuse permission
  exists and the default is reserved. Their headline finding is stated as attributed prose with a
  link, which is a fact rather than their data, and `/alignment/` says so on the page.

**Legal constraints** (detail in `docs/00-research-findings.md` section 3):

- The EU sui generis database right is separate from copyright. **Do not bulk-extract OECD.AI or
  IAPP.** Our own coded indexes sidestep this.
- News aggregation is headline, short extract, publisher, canonical link. Never full text, never a
  hotlinked image. The 200-character cap in `fetch_news.py` is the mechanism.
- AI Incident Database is ODbL: display only, never a derived database dump.
- Identify the bot honestly in the user agent. Daily, not hourly. These publishers give us the data
  for free.

## Deployment

Public repo, `main` branch, Cloudflare Workers static assets, `wrangler.jsonc` at the root.

**Cloudflare Workers Builds is connected and builds every push to `main`.** Deploys land in about a
minute. `.github/workflows/refresh-data.yml` runs daily at 06:17 UTC, runs every guard before
fetching, builds the site before committing, and labels its commits `Data refresh` or
`Pipeline heartbeat`.

Three things that are true and non-obvious:

- **Workers Builds reports as a GitHub check run, not a deployment.** Querying deployments returns
  nothing even when everything works. Check with:
  ```bash
  gh api repos/PhlegmaticPhox/ai-safety-index/commits/main/check-runs --jq '.check_runs[] | "\(.name): \(.status) \(.conclusion)"'
  ```
- **Never change `name` in `wrangler.jsonc`.** It does not rename a Worker: it creates a second one
  and leaves the domain pointing at the first, with every build reporting success.
- **A green build is not a visible change.** Build success only means the Worker updated. Verify by
  fetching the live URL, and remember Cloudflare caches.

**The site origin is hardcoded** in `astro.config.mjs` and deliberately not read from the
environment; a value that never changes does not need a mechanism. `check:built` fails if the
rendered canonical origin is not a plausible hostname, if any page carries a `noindex`, or if any
page still carries the pre-rename name.

## Working agreement

Matthew wants involvement only in decisions and payment, not build mechanics. **Act rather than
ask;** batch anything that genuinely needs him into one block.

**Hard limits, never worked around:** creating accounts, entering passwords and making purchases are
his, always. Several gaps in the data exist because of this and that is the correct outcome.

**His personal email never appears publicly.** Commits use the GitHub noreply address, which
`git config` already enforces, so commits are safe without anyone remembering. The rule is wider
than commits: no `mailto:`, no contact field, no bot user-agent carrying it. Corrections route
through GitHub issues, which is why `/corrections/` is written the way it is.

**He challenges analytically weak framing and is usually right to.** The flagship visualisation was
originally compute concentration against regulation; he rejected it because compute is where models
are built, which says nothing about where they are used or governed. Before proposing any
comparison, be able to state plainly what links the two variables. If you cannot, it is decoration.

## What this site has that the others do not

Five joins nobody else publishes. If a change would break one of them, it is the wrong change.

1. **Compute thresholds against actual models** (`/capability/#thresholds`). Every training-compute
   threshold written into law, with the count of models above each.
2. **How far behind the open-weight frontier is** (`/capability/#open-weights`). Two running maxima
   read horizontally: the gap in months between the overall frontier reaching a level and an
   open-weight model doing so.
3. **Frontier safety frameworks side by side** (`/alignment/#frameworks`). Eight developers, eight
   incomparable scales, and who commits to stopping rather than to deciding. Includes the developers
   who have published nothing, because the absence is the finding.
4. **Safety research against capability research** (`/alignment/#research`). OpenAlex counts by year
   with the literal query printed next to every series, so the definition is arguable.
5. **What law applies where** (`/policy/`). Eleven jurisdictions, and the number the page leads on is
   how few binding instruments name AI at all.

## Not done

- The law index covers eleven jurisdictions. Australia is far deeper than the rest because it was
  indexed first, which the page says out loud so the totals are not read as a comparison.
- `/progress/` is the only page that extends past the last observation. Every such number is
  labelled an extrapolation of a stated fit, with the window and both directions of bias printed
  beside it. Keep it that way or take it out.
- The news feed's alignment and progress categories depend on arXiv, which announces on weekdays
  only. A feed built at a weekend legitimately has none, and the page says so.
- US industry adoption is missing. Census BTOS has it; its API needs a key, which needs an account.
- The Anthropic Economic Index is registered but unused: the release files are 77MB and 219MB, too
  much to pull daily without streaming aggregation.
- The site is newly indexable. Submitting the sitemap to Search Console needs a Google account.

`docs/02-plan.md` and `docs/01-ideas-backlog.md` are the original plan and idea list, now marked
item by item with what was built. Read them for the reasoning and the unbuilt ideas, not for current
state: **this file is the source of truth for what exists.**

**The largest unbuilt block is the explainer layer** (backlog B1 to B4, plan Phase 4): dual-track
prose, a jargon layer, a scale-intuition widget, a disagreement map. It is the half of the
two-audience promise that is currently thinner, and the obvious next objective.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
