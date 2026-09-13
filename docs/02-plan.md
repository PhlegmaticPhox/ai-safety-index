# Build Plan

Decisions locked 2026-09-13. Supersedes nothing; see `00-research-findings.md` for evidence
and `01-ideas-backlog.md` for the unbuilt idea pool.

---

## 0. Decisions locked

| Decision | Choice | Rationale |
|---|---|---|
| Identity | **Balanced hub** | Homepage is a live "state of AI" dashboard; each panel a door into a section |
| Original dataset | **AI Governance Readiness Index, ~25 jurisdictions** | Our own coding from primary sources. Sidesteps EU database right; it is the differentiator |
| Repo | **Public** | Unlimited free Actions minutes; it *is* the portfolio artifact |
| Domain | **Custom** (user purchases) | Free `*.pages.dev` works until then |
| First signature build | **Exposure vs Governance map** (revised) | See §1 |

### §1 Why the flagship changed

Original proposal was compute-concentration vs regulation. Rejected, correctly: the EU AI Act
regulates *placing on the market and use within the EU* regardless of training location. "Strict
rules, no compute" is the design working, not a divergence. Compute location is a chokepoint story
(export controls, training-compute thresholds) and belongs on its own page, not paired with
regulation.

The comparison that carries meaning is **exposure vs readiness**: how much a population actually
encounters AI systems, against how prepared its jurisdiction is to govern them.

Data confirmed available:
- **Exposure** — Microsoft AI Diffusion, 147 economies, population-normalised, **MIT licence**,
  `github.com/microsoft/ai-diffusion-report`, three time points (H1 2025 → Q1 2026).
- **Readiness** — our own index (§4).
- **Derived: Governance Gap** = exposure percentile − readiness percentile. High-exposure,
  low-readiness jurisdictions are the story.

Triangulation, not single-vendor: Microsoft telemetry + Anthropic Economic Index + OpenAI Signals
measure different populations by different methods. We show all available series and their
disagreement rather than picking one and implying false precision. The disagreement is itself
a finding worth rendering.

---

## 2. Architecture

```
ai-safety-index/
├── data/
│   ├── sources.json        # source registry: id, name, licence, attribution, url, cadence
│   ├── raw/                # fetched artefacts, gitignored above 1 MB
│   └── processed/          # typed JSON consumed by the site
├── etl/                    # Python. One module per source. Idempotent, re-runnable.
│   ├── fetch_epoch.py
│   ├── fetch_microsoft_diffusion.py
│   ├── fetch_owid.py
│   ├── fetch_policy_feeds.py
│   └── build_governance_index.py
├── src/
│   ├── components/         # Astro islands: charts, map, provenance popover
│   ├── content/            # MDX explainers, dual-track
│   ├── data/               # generated JSON imported at build time
│   └── pages/
└── .github/workflows/      # cron ETL → commit → Pages deploys on push
```

**Stack:** Astro 5 + TypeScript, static output, islands only where interaction is required.
**Charts:** Observable Plot, rendered to SVG *at build time* — zero client JS for static charts.
**Map:** d3-geo + Natural Earth TopoJSON (public domain). No tile server, no API key, no
attribution entanglement. Deliberately not MapLibre — we do not need tiles.
**ETL:** Python stdlib where possible. Output committed as JSON so the site builds offline and
every data change is a reviewable diff.
**Host:** Cloudflare Pages. **CI:** GitHub Actions cron.

### The one non-negotiable: citation-first

Every processed record carries `source_id`. `sources.json` holds licence, attribution string, and
canonical URL once. A `<Provenance>` component resolves `source_id` at render time into the
click-through popover.

Consequences, all good:
- Attribution is structurally impossible to forget — it is a join, not a habit.
- A takedown request is a one-line change in `sources.json`, not an audit.
- The "click any number to see where it came from" feature falls out for free.

This is cheap now and expensive later. It goes in before the first chart.

---

## 3. Phases

### Phase 0 — Foundation
Repo, Astro scaffold, `sources.json` schema, `<Provenance>` component, one end-to-end vertical
slice (one dataset → one chart → working popover), CI deploying to Pages.
**Exit test:** a number on a deployed page, clickable, showing correct licence and retrieval date.

### Phase 1 — Data spine
ETL for Epoch (models, benchmarks, GPU clusters, hardware), Microsoft Diffusion, OWID.
Scheduled, idempotent, with a failure mode that serves stale data rather than breaking the build.
**Exit test:** `make etl` from clean checkout reproduces every JSON in `data/processed/`.

### Phase 2 — Flagship map + timeline
Exposure vs Governance Readiness map with layer toggle and gap view.
Capability–Governance Timeline (capability milestones above axis, governance events below).
**Exit test:** both work with keyboard only and have table fallbacks.

### Phase 3 — Governance Readiness Index
~25 jurisdictions coded from primary sources (§4). Public methodology page. Versioned.

### Phase 4 — Explainer layer
Dual-track prose (lay/technical toggle from one source), glossary hover layer, scale-intuition
widget, "who believes what" disagreement map.

### Phase 5 — Live policy feed
Federal Register + GOV.UK + EC + NIST. Headline, ≤200 char snippet, publisher, canonical link.
No full text, no hotlinked images. Deduped, tagged by jurisdiction and topic.

### Phase 6 — Benchmarks, incidents, polish
Benchmark saturation dashboard, compute-threshold comparator, incident ticker,
WCAG 2.1 AA pass, SEO, structured data, launch.

---

## 4. Governance Readiness Index — methodology sketch

Scored **only** from primary sources (statute text, official guidance, regulator publications).
Never extracted from OECD.AI or IAPP — see findings §3.2, EU database right.

Proposed dimensions, each 0–4, equally weighted until there is reason to do otherwise:

1. **Binding law in force** — does anything actually bind, or is it voluntary guidance?
2. **Scope** — economy-wide, sectoral, or narrow?
3. **Enforcement capacity** — is there a named regulator with powers and budget?
4. **Transparency obligations** — disclosure, labelling, documentation duties
5. **Frontier/systemic-risk provisions** — compute thresholds, model evaluation duties
6. **Redress** — can an affected person actually do anything?

Every score carries a citation to the specific instrument and article, plus the coding date.
Published as open data. A methodology page states the limitations plainly — including that
"readiness" is not "goodness", and that a high score is not an endorsement.

**Honesty constraint:** this is our editorial judgment, presented as such. Not laundered as
objective measurement.

---

## 5. What I cannot do, and what you must

Hard limits I will not work around:

| Task | Who | Why |
|---|---|---|
| Create GitHub / Cloudflare accounts | **You** | I am prohibited from creating accounts |
| Enter any password | **You** | Prohibited |
| Purchase the domain | **You** | Prohibited from entering payment details |
| Everything else | **Me** | Code, ETL, content, local git, config via CLI |

Minimum-involvement path: you do one auth session (GitHub account + a token for push, Cloudflare
account + connect repo, buy domain). After that I work autonomously and you review output.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Upstream schema change breaks ETL | Validate on fetch; fail loudly in CI; serve last-good data |
| Epoch/OWID rate-limit or block us | Cache raw; identify our bot honestly; daily not hourly |
| Governance Index challenged as wrong | Cite every score to article level; public methodology; correction log |
| Data goes stale and site loses trust | Public "last updated" per dataset; visible staleness warnings |
| Scope creep across six phases | Phase exit tests above; ideas stay in backlog until a phase closes |
| ODbL contamination from AIID | Display only; do not publish a derived dump |
