"""Eurostat: AI adoption by enterprises, the industry side of the adoption story.

Two Eurostat tables carry it. isoc_eb_ai breaks adoption down by country and by
enterprise size; isoc_eb_ain2 breaks it down by economic activity. Both are the
2025 survey wave, both cover enterprises with ten or more people employed unless
the size dimension says otherwise, and both are free to reuse under the
Commission's reuse policy with attribution.

Why enterprises and not individuals: Microsoft's diffusion data already covers
individuals, and setting the two side by side is the most interesting thing on
the adoption page. In several countries the population is using AI at three or
four times the rate their employers are.

Output is deliberately narrow. Eurostat serves 63 indicators across 50 activity
classes and 36 geographies; almost all of that is noise for a general reader, so
this pulls the four slices the page actually shows and leaves the rest where it
is, one link away.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import fetch, write_dataset

SOURCE = "eurostat-ai-enterprises"

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"

# "Using at least one of the AI technologies", as a percentage of enterprises.
# The denominator matters: PC_ENT is all enterprises, not only those online.
ANY_AI = "E_AI_TANY"
PC_ENT = "PC_ENT"
TEN_PLUS = "GE10"
EU27 = "EU27_2020"

# Aggregates, not countries. They belong in the EU-wide slices and would double
# count if they were left in a list of countries.
AGGREGATES = {"EU27_2020", "EA19", "EA20", "EA21", "EU28", "EU27_2007", "EA"}


def assert_countries(records: list[dict]) -> None:
    """Second, independent guard on the same failure as `is_aggregate`.

    Every country label Eurostat publishes is short. Its grouping labels list
    their own composition and run past a hundred characters, so if a new grouping
    code ever evades the prefix rule this catches it on the name instead. A
    grouping ranked among the countries is not a visible error: it looks exactly
    like a country with that number.
    """
    for record in records:
        if len(record["name"]) > 40:
            raise ValueError(
                f"{record['code']} has a {len(record['name'])}-character label "
                f"({record['name'][:50]}...), which is a grouping and not a country"
            )


def is_aggregate(geo: str) -> bool:
    """True for a Eurostat grouping rather than a country.

    The named set is not enough on its own. Eurostat publishes the euro area
    under the rolling code "EA" as well as the vintaged ones, and that bare code
    slipped through and was ranked twenty-first among the countries, on a chart
    whose own caveat said the euro area was excluded.

    So the rule is a prefix rule as well: no ISO 3166-1 alpha-2 country code
    begins "EU" or "EA". EE, EG, EH, ER, ES and ET all begin with E and none of
    them collides, which is what makes the prefix safe to use.
    """
    return geo in AGGREGATES or geo.startswith(("EU", "EA"))

# The seven technologies the survey asks about individually, in the order the
# questionnaire uses. E_AI_TANY and the "at least two" and "none" variants are
# summaries of these and are excluded so the list does not double count.
TECHNOLOGIES = [
    "E_AI_TTM",
    "E_AI_TSR",
    "E_AI_TNLG",
    "E_AI_TIR",
    "E_AI_TML",
    "E_AI_TPA",
    "E_AI_TAR",
]

# Eurostat's own labels for these run to 120 characters and repeat "Enterprises
# using AI technologies" seven times. Shortened for display, with the full label
# kept on the record so nothing is lost.
TECH_SHORT = {
    "E_AI_TTM": "Text mining",
    "E_AI_TSR": "Speech recognition",
    "E_AI_TNLG": "Text or speech generation",
    "E_AI_TIR": "Image recognition",
    "E_AI_TML": "Machine learning for data analysis",
    "E_AI_TPA": "Workflow automation or decision support",
    "E_AI_TAR": "Autonomous robots and vehicles",
}

# Size classes in order, skipping the overlapping roll-ups (0-9, 10-249) that
# would plot a bar containing the bars either side of it.
SIZE_ORDER = ["10-49", "50-249", "GE250"]
SIZE_SHORT = {
    "10-49": "10 to 49 staff",
    "50-249": "50 to 249 staff",
    "GE250": "250 or more staff",
}


def _url(dataset: str, **filters: str) -> str:
    query = "&".join(f"{k}={v}" for k, v in filters.items())
    return f"{BASE}{dataset}?format=JSON&lang=en&{query}"


def _load(dataset: str, filename: str, offline: bool, **filters: str) -> dict[str, Any]:
    path, retrieved = fetch(
        SOURCE, url=_url(dataset, **filters), filename=filename, offline=offline
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not payload.get("value"):
        raise ValueError(f"{dataset}: Eurostat returned no values for {filters!r}")
    return {"payload": payload, "retrieved": retrieved}


def observations(payload: dict[str, Any]) -> Iterator[tuple[dict[str, str], float]]:
    """Walk a JSON-stat 2.0 response as (coordinates, value) pairs.

    Values arrive as a sparse map from a single flat integer to a number, and the
    integer is a mixed-radix encoding of the dimension coordinates with the LAST
    dimension varying fastest. Decoding it wrongly does not error, it silently
    attributes every number to the wrong country, so this is the one function in
    the file with a self-check of its own.
    """
    dims = payload["id"]
    sizes = payload["size"]

    # Position -> code, per dimension. Eurostat gives code -> position.
    codes: list[list[str]] = []
    for dim in dims:
        index = payload["dimension"][dim]["category"]["index"]
        ordered = [""] * len(index)
        for code, position in index.items():
            ordered[position] = code
        codes.append(ordered)

    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    for flat, value in payload["value"].items():
        if value is None:
            continue
        remainder = int(flat)
        coords: dict[str, str] = {}
        for i, dim in enumerate(dims):
            coords[dim] = codes[i][remainder // strides[i]]
            remainder %= strides[i]
        yield coords, float(value)


def _labels(payload: dict[str, Any], dim: str) -> dict[str, str]:
    return payload["dimension"][dim]["category"]["label"]


def build_by_country(offline: bool) -> None:
    loaded = _load(
        "isoc_eb_ai",
        "eurostat-ai-country.json",
        offline,
        unit=PC_ENT,
        indic_is=ANY_AI,
        size_emp=TEN_PLUS,
        sinceTimePeriod="2025",
    )
    payload, retrieved = loaded["payload"], loaded["retrieved"]
    geo_labels = _labels(payload, "geo")

    records = [
        {
            "code": coords["geo"],
            "name": geo_labels.get(coords["geo"], coords["geo"]),
            "share": round(value, 1),
            "year": coords["time"],
            "source_id": SOURCE,
        }
        for coords, value in observations(payload)
        if not is_aggregate(coords["geo"])
    ]
    records.sort(key=lambda r: r["share"], reverse=True)
    assert_countries(records)

    eu = [
        round(v, 1) for c, v in observations(payload) if c["geo"] == EU27
    ]

    write_dataset(
        "enterprise-ai-country",
        records,
        source_ids=[SOURCE],
        unit="percent of enterprises",
        notes=(
            "Share of enterprises with ten or more people employed using at least one of "
            "seven AI technologies, 2025 survey wave. Covers all activities except "
            "agriculture, forestry, fishing, mining and finance. The EU27 figure is "
            f"{eu[0] if eu else 'not reported'} percent. Self-reported by the enterprise, "
            "so it measures what firms say they use and what they recognise as AI."
        ),
        retrieved=retrieved,
    )


def build_by_size(offline: bool) -> None:
    loaded = _load(
        "isoc_eb_ai",
        "eurostat-ai-size.json",
        offline,
        unit=PC_ENT,
        indic_is=ANY_AI,
        geo=EU27,
        sinceTimePeriod="2025",
    )
    payload, retrieved = loaded["payload"], loaded["retrieved"]
    by_size = {c["size_emp"]: v for c, v in observations(payload)}

    records = [
        {
            "size": code,
            "label": SIZE_SHORT[code],
            "share": round(by_size[code], 1),
            "source_id": SOURCE,
        }
        for code in SIZE_ORDER
        if code in by_size
    ]
    if len(records) < len(SIZE_ORDER):
        missing = set(SIZE_ORDER) - set(by_size)
        print(f"  note: size classes absent from this wave: {sorted(missing)}")

    write_dataset(
        "enterprise-ai-size",
        records,
        source_ids=[SOURCE],
        unit="percent of enterprises",
        notes=(
            "EU27 enterprises using at least one AI technology, by number of people "
            "employed, 2025. The overlapping roll-up classes Eurostat also publishes "
            "(0 to 9, 10 to 249) are excluded, because plotting them next to their own "
            "components counts the same firms twice."
        ),
        retrieved=retrieved,
    )


def build_by_technology(offline: bool) -> None:
    loaded = _load(
        "isoc_eb_ai",
        "eurostat-ai-tech.json",
        offline,
        unit=PC_ENT,
        geo=EU27,
        size_emp=TEN_PLUS,
        sinceTimePeriod="2025",
    )
    payload, retrieved = loaded["payload"], loaded["retrieved"]
    labels = _labels(payload, "indic_is")
    by_tech = {c["indic_is"]: v for c, v in observations(payload)}

    records = [
        {
            "code": code,
            "label": TECH_SHORT[code],
            "full_label": labels.get(code, code),
            "share": round(by_tech[code], 1),
            "source_id": SOURCE,
        }
        for code in TECHNOLOGIES
        if code in by_tech
    ]
    records.sort(key=lambda r: r["share"], reverse=True)

    write_dataset(
        "enterprise-ai-technology",
        records,
        source_ids=[SOURCE],
        unit="percent of enterprises",
        notes=(
            "EU27 enterprises with ten or more people employed, by which AI technology "
            "they use, 2025. Shares overlap: a firm using three of them is counted in all "
            "three, so these do not sum to the headline adoption rate. Only the seven "
            "technologies the questionnaire asks about individually are listed; Eurostat's "
            "'at least one', 'at least two' and 'none' totals are summaries of these and "
            "would double count."
        ),
        retrieved=retrieved,
    )


def build_by_industry(offline: bool) -> None:
    loaded = _load(
        "isoc_eb_ain2",
        "eurostat-ai-industry.json",
        offline,
        unit=PC_ENT,
        indic_is=ANY_AI,
        geo=EU27,
        size_emp=TEN_PLUS,
        sinceTimePeriod="2025",
    )
    payload, retrieved = loaded["payload"], loaded["retrieved"]
    labels = _labels(payload, "nace_r2")

    records = [
        {
            "code": coords["nace_r2"],
            "label": labels.get(coords["nace_r2"], coords["nace_r2"]),
            "share": round(value, 1),
            "source_id": SOURCE,
        }
        for coords, value in observations(payload)
    ]
    records.sort(key=lambda r: r["share"], reverse=True)

    write_dataset(
        "enterprise-ai-industry",
        records,
        source_ids=[SOURCE],
        unit="percent of enterprises",
        notes=(
            "EU27 enterprises with ten or more people employed using at least one AI "
            "technology, by economic activity, 2025. NACE classes nest: broad groupings "
            "and their own components both appear, so this is a lookup rather than a "
            "partition and the shares do not sum to anything meaningful."
        ),
        retrieved=retrieved,
    )


def run(offline: bool = False) -> None:
    build_by_country(offline)
    build_by_size(offline)
    build_by_technology(offline)
    build_by_industry(offline)


def _self_check() -> None:
    """Check the JSON-stat decoder, which fails silently when it fails.

    A wrong stride does not raise. It attributes every value to the wrong country
    and produces a chart that looks entirely reasonable, which is the worst kind
    of bug for a site like this one.
    """
    # Two dimensions, 2 x 3, so the expected mapping can be written out by hand.
    payload = {
        "id": ["geo", "time"],
        "size": [2, 3],
        "dimension": {
            "geo": {"category": {"index": {"AA": 0, "BB": 1}, "label": {"AA": "A", "BB": "B"}}},
            "time": {
                "category": {
                    "index": {"2023": 0, "2024": 1, "2025": 2},
                    "label": {"2023": "2023", "2024": "2024", "2025": "2025"},
                }
            },
        },
        # Flat index = geo_position * 3 + time_position, last dimension fastest.
        "value": {"0": 10.0, "2": 12.0, "3": 20.0, "5": 22.0},
    }
    got = {(c["geo"], c["time"]): v for c, v in observations(payload)}
    assert got == {
        ("AA", "2023"): 10.0,
        ("AA", "2025"): 12.0,
        ("BB", "2023"): 20.0,
        ("BB", "2025"): 22.0,
    }, got

    # Reversing the stride order is the mistake that would be made, and it must
    # not produce the same answer, or this check proves nothing.
    swapped = dict(payload, id=["time", "geo"], size=[3, 2])
    other = {(c["geo"], c["time"]): v for c, v in observations(swapped)}
    assert other != got, "decoder gives the same answer whichever way round the dimensions are"

    # Nulls are suppressed observations, not zeroes. Treating one as zero would
    # draw a country at zero percent adoption that simply did not report.
    with_null = dict(payload, value={"0": 10.0, "1": None})
    assert len(list(observations(with_null))) == 1, "a suppressed value became a data point"

    assert set(TECH_SHORT) == set(TECHNOLOGIES), "technology labels and codes have drifted"
    assert set(SIZE_SHORT) == set(SIZE_ORDER), "size labels and codes have drifted"
    assert EU27 in AGGREGATES, "EU27 must be excluded from the country list"

    # The aggregate filter, against the codes Eurostat actually publishes and
    # against the one that got through. A grouping ranked among the countries is
    # not a visible error: it looks exactly like a country with that number.
    for geo in ("EU27_2020", "EA", "EA19", "EA20", "EU28"):
        assert is_aggregate(geo), f"{geo} would be ranked as a country"
    for geo in ("EE", "ES", "EL", "DK", "NO", "TR", "UK"):
        assert not is_aggregate(geo), f"{geo} would be dropped as an aggregate"

    # The label guard runs inside run(), on the records about to be written,
    # rather than here. A check that reads the previous run's output refuses to
    # let the current run fix the thing it is complaining about.
    assert_countries([{"code": "DK", "name": "Denmark"}])
    try:
        assert_countries([{"code": "EA", "name": "Euro area (EA11-1999, " + "x" * 100 + ")"}])
    except ValueError:
        pass
    else:
        raise AssertionError("assert_countries accepted a grouping label")

    print("fetch_eurostat self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        _self_check()
        run(offline="--offline" in sys.argv)
