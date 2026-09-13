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

console.log("check-lib.mjs passed");
