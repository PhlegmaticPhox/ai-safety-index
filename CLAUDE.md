# AI Safety Index

An independent, cited index of AI capability, governance and safety.

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
python etl/build_governance.py --self-check      # scoring rubric
python etl/build_policy_index.py --self-check    # schema and coverage
python etl/fetch_microsoft_diffusion.py --self-check  # source encoding
python etl/check_contrast.py                     # palette against WCAG AA

python etl/build_governance.py --check-links     # probe every cited instrument
python etl/build_policy_index.py --check-links   # same, for the law index
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

## Design lock

Set from the tasteskill brief at `DESIGN_VARIANCE 7 / MOTION_INTENSITY 4 / VISUAL_DENSITY 7`.
Where the skill and the user's instruction conflict, the user's instruction wins.

- **One theme, semi-dark.** No section inverts. Tokens in `src/styles/global.css`.
- **One accent**, amber `#f2a950`, on a blue-slate ground. `--accent-2`, blue, is a DATA hue and
  not a second accent: it encodes governance wherever governance is plotted against exposure or
  capability, and appears nowhere else. `--ok` and `--warn` are for genuine state, never decoration.
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
(Decision 2011/833/EU), and the news feed's eight: US Federal Register and NIST (public domain),
GOV.UK (OGL v3.0), European Commission (Decision 2011/833/EU), Government of Canada (OGL Canada),
arXiv cs.AI and cs.CY (metadata CC0), and the AI Incident Database (ODbL, display only). Map
geometry is Natural Earth, public domain. Two datasets are our own: the Governance Readiness Index
and the AI Law and Policy Index, both CC BY 4.0.

**Ruled out, and registered so that using them fails the build:**

- **Artificial Analysis**: free tier forbids redistribution.
- **Stanford AI Index**: CC BY-NC-ND, so its figures cannot be re-plotted.

**Legal constraints** (detail in `docs/00-research-findings.md` section 3):

- EU sui generis database right is separate from copyright. Do not bulk-extract OECD.AI or IAPP.
  Our own coded index is our own work and sidesteps this.
- News aggregation is headline, short extract, publisher, canonical link. Never full text, never a
  hotlinked image. The 200-character snippet cap in `fetch_news.py` is the mechanism.
- AI Incident Database is ODbL. Display only; do not publish a derived database dump.
- Identify the bot honestly in the user agent. Daily, not hourly. These publishers give us the data
  for free.

## Deployment

Public repo, `main` branch, Cloudflare Workers static assets on a custom domain. Every push
rebuilds. `.github/workflows/refresh-data.yml` runs daily at 06:17 UTC, runs all guards before
fetching, builds the site before committing, and labels its commits `Data refresh` when a dataset
moved or `Pipeline heartbeat` when only the check time did.

**At launch, remove the `noindex` meta in `src/layouts/Base.astro`.** It is there deliberately so a
half-built index is not crawled.

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

Live pages: homepage, `/capability/`, `/map/`, `/news/` plus six category routes, `/adoption/`,
`/policy/` and `/policy/australia/`, `/sources/`, `/about/`, `/methodology/` and the governance
rubric, `/corrections/`, `/privacy/`, `/terms/`.

Built and not yet done:

- The law index covers Australia only. The structure takes more jurisdictions without changes;
  each one is a research job, not an engineering one.
- The news feed's alignment and progress categories depend on arXiv, which announces on weekdays
  only. A feed built at a weekend legitimately has none, and the page says so.
- US industry adoption is missing. Census BTOS has it, and its API needs a key, which needs an
  account, which is Matthew's to create and not mine.
- The Anthropic Economic Index is registered but unused: the release files are 77MB and 219MB,
  which is too much to pull daily without streaming aggregation.

Phases and exit tests in `docs/02-plan.md`. Unbuilt ideas, scored, in `docs/01-ideas-backlog.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
