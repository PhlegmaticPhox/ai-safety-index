"""Shared ETL plumbing: source registry, cached fetch, licence guard, output envelope.

Design rule for the whole pipeline: a processed record never travels without a
`source_id`, and a dataset is never written without passing `guard()`. That makes
attribution a join rather than a habit, and makes an accidental licence breach a
build failure instead of a lawyer's letter.

Stdlib only, deliberately - this runs in CI and should have nothing to break.
"""

from __future__ import annotations

import csv
import io
import json
import ssl
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

# Identify ourselves honestly. A publisher who wants to block us should be able to,
# and should be able to reach a human without guessing.
#
# This used to point at the GitHub repository and say "contact via repo issues".
# That repository is now private, so the URL would have 404'd and the contact
# route named in it would not have existed - which is worse than no user agent at
# all, because it looks like an honest identifier while being a dead end. It now
# points at the site itself and carries the same address the corrections page
# publishes, which is an alias on our own domain rather than anyone's mailbox.
USER_AGENT = (
    "AISafetyTrackerBot/0.1 "
    "(+https://aisafetytracker.org/; data pipeline; "
    "contact corrections@aisafetytracker.org)"
)

# Licence states that must never reach a rendered chart.
BLOCKED_REDISTRIBUTION = {"prohibited", "no-derivatives"}

# Ceiling on a single fetched body. The largest source we actually pull is Epoch's
# benchmarks CSV at about 3.7MB, so this is roughly seventeen times the real high
# water mark: generous enough that a publisher growing their dataset does not trip
# it, small enough that a compromised source cannot exhaust the CI runner by
# streaming forever. Without a cap, response.read() has no upper bound at all.
MAX_BYTES = 64 * 1024 * 1024

# What each declared format is allowed to come back as. Observed values from the
# live sources, not guesses: Epoch serves text/csv, raw.githubusercontent serves
# application/octet-stream for the same kind of file, the Commission and NIST
# serve application/rss+xml, the Incident Database and Canada serve a bare
# application/xml, and gov.uk serves application/atom+xml.
ALLOWED_CONTENT_TYPES = {
    "csv": {"text/csv", "application/csv", "text/plain", "application/octet-stream"},
    "json": {"application/json", "text/json", "application/octet-stream"},
    "rss": {"application/rss+xml", "application/xml", "text/xml", "application/rdf+xml"},
    "atom": {"application/atom+xml", "application/xml", "text/xml"},
}

# Types that are never a legitimate answer for a data endpoint. This is the check
# that earns its place: docs/00-research-findings.md records two Epoch CSV URLs
# that returned HTML stubs, which parse to zero rows and blank a chart rather than
# failing. A publisher moving a dataset behind a login or an interstitial looks
# exactly like this.
REFUSED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


def _ssl_context() -> ssl.SSLContext:
    """Verify TLS against certifi's bundle when it is installed.

    Python on Windows snapshots whatever roots the OS has cached, which can be
    missing or stale: nist.gov fails verification here with "certificate has
    expired" while curl fetches it fine, because curl ships its own bundle. Linux
    CI would not hit that, so without this the pipeline behaves differently on the
    two machines and a source silently drops out locally.

    Verification is never disabled. If certifi is absent we fall back to the system
    default, which still verifies; some hosts may simply be unreachable.
    """
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


SSL_CONTEXT = _ssl_context()


class LicenceError(RuntimeError):
    """Raised when a dataset would be published in breach of its source licence."""


class FetchError(RuntimeError):
    """Raised when a source could not be retrieved and no cached copy exists."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# Written as escape sequences on purpose, never as the literal characters.
# Spelling them literally once let a project-wide dash sweep rewrite the
# normalisation line AND the assertion guarding it into a matching pair that
# passed while doing nothing at all.
EM_DASH = "—"
EN_DASH = "–"


def normalise_dashes(text: str) -> str:
    """Replace em and en dashes with the plain hyphen.

    House typographic rule: the permitted dash on this site is the hyphen. That
    applies to data as much as to prose, because data is what gets rendered. An
    en dash inside an Epoch organisation name reached a chart tooltip on the
    capability page and was only caught by scanning the built HTML.

    This changes presentation and not meaning, and every figure links to the
    unaltered original one click away.
    """
    return text.replace(EM_DASH, "-").replace(EN_DASH, "-")


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
            with urllib.request.urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
                # Read one byte past the cap so an oversized body is detectable
                # without ever holding the whole of it. Nothing is written to
                # disk until both checks below have passed.
                body = response.read(MAX_BYTES + 1)
                content_type = response.headers.get_content_type()
            if len(body) > MAX_BYTES:
                raise FetchError(
                    f"{source_id!r} returned more than {MAX_BYTES:,} bytes; refusing it. "
                    f"Either the source grew a great deal or it is not what it was."
                )
            _check_content_type(source_id, source.get("format"), content_type)
            path.write_bytes(body)
            retrieved = utcnow()
            meta_path.write_text(
                json.dumps({"url": url, "retrieved": retrieved, "bytes": len(body)}, indent=2),
                encoding="utf-8",
            )
            print(f"  fetched {source_id}: {len(body):,} bytes")
            return path, retrieved
        except FetchError as exc:
            # A rejected size or content type is a decision, not a hiccup: asking
            # the same server the same question again will get the same answer.
            # Stop retrying and fall through to the cached copy below, which is
            # the whole point - a stale dataset with a loud warning beats a
            # chart that silently empties.
            last_error = exc
            print(f"  WARNING {source_id}: {exc}")
            break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)

    if cached and path.exists():
        print(f"  WARNING {source_id}: fetch failed ({last_error}); using cached copy "
              f"from {cached['retrieved']}")
        return path, cached["retrieved"]

    raise FetchError(f"Could not fetch {source_id!r} from {url}: {last_error}")


def _check_content_type(source_id: str, fmt: str | None, received: str) -> None:
    """Refuse a response whose type cannot be what the source declares it is.

    Deliberately not a strict allowlist that rejects everything unfamiliar. Real
    publishers serve the same file under several types - the Microsoft CSV comes
    back as application/octet-stream from raw.githubusercontent, and the Incident
    Database serves RSS as a bare application/xml - and a check that breaks the
    pipeline on a harmless header variation would be turned off within a month.

    So: a known-good type passes silently, a type that is definitely wrong is
    refused, and anything else passes with a note. The refusal list is short and
    specific because it encodes a failure that has actually happened here - a
    data endpoint answering with an HTML page, which then parses to zero rows and
    blanks a chart instead of failing.
    """
    if not fmt or not received:
        return
    if received in REFUSED_CONTENT_TYPES:
        raise FetchError(
            f"{source_id!r} declares format={fmt!r} but the server returned "
            f"{received!r}. A data URL answering with a web page usually means it "
            f"moved, or is now behind a login or an interstitial."
        )
    allowed = ALLOWED_CONTENT_TYPES.get(fmt)
    if allowed and received not in allowed:
        print(
            f"  note {source_id}: content type {received!r} is not one of the "
            f"expected types for format={fmt!r}; accepting it anyway"
        )


def read_csv(path: Path, encoding: str | None = None) -> list[dict[str, str]]:
    """Read a CSV, tolerating the encodings publishers actually ship.

    Epoch's files are UTF-8. Microsoft's diffusion CSV is Mac Roman, which is the
    reason for the `encoding` argument: a fallback chain cannot tell Mac Roman
    from cp1252, because every byte is valid in both. It decoded happily and
    silently produced "TYrkiye" for "Turkiye" until the map join surfaced it. A
    guess that succeeds wrongly is worse than one that fails.

    So: pass `encoding` explicitly whenever the publisher's encoding is known.
    The chain stays for sources where it genuinely is a guess, and it is ordered
    so a real UTF-8 file is never mistaken for anything else.
    """
    raw = path.read_bytes()
    candidates = (encoding,) if encoding else ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    for candidate in candidates:
        try:
            text = raw.decode(candidate)
        except UnicodeDecodeError:
            continue
        return list(csv.DictReader(io.StringIO(text)))
    raise ValueError(f"Could not decode {path} as {', '.join(candidates)}")


def write_dataset(
    name: str,
    records: Iterable[dict[str, Any]],
    source_ids: list[str],
    unit: str | None = None,
    notes: str | None = None,
    retrieved: str | None = None,
) -> Path:
    """Write a processed dataset with its provenance envelope attached.

    Passes through guard() first - there is no code path that writes a dataset
    without a licence check.
    """
    guard(*source_ids)

    records = list(records)
    if not records:
        raise ValueError(f"Refusing to write empty dataset {name!r} - upstream probably changed")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    path = PROCESSED / f"{name}.json"

    # Skip the write when the records are byte-identical to what is already on
    # disk. The generated and retrieved stamps move on every run by definition,
    # so without this a daily scheduled refresh commits timestamp churn forever
    # and the data history becomes unreviewable. A commit should mean the data
    # actually changed. Last-checked time lives in _status.json instead.
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = None
        if (
            existing
            and existing.get("records") == records
            and existing.get("sources") == source_ids
            and existing.get("unit") == unit
            and existing.get("notes") == notes
        ):
            print(f"  {path.relative_to(ROOT)}: unchanged ({len(records):,} records)")
            return path

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


def probe(url: str) -> tuple[str, object]:
    """Classify a citation URL as ok, blocked, unreachable or DEAD.

    Used by the hand-coded indexes to check that every instrument they cite
    still resolves. A citation that 404s is worse than no citation, because it
    looks like evidence.

    The distinction between the four verdicts matters, and the first version of
    this got it wrong by collapsing them. Government sites refuse HEAD, refuse
    anything that is not a browser, sit behind bot walls, and time out. None of
    that means the citation is wrong, and treating it as wrong would push us to
    replace good primary links with worse ones. Only a definite 404 or 410 is
    evidence that a link is bad.

    We do not spoof a browser to get past a bot wall. A publisher blocking
    robots is entitled to; the answer is to report "blocked", not to lie about
    who is asking.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en",
    }
    last: tuple[str, object] = ("unreachable", "unknown")
    for method in ("HEAD", "GET"):
        try:
            request = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(request, timeout=40, context=SSL_CONTEXT) as response:
                # urlopen follows redirects, so a 2xx here is a resolved page.
                return "ok", response.status
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                return "DEAD", exc.code
            last = ("blocked", exc.code)
        except Exception as exc:  # noqa: BLE001
            last = ("unreachable", type(exc).__name__)
    return last


def check_links(entries: Iterable[tuple[str, str]]) -> int:
    """Probe (label, url) pairs. Returns the count of definite 404s.

    Blocked and unreachable are printed but do not fail, because a run that
    fails on someone else's bot wall trains everyone to ignore it.
    """
    seen: set[str] = set()
    buckets: dict[str, list[tuple[str, str, object]]] = {
        "blocked": [], "unreachable": [], "DEAD": []
    }

    for label, url in entries:
        if url in seen:
            continue
        seen.add(url)
        verdict, detail = probe(url)
        print(f"  {verdict:<11} {str(detail):<20} {label}  {url}")
        if verdict != "ok":
            buckets[verdict].append((label, url, detail))

    ok = len(seen) - sum(len(v) for v in buckets.values())
    print(
        f"\n{len(seen)} unique URLs: {ok} ok, {len(buckets['blocked'])} blocked, "
        f"{len(buckets['unreachable'])} unreachable, {len(buckets['DEAD'])} dead"
    )
    for state in ("DEAD", "blocked", "unreachable"):
        for label, url, detail in buckets[state]:
            print(f"  {state}: {detail}  {label}  {url}")
    return len(buckets["DEAD"])


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
            raise AssertionError(f"guard() failed to block {blocked!r} - licence breach possible")

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

    # Dash normalisation, against the real string that got through: an Epoch
    # organisation name carrying an en dash, which reached a chart tooltip.
    got = normalise_dashes("Universite de Technologie de Compiegne – CNRS")
    assert got == "Universite de Technologie de Compiegne - CNRS", got
    assert normalise_dashes("a — b") == "a - b"
    assert EM_DASH not in normalise_dashes(f"x{EM_DASH}y{EN_DASH}z")
    assert EN_DASH not in normalise_dashes(f"x{EM_DASH}y{EN_DASH}z")
    # A hyphen must survive untouched, or every hyphenated name loses its hyphen.
    assert normalise_dashes("fine-tuning") == "fine-tuning"

    # The response cap has to sit above every real source with room to spare, or
    # the first time a publisher adds a year of data the pipeline stops.
    assert MAX_BYTES >= 64 * 1024 * 1024, "cap lowered below the documented value"
    largest = max(
        (p.stat().st_size for p in RAW.glob("*") if p.suffix != ".json"), default=0
    )
    if largest:
        assert largest < MAX_BYTES / 4, (
            f"largest cached raw file is {largest:,} bytes, within 4x of the "
            f"{MAX_BYTES:,} byte cap. Raise the cap before a fetch starts failing."
        )

    # Content types. Every type below was observed coming back from the real
    # endpoint; if one of these starts failing, the source changed, not the check.
    for fmt, received in (
        ("csv", "text/csv"),                      # epoch.ai
        ("csv", "application/octet-stream"),      # raw.githubusercontent.com
        ("json", "application/json"),             # openalex, federalregister
        ("rss", "application/rss+xml"),           # nist, arxiv, ec
        ("rss", "application/xml"),               # incidentdatabase
        ("atom", "application/atom+xml"),         # gov.uk
        ("atom", "application/xml"),              # canada
    ):
        _check_content_type("selfcheck", fmt, received)  # must not raise

    # An unknown type is a note, not a failure: publishers vary and a brittle
    # check gets disabled rather than fixed.
    _check_content_type("selfcheck", "csv", "application/vnd.ms-excel")
    # A missing header, or a format we do not declare, is not a reason to refuse.
    _check_content_type("selfcheck", "csv", "")
    _check_content_type("selfcheck", None, "text/html")

    # But a data endpoint answering with a web page is refused. This is the case
    # that has actually happened: two Epoch CSV URLs returned HTML stubs.
    for fmt in ("csv", "json", "rss", "atom"):
        try:
            _check_content_type("selfcheck", fmt, "text/html")
        except FetchError:
            pass
        else:
            raise AssertionError(f"HTML accepted for format={fmt!r}; the stub bug can recur")

    # Idempotence: writing the same records twice must leave the file untouched,
    # or the daily refresh commits timestamp churn forever.
    probe = PROCESSED / "_selfcheck.json"
    try:
        rows = [{"a": 1, "source_id": "epoch-notable-models"}]
        write_dataset("_selfcheck", rows, ["epoch-notable-models"])
        first = probe.read_bytes()
        time.sleep(1.1)  # guarantee a different second in the timestamp
        write_dataset("_selfcheck", rows, ["epoch-notable-models"])
        if probe.read_bytes() != first:
            raise AssertionError("write_dataset rewrote an unchanged dataset")

        write_dataset("_selfcheck", [{"a": 2, "source_id": "epoch-notable-models"}],
                      ["epoch-notable-models"])
        if probe.read_bytes() == first:
            raise AssertionError("write_dataset failed to write changed records")
    finally:
        probe.unlink(missing_ok=True)

    print("common.py self-check passed")


if __name__ == "__main__":
    _self_check()
