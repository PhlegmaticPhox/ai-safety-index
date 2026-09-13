"""AI law and policy index, jurisdiction by jurisdiction.

Why this is written by hand rather than scraped: the two established policy
trackers, OECD.AI and IAPP, are protected by the EU sui generis database right
on top of copyright, and bulk-extracting either is the fastest route to a
letter. Reading the primary instruments and writing our own index avoids that
entirely, and the result is ours to license CC BY 4.0.

The selection rule is the same in every jurisdiction: an instrument belongs here
if it constrains or authorises AI systems in practice, whether or not it mentions
AI. An index of things with "AI" in the title would be four entries long for most
of these jurisdictions and would badly mislead anyone who read it. It is also the
rule that makes the index worth having, because the answer to "what law applies
to my model" is almost never an AI law.

The instrument lists live in policy_jurisdictions.py. This module holds the
vocabulary they are validated against and the checks.

WHAT THIS IS NOT. Not legal advice, not a compliance checklist, not exhaustive.
It is a map of where to start reading, with a link to the primary source for
every entry. Dates and statuses go stale; the review date is on the record.

    python etl/build_policy_index.py                # validate and write
    python etl/build_policy_index.py --self-check   # schema and coverage
    python etl/build_policy_index.py --check-links  # probe every citation
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import check_links, utcnow, write_dataset
from policy_jurisdictions import JURISDICTIONS

SOURCE = "policy-index"
REVIEWED = "2026-09"

# How binding a thing is. This is the distinction that matters most to a reader
# and the one most often blurred in press coverage: a voluntary standard and a
# statute are not the same kind of object, however similar their contents look.
FORCE = {
    "statute": "Act of Parliament. Binding on everyone it applies to.",
    "delegated": "Rules, regulations or codes made under an Act. Binding.",
    "agency-binding": "Binds government agencies only, not the wider market.",
    "regulator-guidance": (
        "How a regulator says it will apply existing law. Not law itself, but it "
        "tells you what enforcement will look like."
    ),
    "voluntary": "Guidance with no legal force. Compliance is a choice.",
    "proposal": "Proposed, consulted on, or before Parliament. Creates no duties yet.",
    "review": "An inquiry or review. Evidence and recommendations, not obligations.",
}

# Topic tags, so a reader can find the instruments that touch their problem
# without reading all of them.
TOPICS = [
    "privacy", "safety", "consumer", "discrimination", "copyright", "security",
    "health", "finance", "government use", "transparency", "children",
    "liability", "competition", "export control", "elections", "labelling",
]


def build_records() -> list[dict]:
    records = []
    for slug, jurisdiction in JURISDICTIONS.items():
        for instrument in jurisdiction["instruments"]:
            if instrument["force"] not in FORCE:
                raise ValueError(
                    f"{instrument['title']}: unknown force {instrument['force']!r}. "
                    f"Known: {sorted(FORCE)}"
                )
            unknown = set(instrument["topics"]) - set(TOPICS)
            if unknown:
                raise ValueError(f"{instrument['title']}: unknown topics {sorted(unknown)}")
            if not instrument["url"].startswith("https://"):
                raise ValueError(f"{instrument['title']}: citation must be an https URL")
            records.append(
                {
                    "jurisdiction": jurisdiction["name"],
                    "jurisdiction_slug": slug,
                    "jurisdiction_code": jurisdiction["code"],
                    "title": instrument["title"],
                    "force": instrument["force"],
                    "force_meaning": FORCE[instrument["force"]],
                    "year": instrument["year"],
                    "body": instrument["body"],
                    "topics": instrument["topics"],
                    "note": instrument["note"],
                    "url": instrument["url"],
                    "reviewed": REVIEWED,
                    "source_id": SOURCE,
                }
            )
    return records


def run(offline: bool = False) -> None:
    """Hand-written, so there is nothing to fetch and offline changes nothing."""
    records = build_records()
    write_dataset(
        "policy-index",
        records,
        source_ids=[SOURCE],
        unit=None,
        notes=(
            f"Our own index of instruments relevant to AI across {len(JURISDICTIONS)} "
            f"jurisdictions, reviewed {REVIEWED}. Each entry links to the primary source and "
            "is tagged by how binding it is, because a voluntary standard and an Act of "
            "Parliament are not the same kind of object however similar their contents look. "
            "Not legal advice, not a compliance checklist, and not exhaustive. Instruments "
            "that never mention AI are included where they apply to it, which is most of "
            "the list in most jurisdictions."
        ),
        retrieved=utcnow(),
    )


def _self_check() -> None:
    records = build_records()
    assert records, "policy index is empty"

    for record in records:
        assert record["note"], f"{record['title']} has no note"
        assert record["url"].startswith("https://"), record["title"]
        assert record["topics"], f"{record['title']} has no topics"
        assert 1900 < record["year"] <= 2100, f"{record['title']}: year {record['year']}"

    # An unknown force value must fail rather than render a blank label. This is
    # the field a reader relies on most, so a typo in it is worse than a missing
    # entry: it would silently present a voluntary standard as unlabelled.
    broken = dict(JURISDICTIONS)
    try:
        JURISDICTIONS["_test"] = {
            "name": "Test", "code": "TST", "summary": "",
            "instruments": [{
                "title": "T", "force": "mandatory-ish", "year": 2024, "body": "b",
                "topics": ["privacy"], "url": "https://example.com", "note": "n",
            }],
        }
        try:
            build_records()
        except ValueError:
            pass
        else:
            raise AssertionError("build_records accepted an unknown force value")

        JURISDICTIONS["_test"]["instruments"][0]["force"] = "statute"
        JURISDICTIONS["_test"]["instruments"][0]["topics"] = ["not-a-topic"]
        try:
            build_records()
        except ValueError:
            pass
        else:
            raise AssertionError("build_records accepted an unknown topic")

        JURISDICTIONS["_test"]["instruments"][0]["topics"] = ["privacy"]
        JURISDICTIONS["_test"]["instruments"][0]["url"] = "http://example.com"
        try:
            build_records()
        except ValueError:
            pass
        else:
            raise AssertionError("build_records accepted a non-https citation")
    finally:
        JURISDICTIONS.pop("_test", None)
        assert JURISDICTIONS == broken

    # The Australian entry is only honest if it includes law that does not
    # mention AI. An index of instruments with "AI" in the title would show four
    # things and mislead anyone who read it.
    titles = [r["title"] for r in records if r["jurisdiction_slug"] == "australia"]
    assert any("Privacy Act 1988" in t for t in titles), "Privacy Act missing"
    assert any("Copyright Act" in t for t in titles), "Copyright Act missing"
    # The claim the page makes is about binding law specifically, so that is what
    # is checked. Across the whole list roughly half name AI, which says nothing:
    # voluntary standards obviously name their own subject.
    australia = [r for r in records if r["jurisdiction_slug"] == "australia"]
    binding = [r for r in australia if r["force"] in ("statute", "delegated")]
    assert len(binding) >= 8, f"only {len(binding)} binding instruments listed for Australia"
    naming = [r for r in binding if "AI" in r["title"] or "Deepfake" in r["title"]]
    assert len(naming) <= 2, (
        f"{len(naming)} binding Australian instruments now name AI. If that is real the page "
        f"claim needs rewriting; if it is a coding slip, fix the entry."
    )

    forces = {r["force"] for r in records}
    assert "statute" in forces and "voluntary" in forces and "proposal" in forces, forces

    # Per jurisdiction. A jurisdiction with one or two entries is worse than no
    # jurisdiction: it reads as a complete picture and is not one.
    for slug, jurisdiction in JURISDICTIONS.items():
        assert jurisdiction["summary"], f"{slug} has no summary"
        assert len(jurisdiction["code"]) == 3, f"{slug}: code {jurisdiction['code']!r}"
        count = len(jurisdiction["instruments"])
        assert count >= 3, f"{slug} has only {count} instruments; that is not an index"

    # Duplicate titles inside one jurisdiction mean a copy-paste that left the
    # wrong link attached, which is the failure mode that looks most like data.
    seen = set()
    for record in records:
        key = (record["jurisdiction_slug"], record["title"])
        assert key not in seen, f"duplicate entry: {key}"
        seen.add(key)

    codes = {j["code"] for j in JURISDICTIONS.values()}
    assert len(codes) == len(JURISDICTIONS), "two jurisdictions share a code"

    print(
        f"build_policy_index self-check passed: {len(records)} instruments across "
        f"{len(JURISDICTIONS)} jurisdictions, {len(forces)} force levels"
    )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    elif "--check-links" in sys.argv:
        raise SystemExit(
            1 if check_links((r["title"][:40], r["url"]) for r in build_records()) else 0
        )
    else:
        _self_check()
        run()
