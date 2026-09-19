/**
 * Runnable checks for the render-side logic that can be silently wrong.
 *
 * The Python side has its own self-checks; this is the TypeScript equivalent,
 * covering the three things here that fail without looking like they failed:
 * path rounding (produces a valid-but-wrong outline), percentile ranks (produce
 * a plausible-but-wrong map), and the country join (paints the wrong country).
 *
 *     node scripts/check-lib.mjs
 *
 * No test framework on purpose. Three asserts do not need one.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

// Imported from source rather than reimplemented here. A copy of the logic in
// the test would drift from the real thing and keep passing while the site broke.
// Needs node --experimental-strip-types; see the npm script.
const geo = await import("../src/lib/geo.ts");

/* roundPath. The trailing-zero strip is the part that can corrupt an outline:
   it must never eat a zero that belongs to the integer part. */
assert.equal(geo.roundPath("M100.04 200.00L1.25 0.04", 1), "M100 200L1.3 0");
assert.equal(geo.roundPath("M10.0 120.04", 1), "M10 120");
assert.equal(geo.roundPath("M-0.04 5.55", 1), "M-0 5.5");
assert.equal(geo.roundPath("M100.44 200.55", 0), "M100 201");
// Integers carry no decimal point and must pass through untouched.
assert.equal(geo.roundPath("M100 200Z", 1), "M100 200Z");
// The digits that matter must survive: 123.456 is not 12.
assert.ok(geo.roundPath("M123.456 0.001", 1).startsWith("M123.5"));

/* percentileRanks. Ties must share a rank, the order must be preserved, and the
   result must be bounded, or the gap map colours countries by file order. */
{
  const ranks = geo.percentileRanks([10, 20, 20, 30]);
  assert.equal(ranks.length, 4);
  assert.equal(ranks[1], ranks[2], "tied values must share a percentile");
  assert.ok(ranks[0] < ranks[1] && ranks[1] < ranks[3], "order must be preserved");
  assert.ok(Math.min(...ranks) > 0 && Math.max(...ranks) <= 100, "must stay in 0..100");

  // Input order must not change the answer for a given value.
  const shuffled = geo.percentileRanks([30, 20, 10, 20]);
  assert.equal(shuffled[2], ranks[0], "rank of 10 must not depend on its position");
  assert.equal(shuffled[0], ranks[3], "rank of 30 must not depend on its position");

  // Every value identical: no spread, and nothing should blow up.
  const flat = geo.percentileRanks([5, 5, 5]);
  assert.ok(flat.every((r) => r === flat[0]), "identical values must rank identically");
}

/* The country join. A wrong answer here paints the wrong country, which is the
   one failure mode nobody spots by looking. */
assert.equal(geo.alpha3("Australia"), "AUS");
assert.equal(geo.alpha3("United States of America"), "USA");
assert.equal(geo.alpha3("Congo (DRC)"), "COD", "alias table must win over the library");
assert.equal(geo.alpha3("Laos"), "LAO");
assert.equal(geo.alpha3("Not A Country At All"), null, "unknown names must not guess");

/* Every economy in the exposure data must either resolve or be a known
   non-country aggregate. A new unresolved name means a country silently
   vanished from the map, so it fails here rather than going unnoticed. */
{
  const exposure = JSON.parse(readFileSync("data/processed/ai-exposure.json", "utf8"));
  const unresolved = exposure.records
    .map((r) => r.entity)
    .filter((name) => !geo.alpha3(name));
  assert.deepEqual(
    unresolved,
    [],
    `economies that no longer resolve to an ISO code: ${unresolved.join(", ")}`,
  );
}

/* Every jurisdiction we code must land on a shape the map can actually paint,
   or its score is computed and then thrown away silently. */
{
  const governance = JSON.parse(readFileSync("data/processed/governance-readiness.json", "utf8"));
  const shapes = new Set(geo.projectWorld(400, 0).shapes.map((s) => s.code));
  const missing = governance.records.map((r) => r.code).filter((c) => !shapes.has(c));
  assert.deepEqual(
    missing,
    ["MLT", "SGP"],
    `coded jurisdictions with no shape on the 110m map: ${missing.join(", ")}. ` +
      `Malta and Singapore are expected: both are too small to appear at 1:110m. ` +
      `Anything else means a join broke.`,
  );
}

/* News categories are defined twice, once in Python and once in TypeScript.
   Two copies drift. This is the thing that notices. */
{
  const news = await import("../src/lib/news.ts");
  const feed = JSON.parse(readFileSync("data/processed/news-feed.json", "utf8"));
  const inData = new Set(feed.records.flatMap((r) => r.categories));
  const known = new Set(news.CATEGORIES.map((c) => c.slug));
  const unlabelled = [...inData].filter((slug) => !known.has(slug));
  assert.deepEqual(
    unlabelled,
    [],
    `categories in the data with no label in src/lib/news.ts: ${unlabelled.join(", ")}. ` +
      `Add them there, or the chips render blank and the routes 404.`,
  );

  // Every item must carry at least one category and the terms behind it, or the
  // "why is this here" line under each row silently shows nothing.
  for (const record of feed.records) {
    assert.ok(record.categories?.length > 0, `${record.title}: no categories`);
    for (const slug of record.categories) {
      if (slug === "general") continue;
      assert.ok(
        record.matched_terms?.[slug]?.length > 0,
        `${record.title}: filed under ${slug} with no matched terms`,
      );
    }
  }
}

/* The render-side licence guard. etl/common.py sabotage-tests the write-side
   guard; this is the half that had no test, which meant the control the site
   relies on to never publish data it has no right to could have been weakened
   without anything noticing. */
{
  const { assertRenderable, getSource, sources } = await import("../src/lib/sources.ts");
  const ids = Object.keys(sources);

  // 1. A permitted source renders. If this fails the guard has become a wall.
  for (const allowed of ["epoch-notable-models", "microsoft-ai-diffusion", "openalex"]) {
    assert.doesNotThrow(
      () => assertRenderable(allowed),
      `assertRenderable blocked ${allowed}, which is permitted. Charts will vanish.`,
    );
  }

  // 2. A blocked source must throw. These three are registered PRECISELY so that
  //    wiring them in fails the build; if this passes silently, the site can
  //    publish data it has no licence to publish.
  const mustBlock = ["artificial-analysis", "stanford-ai-index", "metr-time-horizons"];
  for (const blocked of mustBlock) {
    assert.throws(
      () => assertRenderable(blocked),
      `assertRenderable let ${blocked} (redistribution=${getSource(blocked).redistribution}) ` +
        `through. That is a licence breach waiting to be rendered.`,
    );
  }

  // 3. An unregistered id must throw rather than rendering an unattributed figure.
  assert.throws(
    () => assertRenderable("no-such-source"),
    "assertRenderable accepted an unregistered source_id",
  );

  // 4. The guard must actually be reading the registry, not a hardcoded list of
  //    three names. Every source whose declared state is blocking must throw,
  //    and every other source must not.
  const BLOCKING = new Set(["prohibited", "no-derivatives"]);
  for (const id of ids) {
    const state = getSource(id).redistribution;
    if (BLOCKING.has(state)) {
      assert.throws(() => assertRenderable(id), `${id} is ${state} but renders`);
    } else {
      assert.doesNotThrow(() => assertRenderable(id), `${id} is ${state} but is blocked`);
    }
  }

  // 5. Drift. The blocked set is declared twice, once in Python and once in
  //    TypeScript, because one guards the write and the other guards the render.
  //    Two copies drift; this is the thing that notices. Read the Python source
  //    rather than importing it, since this is a Node process.
  const python = readFileSync("etl/common.py", "utf8");
  const declared = python.match(/BLOCKED_REDISTRIBUTION\s*=\s*\{([^}]*)\}/);
  assert.ok(declared, "could not find BLOCKED_REDISTRIBUTION in etl/common.py");
  const pythonStates = [...declared[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]).sort();
  assert.deepEqual(
    pythonStates,
    [...BLOCKING].sort(),
    `etl/common.py blocks [${pythonStates}] but src/lib/sources.ts blocks [${[...BLOCKING]}]. ` +
      `One end would write data the other end refuses to render, or worse, the reverse.`,
  );

  // 6. And the set this test asserts against must match the one the module
  //    actually uses, or points 4 and 5 are checking a copy of a copy.
  const tsSource = readFileSync("src/lib/sources.ts", "utf8");
  const tsDeclared = tsSource.match(/const BLOCKED[^=]*=\s*new Set\(\[([^\]]*)\]\)/);
  assert.ok(tsDeclared, "could not find the BLOCKED set in src/lib/sources.ts");
  const tsStates = [...tsDeclared[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]).sort();
  assert.deepEqual(
    tsStates,
    [...BLOCKING].sort(),
    `src/lib/sources.ts blocks [${tsStates}] but this test asserts [${[...BLOCKING]}]`,
  );

  const blockedCount = ids.filter((id) => BLOCKING.has(getSource(id).redistribution)).length;
  assert.equal(
    blockedCount,
    mustBlock.length,
    `${blockedCount} sources are marked unrenderable but this test names ${mustBlock.length}. ` +
      `A new blocked source should be added to the list above so it is checked by name.`,
  );
}

/* The feed URLs the renderer will put in an href. etl/fetch_news.py checks the
   scheme on the way in and NewsList.astro checks it again on the way out; this
   checks the render-side half does what it claims, and that the committed data
   currently passes it. */
{
  const { isSafeUrl } = await import("../src/lib/news.ts");

  for (const good of [
    "https://example.com/a",
    "http://example.com/a", // plain http allowed on purpose: many primary sources use it
    "https://www.gov.uk/x?y=1#z",
    "  https://example.com/padded  ",
  ]) {
    assert.ok(isSafeUrl(good), `isSafeUrl rejected ${good}`);
  }

  for (const bad of [
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "file:///etc/passwd",
    "ftp://example.com/x",
    "//example.com/a", // protocol-relative: the browser would supply ours
    "https://",
    "not a url",
    "",
    null,
    undefined,
  ]) {
    assert.ok(!isSafeUrl(bad), `isSafeUrl accepted ${JSON.stringify(bad)}`);
  }

  // The committed feed must pass its own check, or rows silently lose their links.
  const feed = JSON.parse(readFileSync("data/processed/news-feed.json", "utf8"));
  const unsafe = feed.records.filter((r) => !isSafeUrl(r.url));
  assert.deepEqual(
    unsafe.map((r) => r.url),
    [],
    `news-feed.json contains URLs the renderer will refuse to link`,
  );
}

/* TimeMap interpolates period labels into a raw <style> block via set:html, so a
   label containing "</style>" would close the element and everything after it
   would be parsed as markup. The component validates and fails the build rather
   than sanitising. The pattern is read out of the component source rather than
   reimplemented here, so weakening it there fails here. */
{
  const component = readFileSync("src/components/TimeMap.astro", "utf8");
  const found = component.match(/const PERIOD_LABEL = (\/.+\/);/);
  assert.ok(
    found,
    "could not find PERIOD_LABEL in src/components/TimeMap.astro. If it was renamed, " +
      "update this check; if it was removed, the raw <style> sink is unguarded again.",
  );
  const [, body, flags] = found[1].match(/^\/(.*)\/([a-z]*)$/);
  const pattern = new RegExp(body, flags);

  // The labels the site actually renders must still pass.
  for (const real of ["2025-H1", "2025-H2", "2026-Q1", "2026 Q1", "H1_2025"]) {
    assert.ok(pattern.test(real), `PERIOD_LABEL rejects the real label ${real}`);
  }

  // The thing the guard exists for.
  for (const hostile of [
    "</style><script>alert(1)</script>",
    "2026-Q1</style><script>alert(1)</script>",
    '2026-Q1"; } body { display: none } .x { content: "',
    "<img src=x onerror=alert(1)>",
    "2026-Q1\\",
    "a".repeat(64),
    "",
    " leading space",
  ]) {
    assert.ok(
      !pattern.test(hostile),
      `PERIOD_LABEL accepts ${JSON.stringify(hostile)}, which reaches a raw <style> block`,
    );
  }

  // The pattern must be anchored at both ends, or it matches a safe substring of
  // a hostile label and waves the whole thing through.
  assert.ok(body.startsWith("^") && body.endsWith("$"), "PERIOD_LABEL is not fully anchored");
}

/* src/styles/fonts.css is the two Fontsource packages' own @font-face rules with
   font-display changed from swap to optional, because a descriptor cannot be
   overridden from outside its rule and swap was costing five routes their CLS
   budget. Copying the rules buys that control and takes on one risk: an upgrade
   that adds, drops or repoints a subset would leave our copy quietly stale, and
   the failure is a script rendering in the system font with nothing to catch it.

   So this compares the two by the only thing that matters for coverage: the set
   of (family, unicode-range, file) triples. Formatting, ordering and whitespace
   are ignored; a genuine change to what the packages ship is not. */
{
  const faces = (css) =>
    new Set(
      [...css.matchAll(/@font-face\s*\{([^}]*)\}/g)].map((m) => {
        const family = /font-family:\s*['"]?([^'";]+)/.exec(m[1])[1].trim();
        const range = /unicode-range:\s*([^;]+)/.exec(m[1])[1].replace(/\s+/g, "");
        const file = /([\w-]+\.woff2)/.exec(m[1])[1];
        return `${family} | ${range} | ${file}`;
      }),
    );

  const ours = faces(readFileSync("src/styles/fonts.css", "utf8"));
  const theirs = new Set();
  for (const pkg of ["@fontsource-variable/geist", "@fontsource-variable/geist-mono"])
    for (const face of faces(readFileSync(`node_modules/${pkg}/index.css`, "utf8"))) theirs.add(face);

  // A destructuring regex that never matches throws above; an empty set here
  // would instead make both comparisons pass while reading nothing at all.
  assert.ok(ours.size === 11 && theirs.size === 11, `parsed ${ours.size} and ${theirs.size} faces, expected 11 each`);

  assert.deepEqual(
    [...theirs].filter((f) => !ours.has(f)).sort(),
    [],
    "the Fontsource packages ship a face that src/styles/fonts.css does not declare, so that " +
      "script now renders in the system font. Recopy both index.css files and change " +
      "font-display: swap to optional.",
  );
  assert.deepEqual(
    [...ours].filter((f) => !theirs.has(f)).sort(),
    [],
    "src/styles/fonts.css declares a face the packages no longer ship, so its url() is dead. " +
      "Recopy both index.css files and change font-display: swap to optional.",
  );
  const displays = new Set(
    [...readFileSync("src/styles/fonts.css", "utf8").matchAll(/font-display:\s*([a-z]+)/g)].map(
      (m) => m[1],
    ),
  );
  assert.deepEqual(
    [...displays],
    ["optional"],
    `src/styles/fonts.css declares font-display ${[...displays].join(", ")}; the whole reason ` +
      `the file exists is that every face is optional.`,
  );
}

console.log("check-lib.mjs passed");
