# /datacentres/: work in progress, waiting for data

Temporary. Delete this file in the commit that finishes the page.

The owner asked for a Datacentres page: a large map that pans and zooms, a
hover preview per site (owner, when built, size in watts, compute, users,
training or inference, renewable or fossil, evaporative or closed-loop
cooling), a list sortable by category, size and owner, and the share of all
datacentres (count, power, water) that AI accounts for. Epoch AI's data is the
backbone and must be cited on the page.

The first session could not reach epoch.ai, iea.org or any other data host: the
environment's network policy was changed mid-session and did not apply to the
running container. **This branch does not build yet**, because the page and
`scripts/check-lib.mjs` import `data/processed/ai-datacentres.json` and
`data/processed/datacentre-shares.json`, which do not exist until the ETL below
writes them. No placeholder data has been committed, and none should be.

## Done, and tested in Chromium

- `src/components/ZoomMap.astro`: the map. Zero client JavaScript, as the site
  requires. Read its header comment before changing it; every detail in it was
  found by testing, not assumed.
  - Pan is native scrolling of `.zmap__view`. Zoom is a radio group (1, 2, 4, 8
    and 16 times) that sets the canvas width; the minus and plus controls are
    labels for the neighbouring level.
  - Zoom stays centred through a lattice of scroll-snap lines (768 columns,
    384 rows) spread by percentage: after a layout change Chromium re-snaps to
    the same snap target, which is the same map position at any width.
    Measured: pan to (0.70, 0.30) at 4x, then 8x, 16x and back to 2x, and the
    centre stays at (0.70, 0.30). The lines must span the whole map in the
    other axis or Chromium stops snapping once scrolled; at 1x only the centre
    lines are targets, or the first zoom lands in the top-left corner.
  - Markers are HTML placed with margins, never `position` or `transform`, so
    the hover card's containing block is `.zmap__frame` outside the scroller
    and is never clipped. `container-type` sits on the frame, not the view, for
    the same reason. The card attaches with anchor positioning, fallbacks
    anchored at an edge of the marker; a tap opens it as a native popover,
    which on a phone is a sheet along the bottom of the screen.
  - Markers can show two magnitudes: `d` is the ring (power at completion)
    and `fill` the disc inside it (power operating now), area-true.
  - Land is `world-atlas/land-110m` with Antarctica dropped. A coastline mesh
    or `topojson.merge` both drew a wedge across Russia at the antimeridian.
- `src/lib/geo.ts`: `projectLand()` (land, borders and a `place(lon, lat)` in
  the same projection and fit as `projectWorld()`), and `bounds` on every
  `CountryShape`.
- `src/pages/datacentres/index.astro`: the page, written against the record
  shape below. Masthead, bento, map with stage filters and a size key, the
  AI-against-all table, the sortable list, and a gaps section. The list is a
  grid with ARIA table roles; sorting is a radio pointing each row's CSS
  `order` at a rank carried as a custom property, so there is one copy of the
  rows and the map's links to `#site-<id>` always land.
- `src/layouts/Base.astro`: Datacentres in the nav after Capability. The row
  now first fits at 995px (measured every 5px with the row forced on), so the
  breakpoint moved from 960 to 1050, keeping the documented 55px headroom.
- `src/pages/glossary.astro`: IT power, H100 equivalent, evaporative cooling,
  closed-loop cooling.
- `scripts/check-lib.mjs`: `projectLand` against `projectWorld`, and every site
  must fall inside its own country's bounds. Sabotaged by swapping one site's
  latitude and longitude: it failed, then passed on restore.

## To do

1. **Fetch and read Epoch's files** before writing any code against them.
   Web search (not the files themselves) says the AI Data Centers hub
   (`https://epoch.ai/data/ai-data-centers`, CC BY 4.0) covers 86 sites and
   about 44% of global AI compute, with Address, Latitude, Longitude, Owner,
   Users, IT power, H100 equivalents, chips, capital cost and buildout status
   over time, plus separate cooling files (chillers, cooling towers). A CSV was
   indexed at `https://epoch.ai/data/generated/data_centers/data_centers.csv`
   under the hub's old name. Documentation:
   `https://epoch.ai/data/data-centers-documentation`. Check the real headers,
   the licence text and the coverage figure; none of the above is verified.
2. **Register the source** in `data/sources.json` (suggested id
   `epoch-ai-data-centers`) with its verified URL, cadence and caveats. The
   map caveat prints the caveats verbatim.
3. **ETL**: add `build_datacentres()` to `etl/fetch_epoch.py` (it becomes six
   datasets; update CLAUDE.md). Write `ai-datacentres` through
   `write_dataset()`, one record per site, `source_id` on each, dashes
   normalised with `_text()`. Map Epoch's buildout stage onto `stage`, the
   cooling files onto `cooling` and `water` (cooling towers evaporate; dry
   coolers and air-cooled chillers are closed loop), and leave `use` and
   `power_source` null wherever Epoch does not record them; the page reports
   the count of nulls. Fail loudly on missing columns, like `build_models()`.
   `category` is this site's own grouping of the owner (for example
   hyperscale cloud, AI developer, GPU cloud, colocation), labelled as ours on
   the page; unmapped owners should fail the build, as unmapped benchmarks do.
   Add a `--self-check` and wire it into `.github/workflows/refresh-data.yml`.
4. **Shares of all datacentres** (`datacentre-shares`): hand-coded figures in
   `etl/build_environment_index.py` under the Environmental Disclosure Index,
   with their own review date so the index's `REVIEWED` is not bumped. One
   record per measure (count, electricity, water), each with the publisher's
   total, the AI portion and its definition only where the publisher states
   them, and a URL that resolves. Candidates to read, none yet verified: IEA,
   Energy and AI (2025), and LBNL's 2024 United States Data Center Energy
   Usage Report. Where no publisher splits AI from the total, the record says
   so and the table prints a dash. Nothing unverified is published.
5. **The page against real data**: adjust `SiteRecord`, the card rows and the
   list columns to what exists, keeping "not recorded" distinct from zero.
   Check the copy against the register rules in CLAUDE.md.
6. **Homepage**: a numbered panel for Datacentres after 02 Capability, and
   renumber the rest.
7. **CLAUDE.md**: the page table, `ZoomMap` in the component list,
   `fetch_epoch` dataset count, source counts, and the new join if the page
   makes one.
8. **Verify** with `npm run check:lib`, `npm run build`, `npm run check:built`,
   every Python self-check and `python etl/check_contrast.py`, then read the
   built page at 1440px and 390px, run the horizontal-overflow probe from
   CLAUDE.md, and drive the map: zoom, pan, hover, tap, filters.
