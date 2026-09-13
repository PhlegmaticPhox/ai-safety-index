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

from common import fetch, read_csv, write_dataset

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


def _float(value: str | None) -> float | None:
    if not value or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


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
                "model": row["Model"].strip(),
                "organisation": (row.get("Organization") or "").strip(),
                "country": (row.get("Country (of organization)") or "").strip(),
                "published": published[:10],
                "compute_flop": compute,
                "parameters": _float(row.get("Parameters")),
                "confidence": (row.get("Confidence") or "").strip(),
                "domain": (row.get("Domain") or "").strip(),
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
        task = (row.get("task") or "").strip()
        month = _year_month(row.get("Version release date"))
        score = _float(row.get(score_col))
        if not task or not month or score is None:
            continue
        key = (task, month)
        if key not in best or score > best[key]["score"]:
            best[key] = {
                "score": score,
                "model": (row.get("Display name") or row.get("model") or "").strip(),
                "organisation": (row.get("Organization") or "").strip(),
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
        records.append(
            {
                "benchmark": task,
                "points": frontier,
                "first_month": frontier[0]["month"],
                "latest_month": frontier[-1]["month"],
                "latest_best": frontier[-1]["best"],
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
            "available capability, not the typical one."
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
        country = (row.get("Country") or "").strip()
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


def run(offline: bool = False) -> None:
    build_models(offline=offline)
    build_benchmarks(offline=offline)
    build_clusters(offline=offline)


if __name__ == "__main__":
    run(offline="--offline" in sys.argv)
