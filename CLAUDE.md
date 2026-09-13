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

Astro 5 + TypeScript, static output, **zero client JavaScript** (keep it that way; charts render to
SVG at build time). Python stdlib ETL plus `certifi`. Geist and Geist Mono via Fontsource.
Phosphor icons via `astro-icon`. Hosted on Cloudflare Workers static assets, data refreshed by a
daily GitHub Actions cron.

```bash
npm install
npm run etl          # fetch and process every source
npm run etl:offline  # rebuild from cache, no network
npm run dev          # http://localhost:4321
npm run build

python etl/common.py                          # licence guard + idempotence self-check
python etl/fetch_policy_feeds.py --self-check # snippet cap, relevance filter, dash normalisation
python etl/check_contrast.py                  # palette against WCAG AA
```

All three checks run in CI before any data is written.

## House rules, learned the hard way

Each of these cost real debugging time. Do not relearn them.

- **`Provenance.astro` must emit phrasing content only.** Spans, never `div`/`p`/`dl`. The marker
  sits inside `<p>`, and the HTML parser auto-closes a paragraph when it meets a block-level tag,
  silently hoisting the panel out and leaving an empty paragraph behind.
- **Never run a bulk regex over source files.** A project-wide dash sweep once rewrote a
  normalisation line *and the assertion guarding it* into a matching pair that passed while doing
  nothing. Edit deliberately, and assert that every string replacement actually matched.
- **Write dash characters as escape sequences in code**, never as the literal character, so a
  text-level sweep cannot reach them. See `_clean` in `etl/fetch_policy_feeds.py`.
- **Multi-layer heredoc escaping breaks regexes.** `\b` is a valid Python escape and collapses to a
  backspace byte; `\s` and `\d` are not and survive. Use the Write or Edit tools for regex code.
- **Verify a check by sabotaging it.** A check that passes when the logic is broken is worse than
  no check.
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
- **One accent**, amber `#e9a23b`. `--ok` and `--warn` are for genuine state, never decoration.
- **One radius system.** `--r` containers and controls, `--r-pill` tags, `--r-mark` data marks.
- **Zero em-dashes and en-dashes anywhere**, including feed extracts, which are normalised at ETL
  time with the unaltered original one link away. The permitted dash is the plain hyphen.
- **No images.** This is an index, not an article. Visual interest comes from the data.
- **No marketing hero.** The page opens on current figures, not a pitch. The provenance icon on
  each metric already demonstrates the sourcing claim, so stating it in prose was redundant.
- **No hand-rolled SVG icons**, no decorative dots, no eyebrows above section headings, no scroll
  cues, no version labels.
- Run `python etl/check_contrast.py` after any colour change.

## Data sources

Verified working, with licences, in `data/sources.json`. Backbone is Epoch AI (models, benchmarks,
clusters, hardware, CC BY 4.0), Microsoft AI Diffusion (147 economies, MIT), and four official
policy feeds: US Federal Register and NIST (public domain), GOV.UK (OGL v3.0), European Commission
(Decision 2011/833/EU).

**Ruled out, and registered so that using them fails the build:**

- **Artificial Analysis**: free tier forbids redistribution.
- **Stanford AI Index**: CC BY-NC-ND, so its figures cannot be re-plotted.

**Legal constraints** (detail in `docs/00-research-findings.md` section 3):

- EU sui generis database right is separate from copyright. Do not bulk-extract OECD.AI or IAPP.
  Our own coded index is our own work and sidesteps this.
- News aggregation is headline, short extract, publisher, canonical link. Never full text, never a
  hotlinked image. The 200-character snippet cap in `fetch_policy_feeds.py` is the mechanism.
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

Phase 0 and Phase 1 complete: citation layer, four ETL modules, and the dashboard homepage.
Phase 2 is the exposure against governance readiness map. Phases and exit tests in `docs/02-plan.md`.
Unbuilt ideas, scored, in `docs/01-ideas-backlog.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
