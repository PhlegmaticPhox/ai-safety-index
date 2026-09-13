# AI Safety Tracker

An independent, cited index of AI capability, governance and safety.

Named for the domain, not the other way round. It was called AI Safety Index until the domain
made the mismatch obvious, and the rename also clears a collision with the Future of Life
Institute's AI Safety Index, which is an established annual report on a different subject. The
word index still describes what the site is and is used freely in prose and in the names of our
own datasets; it is just not the name.

## Goals

The field's data is fragmented. Epoch AI has the best capability data and almost no policy.
OECD and IAPP have policy and no capability data. AI Safety Atlas has excellent explainers and no
live data. Nobody joins them, and practitioners say so plainly: the field is hard to navigate and
there is no single overview of how the different efforts link together.

This site tries to be that overview, serving two audiences at once:

- a lay reader who wants to understand what is actually happening in AI
- a technical reader who wants current, sourced numbers without chasing eight sites

Four gaps it exists to fill:

1. Capability, governance and incident data on one screen
2. One page that serves both audiences through progressive disclosure, not two sites
3. Exposure against governance readiness, rendered as a live map
4. Per-datapoint provenance, so any number can be traced to where it came from

Non-goals, deliberately: no forecasts of our own (we render other people's with their track
records instead), no accounts, no comments, no newsletter, no tracking cookies.

This is a personal portfolio project and an experiment in agentic AI. It is not a commercial
product and has no revenue model.

## The one architectural rule

Citation-first. Everything else follows from it.

1. Every source is declared once in `data/sources.json` with its licence, attribution, cadence and
   known limitations.
2. Every processed record carries a `source_id`. Licence and attribution are resolved by joining
   the registry at render time, so attribution is a join rather than a habit.
3. Both ends guard the licence. `etl/common.py:guard()` refuses to *write* a dataset whose source
   forbids republication; `src/lib/sources.ts:assertRenderable()` refuses to *render* one. Two
   checks because data can also arrive hand-authored.
4. `<Provenance>` turns a `source_id` into the click-through popover on any figure.

Adding a source means: register it, write an ETL module that stamps `source_id` on each record,
pass `source` to `<Provenance>`. Nothing else.

## Stack

Astro 5 + TypeScript, static output, **zero client JavaScript** (keep it that way; charts and maps
render to SVG at build time). Python stdlib ETL plus `certifi`. Geist and Geist Mono via Fontsource.
Phosphor icons via `astro-icon`. Map geometry from Natural Earth via `world-atlas`, projected with
`d3-geo` at build time. Hosted on Cloudflare Workers static assets, data refreshed by a daily
GitHub Actions cron.

```bash
npm install
npm run etl          # fetch and process every source
npm run etl:offline  # rebuild from cache, no network
npm run dev          # http://localhost:4321
npm run build
npm run check:lib    # render-side logic: path rounding, ranks, country joins, category drift
npm run check:built  # against dist/: internal links, same-page anchors, forbidden dashes

python etl/common.py                             # licence guard, idempotence, dash rule
python etl/fetch_news.py --self-check            # snippet cap, relevance, categories, language
python etl/fetch_eurostat.py --self-check        # JSON-stat decoder
python etl/fetch_openalex.py --self-check        # query narrowing and year range (needs network)
python etl/build_governance.py --self-check      # scoring rubric
python etl/build_policy_index.py --self-check    # schema and coverage
python etl/build_frontier_index.py --self-check  # frameworks and compute thresholds
python etl/fetch_microsoft_diffusion.py --self-check  # source encoding
python etl/check_contrast.py                     # palette against WCAG AA

python etl/build_governance.py --check-links     # probe every cited instrument
python etl/build_policy_index.py --check-links   # same, for the law index
python etl/build_frontier_index.py --check-links # same, for frameworks and thresholds
```

Every check runs in CI before any data is written; `check:built` runs after the build. The
`--check-links` probes are run by hand, not in CI, because they hit other people's servers.

## House rules, learned the hard way

Each of these cost real debugging time. Do not relearn them.

- **`Provenance.astro` must emit phrasing content only.** Spans, never `div`/`p`/`dl`. The marker
  sits inside `<p>`, and the HTML parser auto-closes a paragraph when it meets a block-level tag,
  silently hoisting the panel out and leaving an empty paragraph behind.
- **Never run a bulk regex over source files.** A project-wide dash sweep once rewrote a
  normalisation line *and the assertion guarding it* into a matching pair that passed while doing
  nothing. Edit deliberately, and assert that every string replacement actually matched.
- **Write dash characters as escape sequences in code**, never as the literal character, so a
  text-level sweep cannot reach them. See `normalise_dashes` in `etl/common.py`.
- **Multi-layer heredoc escaping breaks regexes.** `\b` is a valid Python escape and collapses to a
  backspace byte; `\s` and `\d` are not and survive. Use the Write or Edit tools for regex code.
- **Verify a check by sabotaging it, and check the sabotage actually bit.** A check that passes
  when the logic is broken is worse than no check. It has twice happened here that a sabotage run
  passed, once because the edit did not apply and once because the case being tested had been
  removed along with the bug. If the sabotage does not fail, the test is proving nothing.
- **Read the rendered output, not only the source.** Almost every real bug in this project was
  found by looking at built HTML or live ETL output: an en dash inside an upstream organisation
  name, a cost axis printing "$0k" three times, signed numbers rendering as "+ 30", a classifier
  filing everything under one heading, Dutch articles in an English feed. None of them are visible
  in the code.
- **A fallback encoding chain succeeds wrongly.** Mac Roman and cp1252 both decode every byte of
  Microsoft's CSV; cp1252 silently turned Turkiye into TYrkiye and dropped Turkey off the map.
  Pass `encoding=` to `read_csv` whenever the publisher's encoding is known.
- **Feeds carry invisible characters.** A zero-width space is not whitespace to Python, so it
  survives a `\s+` collapse, shows the reader nothing and still counts against the 200-character
  copyright cap. `_clean` strips category Cf.
- **Distinguish blocked from dead when checking links.** Government sites refuse HEAD, refuse
  non-browsers and time out. Only 404 and 410 mean a citation is wrong. A checker that fails on
  someone else's bot wall trains everyone to ignore it. Never spoof a browser to get past one.
- **`write_dataset` is idempotent.** It skips the write when records are unchanged, because
  timestamps move every run and would otherwise commit churn daily. A commit means data moved.
- **When CSS looks wrong, check the production build before debugging.** The dev server serves
  stale scoped styles after component edits; restart it.
- **A `?` in terminal output is usually the Windows console**, not corrupt data. Check the bytes.
- **`documentElement.scrollWidth` counts clipped descendant overflow.** To test for real horizontal
  scroll, try `window.scrollTo(500, 0)` and see whether `scrollX` moves.
- **`var(--x)` with no fallback is not transparent, it is invalid.** An unresolvable custom
  property makes the whole declaration invalid at computed-value time, so `fill` falls back to its
  initial value, which is black. In `TimeMap` that would have painted every country with no data
  solid black with nothing in the markup looking wrong. Always `var(--x, fallback)` when the
  property may be absent.
- **`getComputedStyle` during a CSS transition returns the animated value**, so reading a colour
  immediately after toggling a class reports the old one. Verifying a state change means disabling
  the transition first, not sleeping and hoping.
- **`10 ** 25 != 1e25` in Python.** One is an exact integer, the other the nearest double. Compare
  `float(10 ** n) == value`.
- **A running maximum can never have a negative slope.** Fitting a trend to a frontier series and
  reporting "no progress" when the slope is negative means that branch can never fire. Say the
  series is monotone where the fit is shown.
- **Moving a component's styles out from under it leaves no styles.** `.leaders` lived scoped
  inside the homepage; when the capability page started using it and the homepage stopped, it
  rendered as a bulleted list. Shared furniture belongs in `global.css`.
- **A citation that cannot be verified is not published.** China's draft AI Law has no resolving
  primary or translated URL, so it is named in the jurisdiction summary and has no index entry.

## Design lock

Set from the tasteskill brief at `DESIGN_VARIANCE 7 / MOTION_INTENSITY 4 / VISUAL_DENSITY 7`.
Where the skill and the user's instruction conflict, the user's instruction wins.

- **One theme, semi-dark.** No section inverts. Tokens in `src/styles/global.css`.
- **One accent**, amber `#f2a950`, on a blue-slate ground. `--accent-2`, blue, is a DATA hue and
  not a second accent: it encodes governance wherever governance is plotted against exposure or
  capability, and appears nowhere else. `--ok` and `--warn` are for genuine state, never decoration.
- **Density over whitespace.** Section padding, type scale and table rows are all sized to the
  smallest gap that still separates two things. If a change makes the page taller without adding
  information, it is the wrong change.
- **The ground is graph paper**, not flat colour: a 56px grid at 5% opacity on `body`, a dot grid
  on `.section--sunk`, a diagonal hatch on `.section--hatch`. All CSS gradients; there are still
  no images.
- **Copy on a data page describes the figure and stops.** What it shows, over what period, from
  whom, and a notable number if there is one. No implication drawn for the reader: the legend and
  the key are the explanation. Argument belongs on `/about/` and `/methodology/`.
- **Long ranked lists show ten rows and put the tail in `<details class="reveal">`.** Use the
  shared `BarTable` component rather than writing another table.
- **One radius system.** `--r` containers and controls, `--r-pill` tags, `--r-mark` data marks.
- **Zero em-dashes and en-dashes anywhere**, including source data, which is normalised at ETL
  time by `normalise_dashes` in `common.py` with the unaltered original one link away. The
  permitted dash is the plain hyphen, and `npm run check:built` fails the build if one reaches the
  rendered HTML.
- **No images.** This is an index, not an article. Visual interest comes from the data.
- **No marketing hero.** The page opens on current figures, not a pitch. The provenance icon on
  each metric already demonstrates the sourcing claim, so stating it in prose was redundant.
- **No hand-rolled SVG icons**, no decorative dots, no eyebrows above section headings, no scroll
  cues, no version labels.
- Run `python etl/check_contrast.py` after any colour change.

## Data sources

Verified working, with licences, in `data/sources.json`. Backbone is Epoch AI (models, benchmarks,
clusters, CC BY 4.0), Microsoft AI Diffusion (147 economies, MIT), Eurostat enterprise AI adoption
(Decision 2011/833/EU), OpenAlex (research volume, CC0), and the news feed's eight: US Federal
Register and NIST (public domain), GOV.UK (OGL v3.0), European Commission (Decision 2011/833/EU),
Government of Canada (OGL Canada), arXiv cs.AI and cs.CY (metadata CC0), and the AI Incident
Database (ODbL, display only). Map geometry is Natural Earth, public domain.

Four datasets are our own, all CC BY 4.0: the Governance Readiness Index, the AI Law and Policy
Index, the Frontier Safety Framework Index and the Compute Threshold Index.

**Ruled out, and registered so that using them fails the build:**

- **Artificial Analysis**: free tier forbids redistribution.
- **Stanford AI Index**: CC BY-NC-ND, so its figures cannot be re-plotted.
- **METR time horizons**: their analysis repository carries no LICENSE file and its README points
  at one that is not there, so no reuse permission exists and the default is reserved. Their
  headline finding is stated as attributed prose with a link, which is a fact rather than their
  data. `/alignment/` says so on the page.

**Legal constraints** (detail in `docs/00-research-findings.md` section 3):

- EU sui generis database right is separate from copyright. Do not bulk-extract OECD.AI or IAPP.
  Our own coded index is our own work and sidesteps this.
- News aggregation is headline, short extract, publisher, canonical link. Never full text, never a
  hotlinked image. The 200-character snippet cap in `fetch_news.py` is the mechanism.
- AI Incident Database is ODbL. Display only; do not publish a derived database dump.
- Identify the bot honestly in the user agent. Daily, not hourly. These publishers give us the data
  for free.

## Deployment

Public repo, `main` branch, Cloudflare Workers static assets, `wrangler.jsonc` at the root.

**Cloudflare Workers Builds is connected and builds every push to `main`.** The Worker is named
`ai-safety-index`, which matches the `name` in `wrangler.jsonc`; if that name ever diverges,
`npx wrangler deploy` silently creates a second Worker instead of updating the one the domain
points at.

**How to check whether a push deployed, correctly.** Workers Builds reports as a GitHub *check run*
on the commit, not as a GitHub *deployment*. Looking for deployment records returns nothing even
when everything is working, which is how this file previously came to claim the opposite:

```bash
gh api repos/PhlegmaticPhox/ai-safety-index/commits/main/check-runs --jq '.check_runs[] | "\(.name): \(.status) \(.conclusion)"'
```

Cloudflare watches the repository over a webhook rather than through GitHub Actions, which matters
because `refresh-data.yml` pushes with the default `GITHUB_TOKEN` and GitHub deliberately does not
trigger workflows from those pushes. An Actions-based deploy would fire for hand-made commits and
silently skip every daily data refresh; the Cloudflare integration is not subject to that rule.

**A green build is not a visible change.** Build success only means the Worker was updated. If the
custom domain is routed to a different Worker or an older project, every build can succeed while
the domain serves something else entirely, and nothing in the build log says so.

`.github/workflows/refresh-data.yml` runs daily at 06:17 UTC, runs all guards before fetching,
builds the site before committing, and labels its commits `Data refresh` when a dataset moved or
`Pipeline heartbeat` when only the check time did.

**Live and indexable at https://aisafetytracker.org.** The `noindex` meta is gone and
`public/robots.txt` points crawlers at the sitemap, so canonical links, `og:url` and the sitemap
now matter for real rather than being dormant.

The Worker is named `ai-safety-index` and the GitHub repository is `ai-safety-index`, both from
before the rename. **Neither was renamed and neither should be casually.** Changing the `name` in
`wrangler.jsonc` does not rename the Worker: it creates a second one and leaves the domain pointing
at the first, with every build reporting success.

**The site origin is hardcoded in `astro.config.mjs`** as `https://aisafetytracker.org`, and is
deliberately not read from the environment. It was an env var for one day and was wrong twice in
that day: a default pointing at a domain that does not resolve, then a Cloudflare build variable
holding the scheme twice, which put `https://https/` in every canonical link, every og:url and all
thirty-two sitemap entries of the live site. `npm run check:built` now fails when the rendered
origin is not a plausible hostname, verified by sabotage.

## Working agreement

Matthew wants involvement only in decisions and payment, not build mechanics. Act rather than ask;
batch anything that genuinely needs him into one block.

Hard limits that are never worked around: creating accounts, entering passwords, and making
purchases are his, always.

He challenges analytically weak framing and is usually right to. The flagship visualisation was
originally compute concentration against regulation; he rejected it because compute is where models
are built, which says nothing about where they are used or governed. Before proposing any
comparison, be able to state plainly what links the two variables. If you cannot, it is decoration.

## Status

The homepage is a dashboard: one panel per section carrying that section's headline figures, with
the heading as the way in, plus a full-width choropleth that steps through reporting periods with
no JavaScript (`TimeMap`). Everything else lives on its own page.

Live pages: homepage, `/progress/`, `/capability/`, `/alignment/`, `/adoption/`, `/map/`,
`/policy/` plus eleven jurisdiction routes, `/news/` plus six category routes, `/sources/`,
`/about/`, `/methodology/` and the governance rubric, `/corrections/`, `/privacy/`, `/terms/`.

The split between `/progress/` and `/capability/` is inputs against outputs: capability is compute,
cost, who builds them and how they ship; progress is what comes out and how fast it is changing.
Benchmarks live on progress. Do not put them back on capability.

Built and not yet done:

- The law index covers eleven jurisdictions. Australia is far deeper than the rest because it was
  indexed first, which the page says out loud so the totals are not read as a comparison.
- `/progress/` is the only page that extends past the last observation. Every such number is
  labelled an extrapolation of a stated fit, with the window and both directions of bias printed
  next to it. Keep it that way or take it out.
- The news feed's alignment and progress categories depend on arXiv, which announces on weekdays
  only. A feed built at a weekend legitimately has none, and the page says so.
- US industry adoption is missing. Census BTOS has it, and its API needs a key, which needs an
  account, which is Matthew's to create and not mine.
- The Anthropic Economic Index is registered but unused: the release files are 77MB and 219MB,
  which is too much to pull daily without streaming aggregation.

## What this site has that the others do not

Four joins nobody else publishes. If a change would break one of them, it is the wrong change.

1. **Compute thresholds against actual models** (`/capability/#thresholds`). Every training-compute
   threshold written into law, with the count of models above each. Four exist, two are the same
   number, one is revoked and one was vetoed.
2. **Frontier safety frameworks side by side** (`/alignment/#frameworks`). Eight developers, eight
   incomparable scales, and who commits to stopping rather than to deciding. Includes the
   developers who have published nothing, because the absence is the finding.
3. **Safety research against capability research** (`/alignment/#research`). OpenAlex counts by
   year with the literal query printed next to every series, so the definition is arguable.
4. **What law applies where** (`/policy/`). Eleven jurisdictions, and the number the page leads on
   is how few binding instruments name AI at all.
5. **How far behind the open-weight frontier is** (`/capability/#open-weights`). Two running
   maxima of training compute, read horizontally rather than vertically: the gap in months
   between the overall frontier reaching a level and an open-weight model doing so. Publishing
   weights is the one release decision nobody can reverse, and this is the only measure of it
   that is about capability rather than count.

Phases and exit tests in `docs/02-plan.md`. Unbuilt ideas, scored, in `docs/01-ideas-backlog.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
