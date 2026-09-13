"""Shared ETL plumbing: source registry, cached fetch, licence guard, output envelope.

Design rule for the whole pipeline: a processed record never travels without a
`source_id`, and a dataset is never written without passing `guard()`. That makes
attribution a join rather than a habit, and makes an accidental licence breach a
build failure instead of a lawyer's letter.

Stdlib only, deliberately — this runs in CI and should have nothing to break.
"""

from __future__ import annotations

import csv
import io
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
SOURCES_FILE = DATA / "sources.json"

# Identify ourselves honestly. A publisher who wants to block us should be able to.
USER_AGENT = "AISafetyIndexBot/0.1 (+https://github.com/; data pipeline; contact via repo issues)"

# Licence states that must never reach a rendered chart.
BLOCKED_REDISTRIBUTION = {"prohibited", "no-derivatives"}


class LicenceError(RuntimeError):
    """Raised when a dataset would be published in breach of its source licence."""


class FetchError(RuntimeError):
    """Raised when a source could not be retrieved and no cached copy exists."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_sources() -> dict[str, dict[str, Any]]:
    with SOURCES_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)["sources"]


def get_source(source_id: str) -> dict[str, Any]:
    sources = load_sources()
    if source_id not in sources:
        raise KeyError(
            f"Unknown source_id {source_id!r}. Register it in data/sources.json "
            f"before using it, so its licence travels with its data."
        )
    return sources[source_id]


def guard(*source_ids: str) -> None:
    """Refuse to build a dataset whose licence forbids republication.

    Called by write_dataset, so every output passes through it. Sources such as
    Artificial Analysis and the Stanford AI Index are registered precisely so that
    wiring them in fails loudly here rather than silently shipping.
    """
    for source_id in source_ids:
        source = get_source(source_id)
        state = source.get("redistribution")
        if state in BLOCKED_REDISTRIBUTION:
            raise LicenceError(
                f"Source {source_id!r} ({source['publisher']}) is marked "
                f"redistribution={state!r} and must not be rendered on the site.\n"
                f"  Licence: {source['licence']}\n"
                f"  Why:     {source.get('caveats', '')}\n"
                f"Link out to {source['landing_page']} instead."
            )


def fetch(
    source_id: str,
    url: str | None = None,
    filename: str | None = None,
    offline: bool = False,
    max_age_hours: float = 12.0,
    retries: int = 3,
) -> tuple[Path, str]:
    """Download a source to data/raw/, returning (path, retrieved_iso8601).

    Serves a cached copy when it is fresh, when offline is set, or when the network
    fails but a previous copy exists. A stale-but-present dataset is far better than
    a broken build: the site surfaces staleness to the reader rather than vanishing.
    """
    source = get_source(source_id)
    url = url or source.get("url")
    if not url:
        raise FetchError(f"Source {source_id!r} has no URL; it is reference-only.")

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / (filename or f"{source_id}{_ext_for(source.get('format'))}")
    meta_path = path.with_suffix(path.suffix + ".meta.json")

    cached = _read_meta(meta_path)
    if cached and (offline or _age_hours(cached["retrieved"]) < max_age_hours):
        if path.exists():
            return path, cached["retrieved"]

    if offline:
        raise FetchError(f"--offline set but no cached copy of {source_id!r} at {path}")

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
            path.write_bytes(body)
            retrieved = utcnow()
            meta_path.write_text(
                json.dumps({"url": url, "retrieved": retrieved, "bytes": len(body)}, indent=2),
                encoding="utf-8",
            )
            print(f"  fetched {source_id}: {len(body):,} bytes")
            return path, retrieved
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)

    if cached and path.exists():
        print(f"  WARNING {source_id}: fetch failed ({last_error}); using cached copy "
              f"from {cached['retrieved']}")
        return path, cached["retrieved"]

    raise FetchError(f"Could not fetch {source_id!r} from {url}: {last_error}")


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV, tolerating the encodings publishers actually ship.

    Microsoft's diffusion CSV is latin-1 with stray high bytes; Epoch's are UTF-8.
    Guessing wrong throws a UnicodeDecodeError halfway through a CI run, so try in
    order rather than assuming.
    """
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return list(csv.DictReader(io.StringIO(text)))
    raise ValueError(f"Could not decode {path} with any known encoding")


def write_dataset(
    name: str,
    records: Iterable[dict[str, Any]],
    source_ids: list[str],
    unit: str | None = None,
    notes: str | None = None,
    retrieved: str | None = None,
) -> Path:
    """Write a processed dataset with its provenance envelope attached.

    Passes through guard() first — there is no code path that writes a dataset
    without a licence check.
    """
    guard(*source_ids)

    records = list(records)
    if not records:
        raise ValueError(f"Refusing to write empty dataset {name!r} — upstream probably changed")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    path = PROCESSED / f"{name}.json"
    payload = {
        "dataset": name,
        "generated": utcnow(),
        "retrieved": retrieved or utcnow(),
        "sources": source_ids,
        "unit": unit,
        "notes": notes,
        "count": len(records),
        "records": records,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)}: {len(records):,} records")
    return path


def _ext_for(fmt: str | None) -> str:
    return {"csv": ".csv", "json": ".json", "rss": ".xml", "atom": ".xml", "parquet": ".parquet"}.get(
        fmt or "", ".dat"
    )


def _read_meta(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _age_hours(iso: str) -> float:
    then = datetime.fromisoformat(iso)
    return (datetime.now(timezone.utc) - then).total_seconds() / 3600


def _self_check() -> None:
    """Runnable check on the logic that actually matters: the licence guard.

    If this ever passes for a blocked source, the site can silently ship data it
    has no right to publish.
    """
    guard("epoch-notable-models", "microsoft-ai-diffusion")  # permitted, must not raise

    for blocked in ("artificial-analysis", "stanford-ai-index"):
        try:
            guard(blocked)
        except LicenceError:
            pass
        else:
            raise AssertionError(f"guard() failed to block {blocked!r} — licence breach possible")

    try:
        guard("no-such-source")
    except KeyError:
        pass
    else:
        raise AssertionError("guard() accepted an unregistered source")

    # An empty dataset means upstream changed shape; writing it would silently
    # blank a chart rather than failing the build.
    try:
        write_dataset("_selfcheck", [], ["epoch-notable-models"])
    except ValueError:
        pass
    else:
        raise AssertionError("write_dataset accepted an empty dataset")

    print("common.py self-check passed")


if __name__ == "__main__":
    _self_check()
