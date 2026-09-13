# Research Findings — AI Safety Index Site

Compiled 2026-09-13. Every endpoint below was probed live, not assumed.
Re-verify before relying on any of it in six months.

---

## 1. Landscape: who already does this

| Site | Does well | Does not do |
|---|---|---|
| **Epoch AI** (epoch.ai) | Best-in-class compute/model/hardware data, CC BY, real CSVs | Researcher-facing; almost no policy; no explainers; no news |
| **Stanford HAI AI Index** | Comprehensive annual survey | 400-page PDF, stale between releases, non-interactive, **CC BY-NC-ND** |
| **OECD.AI Policy Observatory** | 1,300+ policy initiatives, 80+ jurisdictions | Dry, hard to navigate, no capability data, no bulk export/API found |
| **IAPP Global AI Law Tracker** | Authoritative legal detail | Aimed at compliance professionals; partly gated |
| **LMArena / Artificial Analysis** | Live model leaderboards | Capability only; no safety, no policy. AA free tier forbids redistribution |
| **FLI AI Safety Index** | Graded company safety practices, 37 indicators | Twice-yearly snapshot; company-scoped only |
| **AI Safety Atlas / aisafety.info** | Excellent layered explainers, 600+ pages | No live data, no policy tracking |
| **AI Incident Database** | Curated real-world harms | Incidents only; ODbL share-alike |
| **Alignment Forum / LessWrong** | Depth of research discussion | Impenetrable to lay readers |

### The gap (externally corroborated)

Practitioners report the field is "hard to navigate" and that "there is no single overview of all the
work being done ... and of how the different efforts link together"
([EA Forum](https://forum.effectivealtruism.org/posts/mX2eiWYJBxRkS6nkF/a-map-of-work-needed-to-achieve-safe-ai),
[BlueDot](https://blog.bluedot.org/p/ai-safety-articles-we-would-like-to-exist)).

Four specific, fillable gaps:

1. **No site joins capability + policy + incidents on one screen.** You can see the frontier
   capability curve (Epoch) or the regulatory state (OECD/IAPP), never both together.
2. **No layered reading.** Sites target either lay readers *or* researchers. Nobody does one page
   that serves both via progressive disclosure.
3. **No compute-vs-regulation map.** The compute is in the US and China; the binding regulation is in
   the EU. That divergence is the single most interesting story in AI governance and nobody
   renders it as a live map. We have the data to do it (see §2).
4. **No per-datapoint provenance.** Almost every site shows a chart with a source note at the
   bottom. None let you click a point and see exactly where that number came from.

Gap 4 is both the differentiator *and* the legal safety mechanism — see §3.

---

## 2. Verified data sources

### Tier A — CC BY 4.0, direct download, no auth, no key. Use freely with attribution.

**Epoch AI** — `robots.txt` permits `/data/`. Licence: CC BY 4.0.

| Endpoint | Size | Contents |
|---|---|---|
| `https://epoch.ai/data/notable_ai_models.csv` | 2.24 MB | Model registry: compute (FLOP), params, org, country, dates, training cost, power draw, hardware |
| `https://epoch.ai/data/large_scale_ai_models.csv` | 1.10 MB | Frontier subset |
| `https://epoch.ai/data/benchmarks.csv` | 3.75 MB | Benchmark runs w/ scores + dates. Confirmed current to 2026-09-10 |
| `https://epoch.ai/data/gpu_clusters.csv` | 304 KB | **482 clusters**: country, owner, power capacity (MW), chip type/qty, location, status |
| `https://epoch.ai/data/ml_hardware.csv` | 97 KB | Accelerator specs over time |
| `https://epoch.ai/data/ai_companies.csv` | 2.5 KB | Company reference table |

`gpu_clusters.csv` country split: China 188, USA 119, Japan 25, France 14, South Korea 12,
Germany 11, Italy 9, Brazil 9, Russia 8, UK 6, Canada 5. **This is the world-map spine.**

Caveat: `data_centers.csv` / `machine_learning_hardware.csv` return an HTML redirect stub, not CSV.
Do not use those names.

**Our World in Data** — CC BY 4.0. `robots.txt` is sitemap-only (no restrictions).
Requires following redirects (`curl -L`), else you get an empty body.

- `https://ourworldindata.org/grapher/{slug}.csv`
- `https://ourworldindata.org/grapher/{slug}.metadata.json` — machine-readable provenance
- `https://ourworldindata.org/grapher/{slug}.config.json`

Useful slugs: `artificial-intelligence-training-computation`, `artificial-intelligence-parameter-count`,
`share-companies-using-artificial-intelligence`, `artificial-intelligence-patents-submitted`,
`newly-funded-artificial-intelligence-companies`, `share-artificial-intelligence-job-postings`.

**LMArena** — `huggingface.co/datasets/lmarena-ai/leaderboard-dataset`, CC BY 4.0, parquet,
historical leaderboard snapshots. Last updated 2026-09-12.

**Anthropic Economic Index** — `huggingface.co/datasets/Anthropic/EconomicIndex`, CC BY 4.0.
Releases: 2025_02_10, 2025_03_27, 2025_09_15, 2026_01_15, 2026_03_24, and later.
Country- and US-state-level usage breakdowns from the 2025-09 release onward.
**This is the "AI model use by country" map layer.**

### Tier B — public domain / open government licence. Best sources for the news feed.

| Source | Endpoint | Licence |
|---|---|---|
| **US Federal Register** | `https://www.federalregister.gov/api/v1/documents.json?conditions[term]=artificial+intelligence&order=newest` | US Gov **public domain** |
| **GOV.UK** | `https://www.gov.uk/search/news-and-communications.atom?keywords=artificial+intelligence` | **OGL v3.0** |
| **European Commission** (digital-strategy) | `https://digital-strategy.ec.europa.eu/en/rss.xml` | EC reuse decision 2011/833/EU |
| **NIST** | `https://www.nist.gov/news-events/news/rss.xml` | US Gov public domain |

Federal Register returned **1,565** matching documents with structured agency/date/URL fields.
It is the strongest single policy source found: free, keyless, structured, legally unencumbered.

### Tier C — usable with care

- **arXiv** `https://export.arxiv.org/rss/cs.AI` — 273 items. Metadata reuse fine; abstracts are
  author-copyright, so link rather than republish in full.
- **AI Incident Database** — weekly snapshots at
  `https://pub-72b2b2fc36ec423189843747af98f80e.r2.dev/backup-YYYYMMDDHHMMSS.tar.bz2`.
  **ODbL** — share-alike applies to any derived database we publish. GraphQL API is
  origin-locked ("API access is restricted to authorized domains"), so snapshots only.
- Lab blogs (OpenAI `openai.com/news/rss.xml` = 1192 items; FLI `futureoflife.org/feed/` = 20).
  Anthropic / Epoch / AISI feed URLs not yet resolved — their obvious paths 404.

### Tier D — ruled out

- **Artificial Analysis** — free API tier is *internal use only, no redistribution*. Cannot power a
  public site without a commercial agreement. Link out instead.
- **Stanford AI Index** — **CC BY-NC-ND**. No derivative charts, no commercial use. Cite and link,
  quote sparingly, never re-plot their figures.

---

## 3. Legal constraints (secondary research — not legal advice)

1. **Facts are not copyrightable; their arrangement can be.** Re-plotting numbers from a CC BY source
   with attribution is fine. Re-plotting a CC BY-NC-ND figure is not.
2. **EU sui generis database right** — separate from copyright. Protects *substantial* extraction
   from a database where the maker made substantial investment in obtaining/verifying/presenting it.
   15-year term. Applies even to public pages with no personal data. So: do not bulk-extract OECD.AI
   or IAPP. Link out, or build our own coded dataset from primary legal sources.
3. **News aggregation** — headline + short snippet + link to source is the defensible pattern.
   Full-text republication is not. Several EU states have press-publisher rights; the safe posture
   is: title, <=200 char snippet, publisher name, canonical link, no hotlinked images.
4. **ODbL share-alike** (AIID) — if we publish a derived database we must licence it alike.
   Cleanest: consume it for display, do not redistribute a derived dump, or accept ODbL on that slice.
5. **GDPR** — avoidable entirely: no accounts, no tracking cookies, privacy-preserving analytics
   (Cloudflare Web Analytics / Plausible), no newsletter at launch.
6. **Accessibility** — WCAG 2.1 AA is the right target (UK Equality Act; EU Accessibility Act 2025).
   Charts need table fallbacks and non-colour-dependent encodings.

**Design principle that follows:** a *citation-first architecture*. Every number carries a source id,
licence, retrieval timestamp, and canonical URL through the pipeline to the rendered tooltip. That
turns the legal requirement into the product's best feature, and makes a takedown request a
one-line data change rather than an audit.

---

## 4. Cost

| Item | Choice | Cost |
|---|---|---|
| Hosting | Cloudflare Pages (unlimited bandwidth, free tier) | £0 |
| Build/ETL | GitHub Actions (free on public repos) | £0 |
| Analytics | Cloudflare Web Analytics (cookieless) | £0 |
| Data | All Tier A/B sources are keyless and free | £0 |
| Domain | optional, `.org` / `.ai` | £0–£60/yr |

**Total: £0/yr, plus an optional domain.** No paid API is required for anything in scope.

---

## 5. Toolchain present

Node v24.19.0 · npm 11.17.0 · Python 3.14.7 · git 2.55.0 · no `gh`, no `pnpm`.
