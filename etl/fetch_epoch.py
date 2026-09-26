"""Epoch AI: model registry, benchmark runs, compute clusters, data centres.

Produces six datasets:
  frontier-models      models with a training-compute figure, for the capability trend
  model-releases       every notable model with a date, compute figure or not
  benchmark-frontier   best-score-to-date per benchmark, for the saturation view
  compute-clusters     clusters aggregated by country, for the compute map
  compute-thresholds   which released models cross the EU AI Act systemic-risk threshold
  ai-datacentres       one record per site in the AI Data Centers hub, for /datacentres/

All six are CC BY 4.0. Read the caveats in data/sources.json before drawing
conclusions, especially on cluster counts: Chinese clusters are systematically
less well documented than US ones, so the country split measures reporting
opacity as much as it measures capacity.

    python etl/fetch_epoch.py                # fetch and write
    python etl/fetch_epoch.py --offline      # rebuild from the cached files
    python etl/fetch_epoch.py --self-check   # data-centre derivation, no network
    python etl/fetch_epoch.py --check-links  # probe every data-centre site page
"""

from __future__ import annotations

import html
import json
import re
import sys
from collections import defaultdict
from datetime import date

from common import PROCESSED, check_links, fetch, normalise_dashes, read_csv, write_dataset

MODELS = "epoch-notable-models"
BENCHMARKS = "epoch-benchmarks"
CLUSTERS = "epoch-gpu-clusters"
HARDWARE = "epoch-ml-hardware"
DATACENTRES = "epoch-ai-data-centers"

# The hub publishes three things this page needs from two places. The sites and
# their dated timelines are CSV downloads, documented field by field at
# https://epoch.ai/data/data-centers-documentation/records. Coordinates are in
# neither: the only place Epoch publishes them is the props of the map on its
# hub's map page, one fetch for every site. The chillers and cooling-tower files
# in the same download are catalogues of equipment models, not records of which
# site uses what, so no cooling type is taken from them.
DC_TIMELINES = "https://epoch.ai/data/data_centers/data_center_timelines.csv"
DC_MAP = "https://epoch.ai/data/ai-data-centers/map"
# Each site's page on the hub, where a reader lands from the site's name. The
# path is the name lowercased with every run of other characters as one hyphen,
# which is _slug(); every one of the 93 sites resolved to a page carrying its
# name on 26 September 2026, and --check-links probes them all again. The
# download's "Calculations sheet" column is a Google Sheets document per site.
# It is not linked: a link leaves for the publisher's own page, never a
# spreadsheet.
DC_SITE_PAGE = "https://epoch.ai/data/ai-data-centers/directory/{}"

# EU AI Act Art. 51(2): a GPAI model is presumed to carry systemic risk when the
# cumulative training compute exceeds 10^25 FLOP. It is the lower of the two
# thresholds now in force and the only one that applies market-wide rather than
# to a single US state, which is why this by-year count uses it. The full list,
# including the revoked and vetoed ones, is build_frontier_index.THRESHOLDS.
EU_SYSTEMIC_RISK_FLOP = 1e25


def _text(value: str | None) -> str:
    """Trim, and apply the house dash rule.

    Epoch's organisation names carry en dashes, one of which reached a chart
    tooltip on the capability page. Every free-text field that gets rendered
    goes through here.
    """
    return normalise_dashes((value or "").strip())


def _float(value: str | None) -> float | None:
    if not value or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


# Epoch's accessibility values collapse to four states a reader can hold in
# their head. The distinction that matters for safety work is whether the weights
# are out, because that is the one release decision nobody can walk back.
ACCESS_CLASSES = {
    "Open weights (unrestricted)": "Open weights",
    "Open weights (restricted use)": "Open weights",
    "Open weights (non-commercial)": "Open weights",
    "API access": "API only",
    "Hosted access (no API)": "API only",
    "Unreleased": "Unreleased",
}


def _months_between(start: str | None, end: str | None) -> int | None:
    """Whole months between two "YYYY-MM" strings, or None if either is missing.

    None means "has not happened yet", which is a different statement from zero
    and must not collapse into it: a benchmark nobody has saturated and one
    saturated on the day it was published would otherwise print the same number.
    """
    if not start or not end:
        return None
    sy, sm = (int(part) for part in start.split("-"))
    ey, em = (int(part) for part in end.split("-"))
    return (ey - sy) * 12 + (em - sm)


def _access(value: str | None) -> str:
    """Group accessibility, keeping "not recorded" distinct from "unreleased".

    Conflating the two would turn a gap in Epoch's records into a claim that a
    model was never released, which is a different and much stronger statement.
    """
    value = (value or "").strip()
    if not value:
        return "Not recorded"
    return ACCESS_CLASSES.get(value, "Other")


def _year_month(value: str | None) -> str | None:
    """Epoch dates are ISO-ish but occasionally partial. Keep YYYY-MM only."""
    if not value or len(value) < 7:
        return None
    return value[:7]


def build_models(offline: bool) -> None:
    path, retrieved = fetch(MODELS, offline=offline)
    rows = read_csv(path)

    required = {"Model", "Organization", "Publication date", "Training compute (FLOP)"}
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"{MODELS}: expected columns missing: {sorted(missing)}")

    records = []
    for row in rows:
        compute = _float(row.get("Training compute (FLOP)"))
        published = row.get("Publication date") or ""
        if compute is None or len(published) < 7:
            continue
        records.append(
            {
                "model": _text(row["Model"]),
                "organisation": _text(row.get("Organization")),
                "country": _text(row.get("Country (of organization)")),
                "published": published[:10],
                "compute_flop": compute,
                "parameters": _float(row.get("Parameters")),
                "confidence": _text(row.get("Confidence")),
                "domain": _text(row.get("Domain")),
                # Disclosed for about a third of models. Where it is absent that
                # is a disclosure gap, not a cheap model, and the site has to say
                # so wherever the figure is plotted.
                "cost_usd": _float(row.get("Training compute cost (2023 USD)")),
                "accessibility": _access(row.get("Model accessibility")),
                "hardware": _text(row.get("Training hardware")),
                "reference": (row.get("Link") or "").strip(),
                "source_id": MODELS,
            }
        )

    records.sort(key=lambda r: r["published"])

    write_dataset(
        "frontier-models",
        records,
        source_ids=[MODELS],
        unit="FLOP",
        notes=(
            "Notable AI models with a published or estimated training-compute figure. "
            "Inclusion is editorial rather than exhaustive, and many compute values are "
            "estimates. Check the confidence field on each record before citing it."
        ),
        retrieved=retrieved,
    )

    _build_thresholds(records, retrieved)


def _build_thresholds(models: list[dict], retrieved: str) -> None:
    """Count models per year that cross the EU systemic-risk compute threshold."""
    per_year: dict[str, dict[str, int]] = defaultdict(lambda: {"above": 0, "below": 0})
    crossing = []

    for model in models:
        year = model["published"][:4]
        if model["compute_flop"] >= EU_SYSTEMIC_RISK_FLOP:
            per_year[year]["above"] += 1
            crossing.append(model)
        else:
            per_year[year]["below"] += 1

    records = [
        {
            "year": year,
            "above_threshold": counts["above"],
            "below_threshold": counts["below"],
            "source_id": MODELS,
        }
        for year, counts in sorted(per_year.items())
    ]

    write_dataset(
        "compute-thresholds",
        records,
        source_ids=[MODELS],
        unit="models per year",
        notes=(
            f"Models whose reported training compute reaches the EU AI Act Article 51 "
            f"systemic-risk presumption of {EU_SYSTEMIC_RISK_FLOP:.0e} FLOP. "
            f"{len(crossing)} models in the dataset cross it. Compute figures are often "
            "estimates, so treat borderline cases as indicative, not as legal findings."
        ),
        retrieved=retrieved,
    )


# Our own grouping of Epoch's benchmarks into things a non-specialist can hold in
# their head. Epoch's CSV has no category column, so this is a classification we
# are adding, and it is labelled as ours wherever it is rendered.
#
# `tier` answers the question a lay reader actually asks about a benchmark score,
# which is not "what is GPQA" but "who else could do this". It is a statement
# about the difficulty of the questions, not about the model.
#
# A task that appears upstream and is not listed here fails the build. That is
# deliberate: the alternative is a silent "Other" bucket that grows until the
# categories mean nothing, and Epoch adds benchmarks regularly.
BENCHMARK_CATEGORIES = {
    "OTIS Mock AIME 2024-2025": ("Mathematics", "olympiad"),
    "MATH level 5": ("Mathematics", "school"),
    "FrontierMath-2025-02-28-Public": ("Mathematics", "research"),
    "FrontierMath-2025-02-28-Private": ("Mathematics", "research"),
    "FrontierMath-Tiers-1-3-v2-Private": ("Mathematics", "research"),
    "FrontierMath-Tier-4-2025-07-01-Public": ("Mathematics", "research"),
    "FrontierMath-Tier-4-2025-07-01-Private": ("Mathematics", "research"),
    "FrontierMath-Tier-4-v2-Private": ("Mathematics", "research"),
    "FrontierMath-Erdos": ("Mathematics", "unsolved"),
    "OEIS Open": ("Mathematics", "unsolved"),
    "OEIS Open Lite": ("Mathematics", "unsolved"),
    "GPQA diamond": ("Science knowledge", "expert"),
    "SimpleQA Verified": ("Factual accuracy", "general"),
    "SWE-Bench verified": ("Software engineering", "professional"),
    "MirrorCode": ("Software engineering", "professional"),
    "Chess Puzzles": ("Games and planning", "expert"),
    "Mystery Game Puzzles": ("Games and planning", "general"),
    "Furniture Assembly": ("Games and planning", "general"),
    "EBR-bench": ("Learning from experience", "general"),
}

# What each tier means, in one line, for the reader who has never met the
# benchmark. Ordered easiest first, which is the order they are plotted in.
TIERS = {
    "school": "Problems a strong secondary-school student could do.",
    "general": "Problems most adults could do, given the time.",
    "olympiad": "Competition problems at national olympiad standard.",
    "professional": "Real work from the job, taken from real projects.",
    "expert": "Problems that need a specialist in the field.",
    "research": "Problems that need a working researcher, sometimes hours of one.",
    "unsolved": "Problems nobody has a published answer to.",
}

CATEGORY_NOTES = {
    "Mathematics": "Solving stated mathematical problems with a checkable answer.",
    "Science knowledge": "Answering science questions that resist search.",
    "Factual accuracy": "Answering short factual questions without inventing an answer.",
    "Software engineering": "Making a real codebase pass tests it was failing.",
    "Games and planning": "Choosing well in a game with rules and a long horizon.",
    "Learning from experience": "Getting better at an unfamiliar task by repeating it.",
}


def build_benchmarks(offline: bool) -> None:
    path, retrieved = fetch(BENCHMARKS, offline=offline)
    rows = read_csv(path)

    score_col = "Best score (across scorers)"
    if score_col not in rows[0]:
        raise ValueError(f"{BENCHMARKS}: score column {score_col!r} missing")

    # Best score per (benchmark, month). Running max gives the frontier line:
    # what the best available model could do at that point in time.
    best: dict[tuple[str, str], dict] = {}
    for row in rows:
        task = _text(row.get("task"))
        month = _year_month(row.get("Version release date"))
        score = _float(row.get(score_col))
        if not task or not month or score is None:
            continue
        key = (task, month)
        if key not in best or score > best[key]["score"]:
            best[key] = {
                "score": score,
                "model": _text(row.get("Display name") or row.get("model")),
                "organisation": _text(row.get("Organization")),
            }

    by_task: dict[str, list] = defaultdict(list)
    for (task, month), entry in sorted(best.items(), key=lambda kv: kv[0][1]):
        by_task[task].append({"month": month, **entry})

    records = []
    for task, points in by_task.items():
        # Only benchmarks with enough history to show a trend.
        if len(points) < 4:
            continue
        running = 0.0
        frontier = []
        for point in points:
            running = max(running, point["score"])
            frontier.append(
                {
                    "month": point["month"],
                    "best": round(running, 4),
                    "model": point["model"],
                }
            )
        if task not in BENCHMARK_CATEGORIES:
            raise ValueError(
                f"Benchmark {task!r} has no category. Epoch has added a task since this "
                f"mapping was written. Add it to BENCHMARK_CATEGORIES with a tier rather "
                f"than letting it fall into an unlabelled bucket."
            )
        category, tier = BENCHMARK_CATEGORIES[task]

        # Months from the first recorded run to the first month the frontier
        # crossed 90 percent. This is how long a benchmark stayed useful, and it
        # is the number the saturation story is actually about.
        crossed = next((p["month"] for p in frontier if p["best"] >= 0.9), None)
        records.append(
            {
                "benchmark": task,
                "category": category,
                "category_note": CATEGORY_NOTES[category],
                "tier": tier,
                "tier_meaning": TIERS[tier],
                "points": frontier,
                "first_month": frontier[0]["month"],
                "latest_month": frontier[-1]["month"],
                "latest_best": frontier[-1]["best"],
                "saturated_month": crossed,
                "months_to_saturation": _months_between(frontier[0]["month"], crossed),
                "runs": len(points),
                "source_id": BENCHMARKS,
            }
        )

    records.sort(key=lambda r: r["latest_best"], reverse=True)

    write_dataset(
        "benchmark-frontier",
        records,
        source_ids=[BENCHMARKS],
        unit="score (0 to 1)",
        notes=(
            "Best score achieved on each benchmark by any evaluated model, as a running "
            "maximum by month. Mixes Epoch's own evaluation runs with externally reported "
            "scores, which are not strictly comparable. A rising line shows the best "
            "available capability, not the typical one. Category and difficulty tier are "
            "our own classification, not Epoch's."
        ),
        retrieved=retrieved,
    )


def build_clusters(offline: bool) -> None:
    path, retrieved = fetch(CLUSTERS, offline=offline)
    rows = read_csv(path)

    by_country: dict[str, dict] = defaultdict(
        lambda: {"clusters": 0, "power_mw": 0.0, "known_power": 0}
    )
    for row in rows:
        country = _text(row.get("Country"))
        if not country:
            continue
        entry = by_country[country]
        entry["clusters"] += 1
        power = _float(row.get("Power Capacity (MW)"))
        if power:
            entry["power_mw"] += power
            entry["known_power"] += 1

    records = [
        {
            "country": country,
            "clusters": entry["clusters"],
            "power_mw": round(entry["power_mw"], 1),
            "clusters_with_known_power": entry["known_power"],
            "source_id": CLUSTERS,
        }
        for country, entry in sorted(
            by_country.items(), key=lambda kv: kv[1]["clusters"], reverse=True
        )
    ]

    write_dataset(
        "compute-clusters",
        records,
        source_ids=[CLUSTERS],
        unit="clusters and megawatts",
        notes=(
            "Publicly reported GPU clusters grouped by country. Power capacity is summed "
            "only over clusters where it is known, so totals understate real capacity. "
            "Reporting is uneven between countries: this measures documented capacity, "
            "which is not the same as capacity."
        ),
        retrieved=retrieved,
    )


def build_releases(offline: bool) -> None:
    """Every notable model with a publication date, compute figure or not.

    Separate from frontier-models because that dataset requires a compute value
    and so covers roughly half of what Epoch tracks. Release decisions, domains
    and who built them are knowable for models whose training compute is not,
    and filtering those out would bias every count on the capability page toward
    the labs that publish compute figures.
    """
    path, retrieved = fetch(MODELS, offline=offline)
    rows = read_csv(path)

    records = []
    for row in rows:
        published = row.get("Publication date") or ""
        model = _text(row.get("Model"))
        if not model or len(published) < 7:
            continue
        records.append(
            {
                "model": model,
                "organisation": _text(row.get("Organization")),
                "country": _text(row.get("Country (of organization)")),
                "published": published[:10],
                "domain": _text(row.get("Domain")).split(",")[0],
                "accessibility": _access(row.get("Model accessibility")),
                "org_category": _text(row.get("Organization categorization")).split(",")[0],
                "source_id": MODELS,
            }
        )

    records.sort(key=lambda r: r["published"])

    write_dataset(
        "model-releases",
        records,
        source_ids=[MODELS],
        unit="models",
        notes=(
            "Every notable model with a publication date, whether or not its training "
            "compute is known. Inclusion in Epoch's database is editorial, not "
            "exhaustive, so counts describe what has been judged notable rather than "
            "everything built. Accessibility is missing for a substantial minority and "
            "is reported as 'not recorded' rather than folded into 'unreleased'."
        ),
        retrieved=retrieved,
    )


# Our own grouping of each site's owner, which Epoch defines as the owner of the
# chips, not of the building. The line that matters for a reader is who controls
# the compute: a company renting it to others, or a developer running it for its
# own models. Epoch has no such column, so this is ours and the page says so.
#
# An owner that appears upstream and is not listed here fails the build, as an
# unmapped benchmark does. "Other" is a deliberate list, not a catch-all: SoftBank
# is an investor, G42 a technology group, Cipher Mining a bitcoin miner hosting AI,
# VNET a datacentre operator, and AI XPV Platform could not be identified from
# any public source.
OWNER_CATEGORIES = {
    "Amazon": "Cloud provider",
    "Google": "Cloud provider",
    "Microsoft": "Cloud provider",
    "Oracle": "Cloud provider",
    "Alibaba": "Cloud provider",
    "Huawei": "Cloud provider",
    "CoreWeave": "Cloud provider",
    "Nebius": "Cloud provider",
    "Nscale": "Cloud provider",
    "Firmus": "Cloud provider",
    "Core42": "Cloud provider",
    "Meta": "AI developer",
    "SpaceXAI": "AI developer",
    "Mistral AI": "AI developer",
    "Softbank": "Other",
    "G42": "Other",
    "Cipher Mining": "Other",
    "VNET": "Other",
    "AI XPV Platform": "Other",
}
NO_OWNER = "Owner not recorded"

# Epoch's three confidence signifiers, from its records documentation.
CONFIDENCE = ("confident", "likely", "speculative")

DC_SITE_COLUMNS = {
    "Name", "Owner", "Users", "Project", "Country", "All chip types", "Current power (MW)",
}
DC_TIMELINE_COLUMNS = {
    "Data center", "Date", "IT power (MW)", "Power (MW)", "H100 equivalents",
}


def _tagged(value: str | None, what: str) -> tuple[str, str | None]:
    """Split "Oracle #likely" into ("Oracle", "likely").

    A name with no signifier keeps a null confidence rather than borrowing one:
    three entries upstream carry none, and "not stated" is not "confident".
    """
    text = _text(value)
    match = re.fullmatch(r"(.*?)\s*#(\w+)", text)
    if not match:
        return text, None
    name, level = match.group(1).strip(), match.group(2).lower()
    if level not in CONFIDENCE:
        raise ValueError(f"{DATACENTRES}: {what}: unknown confidence signifier #{level}")
    return name, level


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class _Unsupported:
    """An Astro prop type this decoder does not read. Never a valid field value."""

    def __init__(self, kind: int):
        self.kind = kind

    def __repr__(self) -> str:
        return f"<unsupported Astro prop type {self.kind}>"


def _astro(node):
    """Decode an Astro island's serialised props.

    Every value is a [type, payload] pair: 0 a plain value, whose objects hold
    further pairs, and 1 an array of pairs. Other types (dates, maps, regular
    expressions) are left as a marker the caller's validation rejects, so a field
    that changes type fails the build instead of reading as empty.
    """
    if isinstance(node, list) and len(node) == 2 and isinstance(node[0], int):
        kind, payload = node
        if kind == 0:
            if isinstance(payload, dict):
                return {key: _astro(value) for key, value in payload.items()}
            return payload
        if kind == 1:
            return [_astro(value) for value in payload]
        return _Unsupported(kind)
    return node


def map_sites(page: str) -> dict[str, dict]:
    """Every site on Epoch's hub map, by name, with its coordinates and place."""
    for match in re.finditer(r'\sprops="([^"]*)"', page):
        raw = html.unescape(match.group(1))
        if '"dataCenters"' not in raw:
            continue
        props = {key: _astro(value) for key, value in json.loads(raw).items()}
        sites = props.get("dataCenters")
        break
    else:
        raise ValueError(
            f"{DATACENTRES}: no map data found on {DC_MAP}. Epoch has changed the page; "
            f"check whether the coordinates are now published as a download."
        )
    if not isinstance(sites, list) or not sites:
        raise ValueError(f"{DATACENTRES}: map data is not a list of sites: {type(sites).__name__}")

    out: dict[str, dict] = {}
    for site in sites:
        name = site.get("id") if isinstance(site, dict) else None
        facts = site.get("facts") if isinstance(site, dict) else None
        lng_lat = site.get("lngLat") if isinstance(site, dict) else None
        if not isinstance(name, str) or not isinstance(facts, dict):
            raise ValueError(f"{DATACENTRES}: map site without a name or facts: {site!r:.200}")
        if (
            not isinstance(lng_lat, list)
            or len(lng_lat) != 2
            or not all(isinstance(v, (int, float)) for v in lng_lat)
            or not (-180 <= lng_lat[0] <= 180 and -90 <= lng_lat[1] <= 90)
        ):
            raise ValueError(f"{DATACENTRES}: {name}: unusable coordinates {lng_lat!r}")
        place = [_text(facts.get(k)) for k in ("city", "state") if isinstance(facts.get(k), str)]
        out[name] = {
            "lon": round(float(lng_lat[0]), 4),
            "lat": round(float(lng_lat[1]), 4),
            "place": ", ".join(p for p in place if p) or None,
            "operational": facts.get("operational"),
        }
    return out


def _timeline(rows: list[dict]) -> list[tuple[str, float, float | None, float | None]]:
    """(date, IT MW, facility MW, H100e) for every dated row with an IT power figure.

    Epoch leaves a row's figures blank when it records only a construction note,
    so a blank is skipped rather than read as zero, which would switch a working
    site off for a day.
    """
    series = []
    for row in rows:
        day = (row.get("Date") or "").strip()[:10]
        it = _float(row.get("IT power (MW)"))
        if len(day) == 10 and it is not None:
            series.append((day, it, _float(row.get("Power (MW)")), _float(row.get("H100 equivalents"))))
    return sorted(series)


def datacentre_records(
    sites: list[dict], timelines: list[dict], placed: dict[str, dict], today: str
) -> list[dict]:
    """One record per site, from Epoch's three published pieces.

    `today` is the retrieval date. Timeline rows after it are Epoch's
    projection, so "now" is the last row on or before it and "at completion" is
    the last row of all: the last, not the largest, because a site can shrink
    (Colossus 1 removed chips in 2025 and added them back).
    """
    if not sites or not timelines:
        raise ValueError(f"{DATACENTRES}: empty download")
    for label, rows, required in (
        ("data_centers.csv", sites, DC_SITE_COLUMNS),
        ("data_center_timelines.csv", timelines, DC_TIMELINE_COLUMNS),
    ):
        missing = required - set(rows[0].keys())
        if missing:
            raise ValueError(f"{DATACENTRES}: {label}: expected columns missing: {sorted(missing)}")

    by_site: dict[str, list[dict]] = defaultdict(list)
    for row in timelines:
        by_site[_text(row.get("Data center"))].append(row)

    records = []
    seen_ids: set[str] = set()
    for row in sites:
        name = _text(row["Name"])
        if name not in placed:
            raise ValueError(
                f"{DATACENTRES}: {name!r} is in the download but not on the map page, so it "
                f"has no coordinates. Epoch's two publications disagree; do not guess a location."
            )
        series = _timeline(by_site.get(name, []))
        if not series:
            raise ValueError(f"{DATACENTRES}: {name!r} has no timeline with an IT power figure")

        past = [point for point in series if point[0] <= today]
        now = past[-1] if past else (today, 0.0, 0.0, 0.0)
        full = series[-1]
        online = next((point[0] for point in series if point[1] > 0), None)

        it_now, it_full = now[1], full[1]
        if it_now > 0:
            stage = "Expanding" if it_full > it_now else "Operating"
        else:
            stage = "Under construction"

        # Epoch's own flag on the map, against ours from the timeline. They are
        # computed on different days, so a disagreement is printed, not fatal:
        # a projected first building can come online between the two.
        flag = placed[name]["operational"]
        if isinstance(flag, bool) and flag != (it_now > 0):
            print(f"  note {DATACENTRES}: {name}: map says operational={flag}, timeline says {it_now} MW on {today}")

        owner, owner_conf = _tagged(row.get("Owner"), f"{name} owner")
        if owner and owner not in OWNER_CATEGORIES:
            raise ValueError(
                f"{DATACENTRES}: owner {owner!r} ({name}) has no category. Epoch has added an "
                f"owner since this mapping was written. Add it to OWNER_CATEGORIES."
            )
        users = []
        for part in (row.get("Users") or "").split(","):
            if part.strip():
                user, conf = _tagged(part, f"{name} user")
                users.append({"name": user, "confidence": conf})
        project, project_conf = _tagged(row.get("Project"), f"{name} project")

        site_id = _slug(name)
        if not site_id:
            raise ValueError(f"{DATACENTRES}: {name!r} gives an empty id, so it has no page to link")
        if site_id in seen_ids:
            raise ValueError(f"{DATACENTRES}: two sites share the id {site_id!r}")
        seen_ids.add(site_id)

        records.append(
            {
                "id": site_id,
                "name": name,
                "owner": owner or None,
                "owner_confidence": owner_conf if owner else None,
                "category": OWNER_CATEGORIES.get(owner, NO_OWNER),
                "users": users,
                "project": project or None,
                "project_confidence": project_conf if project else None,
                "country": _text(row.get("Country")) or None,
                "place": placed[name]["place"],
                "lat": placed[name]["lat"],
                "lon": placed[name]["lon"],
                "stage": stage,
                "online": online,
                "as_of": now[0],
                "it_mw": it_now,
                "facility_mw": now[2],
                "h100e": round(now[3]) if now[3] is not None else None,
                "complete": full[0],
                "it_mw_full": it_full,
                "facility_mw_full": full[2],
                "h100e_full": round(full[3]) if full[3] is not None else None,
                "chips": [c.strip() for c in _text(row.get("All chip types")).split(",") if c.strip()],
                "url": DC_SITE_PAGE.format(site_id),
                "source_id": DATACENTRES,
            }
        )

    unplaced = set(placed) - {r["name"] for r in records}
    if unplaced:
        print(f"  note {DATACENTRES}: on the map but not in the download: {sorted(unplaced)}")

    records.sort(key=lambda r: (-r["it_mw_full"], r["name"]))
    return records


def build_datacentres(offline: bool) -> None:
    sites_path, retrieved = fetch(DATACENTRES, offline=offline)
    timeline_path, _ = fetch(
        DATACENTRES, url=DC_TIMELINES, filename=f"{DATACENTRES}-timelines.csv", offline=offline
    )
    map_path, _ = fetch(
        DATACENTRES, url=DC_MAP, filename=f"{DATACENTRES}-map.html", offline=offline, fmt="html"
    )
    records = datacentre_records(
        read_csv(sites_path, encoding="utf-8"),
        read_csv(timeline_path, encoding="utf-8"),
        map_sites(map_path.read_text(encoding="utf-8")),
        today=retrieved[:10],
    )

    write_dataset(
        "ai-datacentres",
        records,
        source_ids=[DATACENTRES],
        unit="MW of IT power",
        notes=(
            "Every site in Epoch AI's AI Data Centers hub. Power, compute and dates are "
            "Epoch's estimates; figures dated after the retrieval date are Epoch's "
            "projection. Owner is the owner of the chips. Category is this site's own "
            "grouping of the owner, not Epoch's."
        ),
        retrieved=retrieved,
    )


def run(offline: bool = False) -> None:
    build_models(offline=offline)
    build_releases(offline=offline)
    build_benchmarks(offline=offline)
    build_clusters(offline=offline)
    # Last, so a change to Epoch's map page cannot stop the four above.
    build_datacentres(offline=offline)


def _self_check() -> None:
    """The data-centre derivation, against small hand-made inputs. No network."""
    site = {
        "Name": "Test Site", "Owner": "Oracle #likely",
        "Users": "OpenAI #confident, Microsoft #speculative, Meta", "Project": "Stargate #confident",
        "Country": "United States", "All chip types": "B200,GB200",
        "Current power (MW)": "100",
    }
    timeline = [
        {"Data center": "Test Site", "Date": "2025-01-01", "IT power (MW)": "0", "Power (MW)": "0", "H100 equivalents": "0"},
        {"Data center": "Test Site", "Date": "2025-06-01", "IT power (MW)": "100", "Power (MW)": "140", "H100 equivalents": "120000.4"},
        # A note-only row: blank figures must not read as the site switching off.
        {"Data center": "Test Site", "Date": "2025-09-01", "IT power (MW)": "", "Power (MW)": "", "H100 equivalents": ""},
        {"Data center": "Test Site", "Date": "2027-01-01", "IT power (MW)": "300", "Power (MW)": "420", "H100 equivalents": ""},
    ]
    placed = {"Test Site": {"lon": -99.7, "lat": 32.5, "place": "Abilene, Texas", "operational": True}}

    [r] = datacentre_records([site], timeline, placed, today="2026-01-01")
    assert r["stage"] == "Expanding", r["stage"]
    assert (r["it_mw"], r["facility_mw"], r["h100e"]) == (100.0, 140.0, 120000), r
    assert (r["it_mw_full"], r["complete"], r["h100e_full"]) == (300.0, "2027-01-01", None), r
    assert r["online"] == "2025-06-01" and r["as_of"] == "2025-06-01", r
    assert (r["owner"], r["owner_confidence"], r["category"]) == ("Oracle", "likely", "Cloud provider")
    assert r["users"] == [
        {"name": "OpenAI", "confidence": "confident"},
        {"name": "Microsoft", "confidence": "speculative"},
        {"name": "Meta", "confidence": None},
    ], r["users"]
    assert r["chips"] == ["B200", "GB200"] and r["id"] == "test-site"
    assert r["url"] == "https://epoch.ai/data/ai-data-centers/directory/test-site", r["url"]
    # Punctuation collapses the way Epoch's paths do, and no record links a sheet.
    assert _slug("Google Council Bluffs (East)") == "google-council-bluffs-east"
    assert _slug("CoreWeave Dalton 1 & 2") == "coreweave-dalton-1-2"
    assert "sheet" not in r and "google" not in json.dumps(r), r

    # Once the projected date passes, the same data reads as fully built.
    [later] = datacentre_records([site], timeline, placed, today="2027-06-01")
    assert later["stage"] == "Operating" and later["it_mw"] == 300.0, later

    # Before anything is built: under construction, and a zero that is Epoch's.
    [early] = datacentre_records([site], timeline, placed, today="2025-03-01")
    assert early["stage"] == "Under construction" and early["it_mw"] == 0.0, early

    # A site that shrinks is measured at its last row, not its largest.
    shrink = timeline[:2] + [{**timeline[1], "Date": "2025-08-01", "IT power (MW)": "80"}]
    [small] = datacentre_records([site], shrink, placed, today="2026-01-01")
    assert small["it_mw_full"] == 80.0 and small["stage"] == "Operating", small

    # No owner: its own category, and null rather than an empty string.
    [orphan] = datacentre_records([{**site, "Owner": ""}], timeline, placed, today="2026-01-01")
    assert orphan["owner"] is None and orphan["category"] == NO_OWNER, orphan

    # The failures that must be loud.
    for label, call in (
        ("an unmapped owner", lambda: datacentre_records([{**site, "Owner": "Newco #confident"}], timeline, placed, "2026-01-01")),
        ("a site with no coordinates", lambda: datacentre_records([site], timeline, {}, "2026-01-01")),
        ("a missing column", lambda: datacentre_records([{k: v for k, v in site.items() if k != "Owner"}], timeline, placed, "2026-01-01")),
        ("an unknown signifier", lambda: datacentre_records([{**site, "Owner": "Oracle #sure"}], timeline, placed, "2026-01-01")),
        ("a site with no timeline", lambda: datacentre_records([site], [{**timeline[0], "Data center": "Elsewhere"}], placed, "2026-01-01")),
        ("a name with no page", lambda: datacentre_records(
            [{**site, "Name": "()"}], [{**t, "Data center": "()"} for t in timeline],
            {"()": placed["Test Site"]}, "2026-01-01")),
    ):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError(f"datacentre_records accepted {label}")

    # The map decoder, on a page shaped like Epoch's.
    props = {"dataCenters": [1, [[0, {
        "id": [0, "Test Site"],
        "facts": [0, {"city": [0, "Abilene"], "state": [0, "Texas"], "operational": [0, True]}],
        "lngLat": [1, [[0, -99.7], [0, 32.5]]],
    }]]]}
    page = f'<astro-island props="{html.escape(json.dumps(props))}"></astro-island>'
    got = map_sites(page)
    assert got == {"Test Site": {"lon": -99.7, "lat": 32.5, "place": "Abilene, Texas", "operational": True}}, got
    for broken in (
        page.replace("dataCenters", "sites"),
        page.replace(html.escape("[0, -99.7]"), html.escape("[3, \"2026-01-01\"]")),
        page.replace(html.escape("[0, 32.5]"), html.escape("[0, 95.0]")),
    ):
        try:
            map_sites(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("map_sites accepted a page it should have refused")

    print(f"fetch_epoch self-check passed: {len(OWNER_CATEGORIES)} owners mapped")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    elif "--check-links" in sys.argv:
        # Every site page the list links to, from the written dataset: 93
        # requests, so by hand only, like the other modules' link probes.
        sites = json.loads((PROCESSED / "ai-datacentres.json").read_text(encoding="utf-8"))
        raise SystemExit(1 if check_links((r["name"], r["url"]) for r in sites["records"]) else 0)
    else:
        run(offline="--offline" in sys.argv)
