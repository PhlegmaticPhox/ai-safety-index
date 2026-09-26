"""Run every ETL module.

One source failing must not take the others down: a partial refresh with a loud
warning beats a green build with no data. Exits non-zero if anything failed, so
CI reports it, but only after everything that could run has run.

Usage:
    python etl/run_all.py              # fetch fresh where cache is stale
    python etl/run_all.py --offline    # build from cache only, no network
"""

from __future__ import annotations

import importlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    "fetch_microsoft_diffusion",
    "fetch_epoch",
    "fetch_eurostat",
    "fetch_news",
    "fetch_openalex",
    # Hand-coded rather than fetched, so these run identically offline. They are
    # in this list because they are datasets like any other and have to pass the
    # same licence guard and idempotence check.
    "build_governance",
    "build_policy_index",
    "build_frontier_index",
    "build_usage_index",
    "build_environment_index",
]


def main() -> int:
    offline = "--offline" in sys.argv
    if offline:
        print("running offline - using cached raw data only\n")

    failed: list[tuple[str, Exception]] = []

    for name in MODULES:
        print(f"{name}:")
        try:
            module = importlib.import_module(name)
            module.run(offline=offline)
        except Exception as exc:  # noqa: BLE001 - one bad source must not stop the rest
            failed.append((name, exc))
            print(f"  FAILED: {exc}")
            traceback.print_exc(limit=3)
        print()

    # Datasets only change on disk when their records change, so this one small
    # file carries "when did we last look", which is what tells a reader the
    # pipeline is alive rather than abandoned.
    _write_status(failed, offline)

    if failed:
        print(f"{len(failed)} of {len(MODULES)} source(s) failed:")
        for name, exc in failed:
            print(f"  - {name}: {type(exc).__name__}: {exc}")
        return 1

    print(f"all {len(MODULES)} source(s) up to date")
    return 0


def _write_status(failed: list[tuple[str, Exception]], offline: bool) -> None:
    from datetime import datetime, timezone

    from common import CONFIRMED

    path = Path(__file__).resolve().parent.parent / "data" / "processed" / "_status.json"

    # Per dataset, when its data was last confirmed: fetched, or reviewed, and
    # found either changed or identical. Merged over the previous file rather than
    # replacing it, so a source that fails today keeps yesterday's confirmation
    # instead of falling back to the day its figures last moved. Only ever moves
    # forward.
    confirmed: dict[str, str] = {}
    if path.exists():
        try:
            confirmed = json.loads(path.read_text(encoding="utf-8")).get("datasets", {})
        except (json.JSONDecodeError, OSError):
            confirmed = {}
    for name, stamp in CONFIRMED.items():
        if stamp > confirmed.get(name, ""):
            confirmed[name] = stamp

    failed_names = {name for name, _ in failed}
    status = {
        "last_checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "offline": offline,
        "modules": {
            name: ("failed" if name in failed_names else "ok") for name in MODULES
        },
        "datasets": dict(sorted(confirmed.items())),
    }
    path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {path.name}")


if __name__ == "__main__":
    raise SystemExit(main())
