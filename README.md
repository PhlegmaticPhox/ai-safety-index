# AI Safety Index

An independent, cited index of AI capability, governance and safety.

Capability data, governance data and incident data live on separate sites, in separate formats,
aimed at separate audiences. This puts them on one screen — and shows the provenance, licence and
limitations of every figure rather than asking you to take it on trust.

**Status: Phase 0.** Foundation and citation layer working end to end. See [`docs/02-plan.md`](docs/02-plan.md).

---

## Run it

```bash
npm install
npm run etl      # fetch and process source data
npm run dev      # http://localhost:4321
```

`npm run etl -- --offline` rebuilds from cached raw data with no network.

Requires Node 20+ and Python 3.11+. The ETL uses the Python standard library only.

---

## How the citation layer works

This is the one architectural rule the whole project rests on, so it is worth understanding
before changing anything.

1. **[`data/sources.json`](data/sources.json)** is the registry. Every source is declared once,
   with its licence, attribution string, canonical URL, update cadence and — importantly — its
   known limitations.

2. **Every processed record carries a `source_id`.** Records stay small; licence and attribution
   are resolved by joining against the registry at render time. Attribution becomes a join rather
   than a habit, so it cannot be forgotten.

3. **Both ends guard the licence.** `etl/common.py:guard()` refuses to *write* a dataset whose
   source forbids republication; `src/lib/sources.ts:assertRenderable()` refuses to *render* one.
   Two checks because data can also arrive hand-authored rather than through the ETL.

   Sources that must not be republished — Artificial Analysis (free tier forbids redistribution)
   and the Stanford AI Index (CC BY-NC-ND, no derivative charts) — are registered *precisely so
   that wiring them in fails the build* instead of silently shipping.

4. **`<Provenance>`** turns a `source_id` into the click-through popover on any figure. It uses
   the native Popover API: no JavaScript, keyboard accessible, native light-dismiss.

Adding a source therefore means: register it in `sources.json`, write an ETL module that stamps
`source_id` onto each record, and pass `source` to `<Provenance>`. Nothing else.

> **If you edit `Provenance.astro`, keep its output phrasing-only** — spans, no `div`/`p`/`dl`.
> The marker sits inside `<p>`, and the HTML parser auto-closes a paragraph when it meets a
> block-level tag, which silently hoists the panel out and leaves an empty paragraph behind.

---

## Layout

```
data/sources.json      source registry — licences and attribution live here
data/processed/        generated JSON, committed so data changes are reviewable diffs
data/raw/              fetched artefacts, gitignored
etl/                   Python fetchers, one per source. Idempotent.
src/components/        Astro components, including Provenance
src/lib/sources.ts     registry access + the render-side licence guard
docs/                  research findings, idea backlog, build plan
```

Processed JSON is committed on purpose: it makes every data change a reviewable diff and lets the
site build with no network.

---

## Data and licences

All data is reproduced from third parties under their own licences and remains theirs. Each
source's terms are recorded in `data/sources.json` and shown in the UI next to the figures it
produces. Current sources include Epoch AI and Our World in Data (CC BY 4.0), Microsoft's AI
Diffusion Report (MIT), and the US Federal Register and GOV.UK (public domain / OGL v3.0).

Original work in this repository — site code, written explainers, and the Governance Readiness
Index — is CC BY 4.0.

Found an error? Open an issue. Corrections are logged publicly rather than quietly patched.

---

## Checks

```bash
python etl/common.py    # self-check on the licence guard
npm run build           # type-checks and fails on any licence violation
```
