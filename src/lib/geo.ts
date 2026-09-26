/**
 * Build-time map geometry and the country joins that go with it.
 *
 * Geometry is Natural Earth via the world-atlas package, public domain, and it
 * is projected to SVG paths during the build. Nothing here reaches the browser:
 * the page ships flat <path d="..."> markup and no client JavaScript.
 *
 * Projection is Natural Earth rather than Mercator. Mercator inflates high
 * latitudes by an enormous factor, which on a choropleth reads as "this
 * phenomenon is mostly a northern one" regardless of the data. On a site about
 * honest numbers, that is not a defensible default.
 */
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature, mesh } from "topojson-client";
import countries from "i18n-iso-countries";
import en from "i18n-iso-countries/langs/en.json" with { type: "json" };
import world from "world-atlas/countries-110m.json" with { type: "json" };
import landAtlas from "world-atlas/land-110m.json" with { type: "json" };
import type { Topology, GeometryCollection } from "topojson-specification";
import type { Feature, FeatureCollection, Geometry, MultiPolygon, Polygon } from "geojson";

countries.registerLocale(en as Parameters<typeof countries.registerLocale>[0]);

/**
 * Names our sources use that are not the ISO English short name.
 *
 * Kept deliberately small and explicit. The alternative, fuzzy matching, fails
 * silently and in the worst possible way: it paints the wrong country rather
 * than leaving it blank, and nothing in the output looks wrong.
 */
const NAME_ALIASES: Record<string, string> = {
  Moldova: "MDA",
  "Congo (DRC)": "COD",
  "Congo (Republic)": "COG",
  Laos: "LAO",
  Syria: "SYR",
  "Hong Kong SAR": "HKG",
  "Macao SAR": "MAC",
  Vietnam: "VNM",
  "South Korea": "KOR",
  "North Korea": "PRK",
  Russia: "RUS",
  Iran: "IRN",
  Tanzania: "TZA",
  Bolivia: "BOL",
  Venezuela: "VEN",
  Brunei: "BRN",
  "Cape Verde": "CPV",
  "Ivory Coast": "CIV",
  Czechia: "CZE",
  "Turkiye": "TUR",
};

/**
 * Eurostat geo codes that are not ISO 3166-1 alpha-2.
 *
 * Eurostat uses EL for Greece and UK for the United Kingdom, both of which are
 * its own convention rather than the ISO code. Passing either to a library that
 * expects ISO returns nothing, which drops the country from the join in silence.
 */
const EUROSTAT_CODES: Record<string, string> = {
  EL: "GRC",
  UK: "GBR",
};

/** ISO alpha-3 from an alpha-2 code, tolerating Eurostat's two exceptions. */
export function alpha3FromAlpha2(code: string): string | null {
  const upper = code.toUpperCase();
  return EUROSTAT_CODES[upper] ?? countries.alpha2ToAlpha3(upper) ?? null;
}

/** ISO alpha-3 for a country name, or null when we genuinely cannot tell. */
export function alpha3(name: string): string | null {
  const alias = NAME_ALIASES[name];
  if (alias) return alias;
  return countries.getAlpha3Code(name, "en") ?? null;
}

export interface CountryShape {
  /** ISO alpha-3, or null for territories with no ISO numeric code. */
  code: string | null;
  name: string;
  /** SVG path data, already projected. */
  d: string;
  /** Detail geometry avoids framing a mainland as a speck beside a remote territory. */
  detailD: string;
  detailBounds: [[number, number], [number, number]];
  /** Bounds of the whole country, remote territories included. */
  bounds: [[number, number], [number, number]];
}

export interface ProjectedWorld {
  width: number;
  height: number;
  shapes: CountryShape[];
  /** Outline of the sphere, for the map's own frame. */
  sphere: string;
  /** Graticule-free: one fewer thing on the page that carries no information. */
}

// Antarctica is dropped. It has no population, no jurisdiction that appears in
// any dataset here, and occupies about a fifth of the frame. Leaving it in would
// cost a fifth of the map to render one permanently grey shape.
const DROPPED = new Set(["Antarctica"]);

/**
 * Drop the coordinate precision nobody can see.
 *
 * d3-geo emits full float precision, which on a 177-country world map is about
 * 340KB of digits per render, most of them below a thousandth of a pixel. At one
 * decimal place the outlines are pixel-identical at any size this site renders
 * and the markup roughly halves. Operates on generated path strings only, never
 * on source.
 */
export function roundPath(d: string, places: number): string {
  return d.replace(/-?\d+\.\d+/g, (n) => {
    const rounded = Number(n).toFixed(places);
    // "12.0" carries a digit that says nothing; "12" says the same thing.
    return places === 0 ? rounded : rounded.replace(/\.?0+$/, "");
  });
}

/**
 * Project the world once, at the given pixel width.
 *
 * Called at build time from a page's frontmatter. Height follows from the
 * projection's own aspect ratio rather than being chosen, so the map is never
 * stretched.
 */
export function projectWorld(width = 1000, places = 1): ProjectedWorld {
  const topology = world as unknown as Topology<{ countries: GeometryCollection }>;
  const collection = feature(
    topology,
    topology.objects.countries,
  ) as unknown as FeatureCollection<Geometry, { name: string }>;

  const kept = collection.features.filter((f) => !DROPPED.has(f.properties.name));
  const height = Math.round(width * 0.5);

  const projection = geoNaturalEarth1().fitSize(
    [width, height],
    { type: "FeatureCollection", features: kept } as FeatureCollection,
  );
  const path = geoPath(projection);

  const shapes: CountryShape[] = [];
  for (const f of kept) {
    const d = path(f);
    if (!d) continue;
    const bounds = path.bounds(f);
    let detail = f as Feature<Geometry, { name: string }>;
    if (f.geometry.type === "MultiPolygon") {
      const polygons = f.geometry.coordinates.map((coordinates) => ({
        type: "Feature" as const,
        properties: f.properties,
        geometry: { type: "Polygon" as const, coordinates },
      } satisfies Feature<Polygon, { name: string }>));
      const largest = polygons.reduce((a, b) => path.area(a) >= path.area(b) ? a : b);
      const [[x0, y0], [x1, y1]] = bounds;
      const boxArea = (x1 - x0) * (y1 - y0);
      const shapeArea = path.area(f);
      if (shapeArea > 0 && boxArea / shapeArea > 12) detail = largest;
    }
    const detailD = path(detail);
    if (!detailD) continue;
    const numeric = typeof f.id === "string" ? f.id : String(f.id ?? "");
    shapes.push({
      code: countries.numericToAlpha3(numeric) ?? null,
      name: f.properties.name,
      d: roundPath(d, places),
      detailD: roundPath(detailD, places),
      detailBounds: path.bounds(detail),
      bounds,
    });
  }

  return {
    width,
    height,
    shapes,
    sphere: roundPath(path({ type: "Sphere" }) ?? "", places),
  };
}

export interface ProjectedLand {
  width: number;
  height: number;
  /** Every coastline as one path: land is drawn once, not once per country. */
  land: string;
  /** Internal borders only, as one path. A shared border is drawn once. */
  borders: string;
  /**
   * Where a longitude and latitude fall, as percentages of the width and the
   * height. Percentages rather than pixels, because a point map that zooms
   * places its markers against a box whose pixel size changes with the zoom.
   * Null when the projection cannot place the point.
   */
  place: (lon: number, lat: number) => [number, number] | null;
}

/**
 * The world as land and borders for a point map, with the projection that
 * places points on it.
 *
 * Same projection and the same fit as projectWorld(), so a point drawn here and
 * a country drawn there land in the same place for the same width. Two meshes
 * rather than 177 country paths: a point map has nothing to say per country, and
 * drawing every shared border twice is about a fifth more markup for no pixel.
 */
export function projectLand(width = 2000, places = 1): ProjectedLand {
  const topology = world as unknown as Topology<{ countries: GeometryCollection }>;
  const collection = feature(
    topology,
    topology.objects.countries,
  ) as unknown as FeatureCollection<Geometry, { name: string }>;

  const kept = collection.features.filter((f) => !DROPPED.has(f.properties.name));
  const height = Math.round(width * 0.5);
  const projection = geoNaturalEarth1().fitSize(
    [width, height],
    { type: "FeatureCollection", features: kept } as FeatureCollection,
  );
  const path = geoPath(projection);

  /* Land is Natural Earth's own land layer, a set of polygons that can be
     filled. Neither alternative can. A coastline mesh stops wherever a border
     meets the sea, and filling an open arc closes it with a straight chord;
     topojson's merge() of the countries goes wrong at the antimeridian. Both
     drew the same wedge from the Black Sea to the Bering Strait across Russia.

     Antarctica is left out, as from projectWorld(): every polygon lying wholly
     south of 55 degrees south, which is Antarctica and its ice shelves and
     nothing else in this layer. Borders are a mesh of the arcs two countries
     share, stroked and never filled. */
  const landTopology = landAtlas as unknown as Topology<{ land: GeometryCollection }>;
  const landFeatures = feature(landTopology, landTopology.objects.land) as unknown as FeatureCollection<MultiPolygon>;
  const land: MultiPolygon = {
    type: "MultiPolygon",
    coordinates: landFeatures.features
      .flatMap((f) => f.geometry.coordinates)
      .filter((poly) => !poly[0].every(([, lat]) => lat < -55)),
  };
  const objects = topology.objects.countries;
  const antarctica = (g: { properties?: { name?: string } }) =>
    DROPPED.has(g.properties?.name ?? "");
  const shared = mesh(topology, objects, (a, b) => a !== b && !antarctica(a) && !antarctica(b));

  return {
    width,
    height,
    land: roundPath(path(land) ?? "", places),
    borders: roundPath(path(shared) ?? "", places),
    place: (lon, lat) => {
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) return null;
      if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return null;
      const xy = projection([lon, lat]);
      if (!xy) return null;
      return [(xy[0] / width) * 100, (xy[1] / height) * 100];
    },
  };
}

/**
 * Percentile rank of each value within its own series, 0 to 100.
 *
 * Exposure is a percentage of a population and readiness is a score out of a
 * scoring rubric we wrote. Subtracting one from the other directly would be
 * meaningless: a 40 percent use rate and a readiness score of 40 are not the
 * same kind of 40. Ranking each within its own distribution first makes the
 * comparison a statement about relative standing, which is all it can honestly
 * be.
 */
export function percentileRanks(values: number[]): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  return values.map((v) => {
    // Midrank, so ties share a percentile rather than being ordered arbitrarily
    // by whatever order the source file happened to list them in.
    const below = sorted.findIndex((s) => s >= v);
    const above = sorted.filter((s) => s <= v).length;
    return ((below + above) / 2 / sorted.length) * 100;
  });
}
