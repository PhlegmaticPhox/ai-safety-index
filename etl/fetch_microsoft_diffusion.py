"""Microsoft AI Diffusion - share of working-age population using AI tools, by economy.

147 economies, three time points, MIT licensed. This is the exposure layer of the
flagship map: how much a population actually encounters AI systems, to be set
against how prepared its jurisdiction is to govern them.

Read the caveats in data/sources.json before drawing conclusions. In short, this
measures Microsoft-visible AI use, scaled by a model - not observed total AI use.
"""

from __future__ import annotations

import re
import sys

from common import fetch, read_csv, write_dataset

SOURCE_ID = "microsoft-ai-diffusion"

# Column header -> the period it reports. Upstream renames these each release, which
# is exactly why we match on pattern and fail loudly rather than hardcoding positions.
PERIOD_PATTERN = re.compile(r"^(H[12]|Q[1-4])\s+(\d{4})\s+AI Diffusion$", re.IGNORECASE)


def parse_percent(value: str) -> float | None:
    value = (value or "").strip().rstrip("%").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def run(offline: bool = False) -> None:
    path, retrieved = fetch(SOURCE_ID, offline=offline)
    rows = read_csv(path)
    if not rows:
        raise ValueError("Microsoft diffusion CSV parsed to zero rows")

    headers = list(rows[0].keys())
    periods = {h: _normalise_period(h) for h in headers if PERIOD_PATTERN.match(h or "")}
    if not periods:
        raise ValueError(
            f"No period columns matched in {headers!r}. Upstream changed the header "
            f"format; update PERIOD_PATTERN rather than guessing column positions."
        )

    records = []
    skipped = []
    for row in rows:
        economy = (row.get("Economy") or "").strip()
        if not economy:
            continue
        values = {
            label: parse_percent(row[header])
            for header, label in periods.items()
            if parse_percent(row[header]) is not None
        }
        if not values:
            skipped.append(economy)
            continue
        latest_period = sorted(values)[-1]
        records.append(
            {
                "entity": economy,
                "values": values,
                "latest_period": latest_period,
                "latest": values[latest_period],
                "source_id": SOURCE_ID,
            }
        )

    if skipped:
        print(f"  note: {len(skipped)} economies had no usable values: {', '.join(skipped[:5])}")

    records.sort(key=lambda r: r["latest"], reverse=True)

    write_dataset(
        "ai-exposure",
        records,
        source_ids=[SOURCE_ID],
        unit="percent of working-age population",
        notes=(
            "Share of each economy's working-age population actively using AI tools, "
            "estimated from anonymised Microsoft telemetry adjusted for device and "
            "internet penetration. Measures Microsoft-visible use, scaled by a model - "
            "not observed total AI use."
        ),
        retrieved=retrieved,
    )


def _normalise_period(header: str) -> str:
    """'Q1 2026 AI Diffusion' -> '2026-Q1', so lexical sort is chronological."""
    match = PERIOD_PATTERN.match(header)
    assert match, header
    part, year = match.group(1).upper(), match.group(2)
    return f"{year}-{part}"


if __name__ == "__main__":
    run(offline="--offline" in sys.argv)
