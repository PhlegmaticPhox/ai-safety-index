"""Epoch AI: model registry, benchmark runs, compute clusters, accelerator specs.

Produces four datasets:
  frontier-models      models with a training-compute figure, for the capability trend
  benchmark-frontier   best-score-to-date per benchmark, for the saturation view
  compute-clusters     clusters aggregated by country, for the compute map
  compute-thresholds   which released models cross the EU AI Act systemic-risk threshold

All four are CC BY 4.0. Read the caveats in data/sources.json before drawing
conclusions, especially on cluster counts: Chinese clusters are systematically
less well documented than US ones, so the country split measures reporting
opacity as much as it measures capacity.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date

from common import fetch, normalise_dashes, read_csv, write_dataset

MODELS = "epoch-notable-models"
BENCHMARKS = "epoch-benchmarks"
CLUSTERS = "epoch-gpu-clusters"
HARDWARE = "epoch-ml-hardware"

# EU AI Act Art. 51(2): a GPAI model is presumed to carry systemic risk when the
# cumulative training compute exceeds 10^25 FLOP. This is the only compute
# threshold currently written into binding law anywhere, which is why it is the
# only one we plot. Others exist in guidance and rescinded executive orders; those
# belong in the governance section as text, not as a line on a chart.
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


def run(offline: bool = False) -> None:
    build_models(offline=offline)
    build_releases(offline=offline)
    build_benchmarks(offline=offline)
    build_clusters(offline=offline)


if __name__ == "__main__":
    run(offline="--offline" in sys.argv)
