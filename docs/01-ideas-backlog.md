# Ideas Backlog — Widgets, Infographics, Content

Running brainstorm. Nothing here is committed. Items are scored:

- **Value** = how much a visitor gains / how differentiated vs existing sites
- **Cost** = build effort
- **Data** = do we already have a verified, legally clean source? (see `00-research-findings.md`)

---

## A. Signature pieces (the things people would link to)

### A1. The Divergence Map ★ flagship
World map, two encodings at once: **compute concentration** (choropleth or proportional symbols
from Epoch `gpu_clusters.csv` — country, MW, H100-equivalents) versus **regulatory bindingness**
(our own coded index). The visual punchline: the countries building the compute are not the
countries writing the binding rules.
Toggle layers: compute · regulation · usage (Anthropic Economic Index per-capita) · incidents.
*Value: very high — nobody has this. Cost: high. Data: verified, all Tier A.*

### A2. Capability–Governance Timeline
One horizontal time axis, two tracks. Above: capability milestones (model releases scaled by
training compute, benchmark saturation points). Below: governance events (EU AI Act stages, EOs,
summits, standards). Shows the lag between capability arriving and rules responding.
*Value: very high. Cost: medium. Data: Epoch + our policy timeline.*

### A3. Benchmark Saturation Dashboard
Every major benchmark as a small multiple, showing score-over-time and the date human-expert
baseline was crossed. The story: benchmarks are being saturated faster each generation.
Derived metric worth computing: **time-from-release-to-saturation**, trending down.
*Value: high. Cost: medium. Data: Epoch `benchmarks.csv`, verified current.*

### A4. "What does this number mean?" provenance popovers
Click any datapoint anywhere on the site: source, licence, retrieval date, canonical link,
and a plain-English note on what it does and does not measure.
*Value: high (unique; also our legal shield). Cost: low if built into the data layer from day one —
expensive to retrofit. Build first.*

---

## B. Explainer / lay-reader layer

### B1. Dual-track prose
Every explainer page renders at two depths from one source: a plain-language track and a
technical track, toggled site-wide and remembered. Not two pages — one page, progressive
disclosure, so links never break.
*Value: high (the corroborated gap). Cost: medium — mostly an authoring convention.*

### B2. Scale intuition widget
"GPT-4 used ~2e25 FLOP" means nothing to a lay reader. Slider comparing training compute to
tangible referents (household electricity-years, transatlantic flights, a country's daily power).
*Value: high for lay audience. Cost: low. Data: Epoch compute + power columns.*

### B3. Jargon layer
Hover any term (RLHF, mesa-optimisation, eval, red-team, compute threshold) for a definition
plus a link to the full explainer. One JSON glossary, one Astro component.
*Value: medium-high. Cost: low. Compounds across the whole site.*

### B4. "Who believes what" disagreement map
Honest rendering of the actual spread of expert opinion on risk, rather than picking a side.
Positions, who holds them, strongest argument each way, what would change their mind.
*Value: high and genuinely missing. Cost: medium (editorial, needs care to stay fair).*

---

## C. Policy layer

### C1. Regulation Explorer
Per-jurisdiction cards: what is in force, what is pending, what it actually binds, penalties,
and the primary-source link. Filterable by jurisdiction, status, risk tier, sector.
*Value: high. Cost: medium-high (editorial). Must be our own coding from primary sources —
not extracted from OECD/IAPP (database right, see findings §3.2).*

### C2. EU AI Act compliance clock
Live countdown to each staged obligation, with the deferrals applied (Annex III moved to Dec 2027,
Annex I to Aug 2028, Art. 50 transparency Aug 2026, legacy GPAI Aug 2027). This is genuinely
confusing right now and a clean tracker is immediately useful.
*Value: high, immediately useful. Cost: low. Data: primary legal text.*

### C3. Live policy feed
Federal Register API + GOV.UK Atom + EC RSS, deduped, tagged by jurisdiction and topic,
headline + short snippet + source link only. Public-domain/OGL sources lead.
*Value: high. Cost: medium. Data: verified, cleanest licences available.*

### C4. Compute threshold comparator
Different regimes trigger on different FLOP thresholds (EU 1e25, US EO 1e26, etc.). Plot which
actually-released models cross which threshold, live from Epoch data. Shows how fast thresholds
are being outrun.
*Value: high, very original. Cost: low-medium. Data: Epoch `notable_ai_models.csv`.*

---

## D. Smaller widgets

- **D1. Frontier tracker strip** — sitewide header: newest frontier model, days since, compute.
- **D2. Incident ticker** — recent AIID entries, with ODbL attribution.
- **D3. Model family tree** — lineage/base-model graph from the `Base model` column in Epoch data.
- **D4. Cost-to-train curve** — training cost over time; pairs with a falling inference-cost curve.
- **D5. Safety-team headcount vs capability spend** — if a credible source exists. Needs research.
- **D6. Where to start** — 5-question router that sends a visitor to the right entry point.
- **D7. Glossary-driven search** — client-side, no server, over content + data + glossary.
- **D8. Data changelog** — public log of every pipeline run and what changed. Trust feature.

---

## E. Deliberately not doing

- **Predictions/forecasts of our own.** Publishing our own frontier projections invites being wrong
  in public. Instead: render *other people's* forecasts side by side with their track records and
  stated assumptions. More useful, more honest, more defensible.
- **Anything requiring Artificial Analysis data** — free tier forbids redistribution.
- **Re-plotting Stanford AI Index figures** — CC BY-NC-ND.
- **Accounts, comments, newsletters at launch** — drags in GDPR, moderation, and spam for no v1 gain.
