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
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    "fetch_microsoft_diffusion",
]


def main() -> int:
    offline = "--offline" in sys.argv
    if offline:
        print("running offline — using cached raw data only\n")

    failed: list[tuple[str, Exception]] = []

    for name in MODULES:
        print(f"{name}:")
        try:
            module = importlib.import_module(name)
            module.run(offline=offline)
        except Exception as exc:  # noqa: BLE001 — one bad source must not stop the rest
            failed.append((name, exc))
            print(f"  FAILED: {exc}")
            traceback.print_exc(limit=3)
        print()

    if failed:
        print(f"{len(failed)} of {len(MODULES)} source(s) failed:")
        for name, exc in failed:
            print(f"  - {name}: {type(exc).__name__}: {exc}")
        return 1

    print(f"all {len(MODULES)} source(s) up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
