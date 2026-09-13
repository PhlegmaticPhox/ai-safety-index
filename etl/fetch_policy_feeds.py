"""Official AI policy sources: US Federal Register, GOV.UK, European Commission, NIST.

These four are deliberately the cleanest licences available anywhere: two US
Government public-domain sources, one Open Government Licence v3.0, and one
covered by the Commission's reuse decision. No press-publisher rights to argue
about, no paywall, no API key.

Legal posture, per docs/00-research-findings.md section 3.3: we store and show
headline, a short snippet, publisher, date and canonical link. Never full text,
never a hotlinked image. The snippet cap below is the mechanism, not a guideline.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from common import fetch, write_dataset

SNIPPET_CHARS = 200

FEDERAL_REGISTER = "us-federal-register"
GOV_UK = "gov-uk"
EC = "ec-digital-strategy"
NIST = "nist"

# Feeds that cover a whole department need topical filtering; a keyword-filtered
# feed does not. Matching on word boundaries so "aim" and "said" do not match "ai".
AI_PATTERN = re.compile(
    r"\b(artificial intelligence|machine learning|a\.?i\.?|algorithmic|"
    r"foundation model|large language model|llm|generative|deepfake|"
    r"automated decision|frontier model|compute threshold)\b",
    re.IGNORECASE,
)

XML_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _clean(text: str | None) -> str:
    """Strip markup, normalise dashes, collapse whitespace.

    Feeds ship HTML inside description. They also ship em and en dashes, which the
    house typographic rule forbids. These extracts are already truncated, so
    normalising a dash character to a hyphen changes presentation and not meaning;
    the canonical link next to every item is the unaltered original.
    """
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
        .replace("&mdash;", "-")
        .replace("&ndash;", "-")
        .replace(" - ", "-")
        .replace(" - ", "-")
    )
    return re.sub(r"\s+", " ", text).strip()


ELLIPSIS = "..."


def _snippet(text: str) -> str:
    """Cap the extract at SNIPPET_CHARS including the ellipsis.

    This is the copyright-safety mechanism from docs/00-research-findings.md, so
    the cap is on the FINAL string. Appending the ellipsis after truncating to the
    cap overshoots it, which is exactly the bug this replaced.
    """
    text = _clean(text)
    if len(text) <= SNIPPET_CHARS:
        return text
    budget = SNIPPET_CHARS - len(ELLIPSIS)
    cut = text[:budget].rsplit(" ", 1)[0]
    return cut + ELLIPSIS


def _relevant(*fields: str) -> bool:
    return bool(AI_PATTERN.search(" ".join(f for f in fields if f)))


def fetch_federal_register(offline: bool) -> list[dict]:
    query = urllib.parse.urlencode(
        {
            "conditions[term]": "artificial intelligence",
            "order": "newest",
            "per_page": "60",
            "fields[]": "title",
        },
        doseq=True,
    )
    # fields[] repeats; urlencode above only carries one, so build the rest by hand.
    extra = "".join(
        f"&fields[]={f}"
        for f in ("publication_date", "html_url", "agencies", "type", "abstract")
    )
    url = f"https://www.federalregister.gov/api/v1/documents.json?{query}{extra}"

    path, retrieved = fetch(FEDERAL_REGISTER, url=url, offline=offline)
    payload = json.loads(path.read_text(encoding="utf-8"))

    records = []
    for item in payload.get("results", []):
        title = _clean(item.get("title"))
        abstract = _clean(item.get("abstract"))
        # Full-text search matches documents that merely mention AI in passing.
        if not _relevant(title, abstract):
            continue
        agencies = [a.get("name", "") for a in item.get("agencies", []) if a.get("name")]
        records.append(
            {
                "title": title,
                "snippet": _snippet(abstract),
                "url": item.get("html_url", ""),
                "date": item.get("publication_date", ""),
                "publisher": agencies[0] if agencies else "US Federal Register",
                "jurisdiction": "United States",
                "kind": _clean(item.get("type")),
                "source_id": FEDERAL_REGISTER,
            }
        )
    return records


def _parse_feed(xml_text: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into a common shape. Both appear across our sources."""
    root = ET.fromstring(xml_text)
    items = []

    for item in root.findall(".//item"):  # RSS 2.0
        items.append(
            {
                "title": _clean(item.findtext("title")),
                "summary": item.findtext("description") or "",
                "url": _clean(item.findtext("link")),
                "date": _clean(item.findtext("pubDate")),
            }
        )

    for entry in root.findall("atom:entry", XML_NS):  # Atom
        link = entry.find("atom:link", XML_NS)
        items.append(
            {
                "title": _clean(entry.findtext("atom:title", namespaces=XML_NS)),
                "summary": entry.findtext("atom:summary", namespaces=XML_NS) or "",
                "url": link.get("href", "") if link is not None else "",
                "date": _clean(entry.findtext("atom:updated", namespaces=XML_NS)),
            }
        )

    return items


def _normalise_date(raw: str) -> str:
    """Feeds use RFC 822, ISO 8601, or something close. Return YYYY-MM-DD or ''."""
    raw = raw.strip()
    if not raw:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%d %b %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def fetch_xml_feed(
    source_id: str, url: str | None, jurisdiction: str, publisher: str,
    offline: bool, needs_filter: bool,
) -> list[dict]:
    path, _ = fetch(source_id, url=url, offline=offline)
    try:
        items = _parse_feed(path.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        print(f"  WARNING {source_id}: feed did not parse ({exc}); skipping")
        return []

    records = []
    for item in items:
        title = item["title"]
        summary = _clean(item["summary"])
        if not title or not item["url"]:
            continue
        if needs_filter and not _relevant(title, summary):
            continue
        records.append(
            {
                "title": title,
                "snippet": _snippet(summary),
                "url": item["url"],
                "date": _normalise_date(item["date"]),
                "publisher": publisher,
                "jurisdiction": jurisdiction,
                "kind": "",
                "source_id": source_id,
            }
        )
    return records


def run(offline: bool = False) -> None:
    records: list[dict] = []

    collectors = [
        ("Federal Register", lambda: fetch_federal_register(offline)),
        (
            "GOV.UK",
            lambda: fetch_xml_feed(
                GOV_UK,
                "https://www.gov.uk/search/news-and-communications.atom"
                "?keywords=artificial+intelligence",
                # The keywords parameter ranks rather than filters: unfiltered it
                # returned police pensions, heating oil and vape imports. Filter
                # locally regardless of what the query promises.
                "United Kingdom", "GOV.UK", offline, needs_filter=True,
            ),
        ),
        (
            "European Commission",
            lambda: fetch_xml_feed(
                EC, None, "European Union", "European Commission",
                offline, needs_filter=True,
            ),
        ),
        (
            "NIST",
            lambda: fetch_xml_feed(
                NIST, None, "United States", "NIST", offline, needs_filter=True,
            ),
        ),
    ]

    for label, collect in collectors:
        try:
            got = collect()
            print(f"  {label}: {len(got)} relevant items")
            records.extend(got)
        except Exception as exc:  # noqa: BLE001 - one dead feed must not kill the feed
            print(f"  WARNING {label} failed: {type(exc).__name__}: {exc}")

    if not records:
        raise RuntimeError("every policy feed failed; refusing to write an empty feed")

    # Same story often appears in two feeds. Dedupe on URL, keep first seen.
    seen: set[str] = set()
    deduped = []
    for record in sorted(records, key=lambda r: r["date"], reverse=True):
        if record["url"] in seen:
            continue
        seen.add(record["url"])
        deduped.append(record)

    deduped = deduped[:60]

    write_dataset(
        "policy-feed",
        deduped,
        source_ids=sorted({r["source_id"] for r in deduped}),
        unit=None,
        notes=(
            f"Headline, a short extract of at most {SNIPPET_CHARS} characters, and a link "
            "back to the official source. We do not reproduce full text. Departmental "
            "communications are political statements about policy, not neutral "
            "descriptions of it."
        ),
        retrieved=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def _self_check() -> None:
    """Guard the two rules that actually matter here.

    The snippet cap is a copyright-safety mechanism and the relevance filter is
    what keeps an AI policy feed from filling with vape-import enforcement notices.
    Both have already failed once in this file.
    """
    long_text = "word " * 200
    for sample in (long_text, "short", "", "x" * 500, "a b c " * 90):
        assert len(_snippet(sample)) <= SNIPPET_CHARS, (
            f"snippet exceeded {SNIPPET_CHARS}: got {len(_snippet(sample))}"
        )

    # Real headlines this filter previously let through, from the GOV.UK feed.
    for noise in (
        "Circular 012/2026: CPI and the Police Pension Scheme 2015",
        "Heating oil suppliers: using fair terms and conditions",
        "Glasgow directors banned after importing more than 350,000 vapes",
        "He said the plan would aim to help",  # must not match on "said"/"aim"
    ):
        assert not _relevant(noise), f"filter wrongly accepted: {noise}"

    for signal in (
        "Guidance on artificial intelligence in public services",
        "Commission adopts rules for general-purpose AI models",
        "NIST releases machine learning evaluation framework",
        "Consultation on automated decision making in hiring",
    ):
        assert _relevant(signal), f"filter wrongly rejected: {signal}"

    assert _normalise_date("2026-09-11T10:00:00Z") == "2026-09-11"
    assert _normalise_date("Thu, 11 Sep 2026 10:00:00 +0000") == "2026-09-11"
    assert _normalise_date("nonsense") == ""

    for dashed in ("a - b", "a - b", "x&mdash;y"):
        assert " - " not in _clean(dashed) and " - " not in _clean(dashed), (
            f"dash normalisation failed on {dashed!r}"
        )

    print("fetch_policy_feeds self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        run(offline="--offline" in sys.argv)
