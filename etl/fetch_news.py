"""The news feed: government publications, research preprints and reported incidents.

Sources are chosen for licence cleanliness before anything else. Two US
Government public-domain feeds, one Open Government Licence v3.0, one covered by
the Commission's reuse decision, one Canadian OGL, two arXiv feeds whose metadata
is CC0, and the AI Incident Database under ODbL. No press-publisher rights to
argue about, no paywall, no API key. That is why there is no Reuters or Wired
here: their headlines are not ours to republish, however much they would improve
the feed.

Legal posture, per docs/00-research-findings.md section 3.3: we store and show
headline, a short snippet, publisher, date and canonical link. Never full text,
never a hotlinked image. The snippet cap below is the mechanism, not a guideline.
ODbL adds one more rule for the incident feed: displaying headlines is display,
publishing a derived database dump is not, and we do not.

Categories are assigned by keyword rule, and every item records which terms
matched, so a reader can see why something was filed where it was and disagree
with it. An unexplained classifier on a site about provenance would be a hole in
the argument.
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from common import PROCESSED, fetch, write_dataset

SNIPPET_CHARS = 200

FEDERAL_REGISTER = "us-federal-register"
GOV_UK = "gov-uk"
EC = "ec-digital-strategy"
NIST = "nist"
CANADA = "canada-news"
ARXIV_AI = "arxiv-cs-ai"
ARXIV_CY = "arxiv-cs-cy"
INCIDENTS = "ai-incident-database"

# arXiv publishes hundreds of papers a day. Uncapped it would bury every
# government publication in the feed, which is the opposite of what this is for.
PER_SOURCE_CAP = {ARXIV_AI: 18, ARXIV_CY: 18, INCIDENTS: 12}
DEFAULT_CAP = 40
TOTAL_CAP = 160

# What kind of thing an item is. Kept separate from category, because "a
# preprint about alignment" and "a regulation about alignment" are different
# objects and a reader should never have to guess which one they are looking at.
KIND_BY_SOURCE = {
    ARXIV_AI: "Research preprint",
    ARXIV_CY: "Research preprint",
    INCIDENTS: "Reported incident",
}
DEFAULT_KIND = "Government publication"

# Categories, as keyword rules. Deliberately readable rather than clever: every
# term here is one a person can look at and argue with, and the matched terms
# travel with each record so the classification is auditable rather than
# asserted. Items can carry several categories; items carrying none are filed
# under "general", which is an honest "this is about AI and nothing narrower".
#
# A trailing asterisk marks a PREFIX term, matching any ending. Everything else
# is bounded at both ends. The distinction is load-bearing: the first version
# bounded only the front, so "act" matched "action", "impact" and "interact",
# and almost every item in the feed came out filed under policy. Bare "act" is
# gone entirely now; named acts are caught by "ai act" and by the other terms.
CATEGORY_TERMS = {
    "safety": [
        "safety", "harm*", "risk*", "misuse", "red team", "red-team", "jailbreak*",
        "adversarial", "robustness", "incident*", "abuse", "catastrophic",
        "dangerous capabilit*", "bioweapon*", "cyberattack*", "guardrail*",
        "safety institute", "security institute", "evaluation*", "eval",
        "systemic risk", "safeguard*", "threat*", "vulnerabilit*",
    ],
    "alignment": [
        "alignment", "aligned", "misalign*", "rlhf", "reward model*",
        "reward hacking", "interpretab*", "mechanistic", "scalable oversight",
        "specification gaming", "deceptive", "deception", "sycophan*",
        "constitutional ai", "preference learning", "value learning",
        "corrigib*", "activation steering", "chain of thought monitoring",
    ],
    "policy": [
        "ai act", "bill", "legislation", "legislative", "statute", "statutory",
        "regulation*", "regulatory", "consultation", "executive order",
        "directive", "rulemaking", "proposed rule", "parliament*", "congress",
        "senate", "treaty", "enforcement", "sanction*", "moratorium", "mandate*",
        "act 20", "designat*", "court", "lawsuit", "verdict", "judgment",
        "judgement", "ruling", "penalt*", "prohibit*",
    ],
    "governance": [
        "governance", "standard*", "framework*", "audit*", "assurance",
        "compliance", "certification", "accountability", "transparency",
        "oversight", "procurement", "risk management", "conformity",
        "code of practice", "guideline*", "principle*", "supervis*",
        "authority", "authorities", "institute", "institutes", "disclosure*",
        "strategy", "strategies",
    ],
    "progress": [
        "benchmark*", "state of the art", "frontier", "training", "pretrain*",
        "compute", "scaling", "parameters", "model release", "open weights",
        "capabilit*", "outperform*", "accuracy", "reasoning", "multimodal",
        "agentic", "fine-tun*", "distillation", "inference", "throughput",
    ],
}


def _term_pattern(term: str) -> str:
    """One term as a regex fragment, honouring the prefix marker."""
    if term.endswith("*"):
        return re.escape(term[:-1]) + r"\w*"
    return re.escape(term) + r"\b"


# Built once. Longest first, so "safety institute" wins over "safety" and the
# matched term shown to the reader is the specific one.
CATEGORY_PATTERNS = {
    name: re.compile(
        r"\b(" + "|".join(_term_pattern(t) for t in sorted(terms, key=len, reverse=True)) + r")",
        re.IGNORECASE,
    )
    for name, terms in CATEGORY_TERMS.items()
}

CATEGORY_ORDER = ["safety", "alignment", "policy", "governance", "progress", "general"]

CATEGORY_LABELS = {
    "safety": "AI Safety",
    "alignment": "AI Alignment",
    "policy": "AI Policy",
    "governance": "AI Governance",
    "progress": "AI Progress",
    "general": "AI",
}

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
    # Unescape and strip twice: some feeds double-encode their markup, and a single
    # pass leaks literal "<span>" text into the snippet.
    for _ in range(2):
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
    # Written as escapes on purpose. Spelling these as literal characters once let a
    # project-wide dash sweep rewrite this line AND its self-check into a matching
    # pair that passed while doing nothing.
    text = text.replace("—", "-").replace("–", "-")
    # Invisible characters survive a \s+ collapse, because Python does not treat
    # a zero-width space as whitespace. Feeds carry them: one arrived with a
    # U+200B thirteen characters into the extract, where it did nothing visible
    # and quietly counted against the 200-character copyright cap. Strip every
    # format character and the byte-order mark.
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf" and ch != "﻿")
    return re.sub(r"\s+", " ", text).strip()


# Drupal-backed feeds, the Commission's among them, put the article title, an author
# placeholder and a formatted timestamp in front of the body text. The live feed
# also leaks editor usernames ("lobacni 11 November 2026") and photo credits
# ("(c) Marcus Jacobi") into the summary, neither of which is content.
MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
)

BOILERPLATE = [
    re.compile(r"Anonymous\s*\(not verified\)", re.IGNORECASE),
    re.compile(r"\b\w{3},\s*\d{2}/\d{2}/\d{4}\s*-\s*\d{1,2}:\d{2}\b"),
    re.compile(r"\bSubmitted by\b.*?\bon\b", re.IGNORECASE),
    # An editor username immediately followed by a publication date.
    re.compile(rf"^\s*[a-z][a-z0-9._-]{{2,20}}\s+\d{{1,2}}\s+(?:{MONTHS})\s+\d{{4}}\b"),
    # Photo credit, to the end of the credited name.
    re.compile(r"(?:©|\(c\))\s*[\w.'-]+(?:\s+[\w.'-]+){0,3}", re.IGNORECASE),
]

# Bare URLs inside a summary. The incident feed appends its own canonical link to
# every description, which then appeared in the extract AND, worse, in the text
# the classifier reads: the host name "incidentdatabase" matched the "incident"
# rule and filed court filings under safety on the strength of their own URL.
# The link already has a home next to the headline.
URL_IN_TEXT = re.compile(r"\(?\bhttps?://\S+\)?", re.IGNORECASE)


def _strip_preamble(summary: str, title: str) -> str:
    """Drop the repeated title, feed furniture and bare URLs from a summary."""
    text = _clean(summary)
    if title and text.lower().startswith(title.lower()):
        text = text[len(title):]
    for pattern in BOILERPLATE:
        text = pattern.sub(" ", text)
    text = URL_IN_TEXT.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip(" .,-")


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


# Function words that are common in English and, importantly, are NOT words in
# the languages this feed actually collides with. The obvious candidates had to
# go: "of", "is", "was" and "over" are all ordinary Dutch words, and including
# them made the screen pass Dutch articles about deepfakes.
ENGLISH_MARKERS = re.compile(
    r"\b(the|to|and|for|with|from|after|that|has|have|been|by|its|are|were|"
    r"will|than|about|which|their|but|not|into|under|against|between|through)\b",
    re.IGNORECASE,
)


def _looks_english(text: str) -> bool:
    """Cheap language screen for the incident feed.

    The AI Incident Database aggregates press coverage worldwide, so a plain
    relevance filter happily admits Dutch reporting on deepfakes: correct on
    topic, useless on an English-language site that cannot summarise it
    responsibly. Counting distinct English-only function words is crude, and
    crude is proportionate. Applied ONLY to the incident feed; every other source
    here publishes in English by construction.

    The threshold scales with length because headlines legitimately drop function
    words. "US judge upholds verdict against Tesla over fatal Autopilot crash"
    carries exactly one, and a flat threshold of two rejected it.
    """
    markers = {m.group(1).lower() for m in ENGLISH_MARKERS.finditer(text)}
    return len(markers) >= (2 if len(text) > 120 else 1)


# A named statute, as capitalised words ending in "Act". Keyword lists cannot
# catch these: bare "act" matched "action" and "impact" and had to go, which then
# lost "Digital Services Act" and "Online Safety Act" entirely. This is the rule
# that puts them back, and it is case sensitive on purpose.
NAMED_ACT = re.compile(r"\b((?:[A-Z][\w&-]*\s+){1,4}Act)\b")


def categorise(title: str, snippet: str) -> tuple[list[str], dict[str, list[str]]]:
    """Assign categories by keyword, and record which terms matched.

    Returns (categories, matched terms per category). The matched terms are shown
    on the site next to the category chip. A classifier nobody can inspect has no
    place on a page whose whole argument is that you can check the source.

    Matching runs over the headline and the extract only, never full text, both
    because that is all we hold and because it keeps the rule the reader can
    verify identical to the rule we ran.
    """
    haystack = f"{title} {snippet}"
    matched: dict[str, list[str]] = {}
    for name, pattern in CATEGORY_PATTERNS.items():
        hits = sorted({m.group(1).lower() for m in pattern.finditer(haystack)})
        if hits:
            matched[name] = hits

    named = sorted({m.group(1) for m in NAMED_ACT.finditer(haystack)})
    if named:
        matched["policy"] = sorted(set(matched.get("policy", [])) | set(named))

    categories = [c for c in CATEGORY_ORDER if c in matched]
    if not categories:
        categories = ["general"]
    return categories, matched


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
                "doc_type": _clean(item.get("type")),
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
        # Strip the repeated title, author placeholder and timestamp that
        # Drupal-backed feeds put in front of the body.
        summary = _strip_preamble(item["summary"], title)
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
                "doc_type": "",
                "source_id": source_id,
            }
        )
    return records


# arXiv puts its own identifier and an announce-type marker in front of every
# abstract, and repeats the abstract label. None of that is content.
ARXIV_PREAMBLE = re.compile(
    r"^\s*arXiv:\S+\s*(Announce Type:\s*\S+)?\s*(Abstract:)?\s*", re.IGNORECASE
)


def fetch_arxiv(source_id: str, offline: bool) -> list[dict]:
    """New submissions in one arXiv category.

    The feed carries the current day's announcements only, and arXiv does not
    announce at weekends, so a Saturday fetch legitimately returns zero items.
    That is not a failure and must not raise: the rolling merge in run() is what
    keeps the feed populated across a weekend.
    """
    path, _ = fetch(source_id, offline=offline, max_age_hours=6.0)
    try:
        items = _parse_feed(path.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        print(f"  WARNING {source_id}: feed did not parse ({exc}); skipping")
        return []

    category = "cs.AI" if source_id == ARXIV_AI else "cs.CY"
    records = []
    for item in items:
        title = item["title"]
        if not title or not item["url"]:
            continue
        summary = ARXIV_PREAMBLE.sub("", _clean(item["summary"]))
        if not _relevant(title, summary):
            continue
        records.append(
            {
                "title": title,
                "snippet": _snippet(summary),
                "url": item["url"],
                "date": _normalise_date(item["date"]),
                "publisher": f"arXiv {category}",
                "jurisdiction": "Research",
                "source_id": source_id,
            }
        )
    return records


def fetch_incidents(offline: bool) -> list[dict]:
    """Recently reported AI incidents, as headlines with a link back.

    ODbL share-alike governs the database. Showing headlines and linking to the
    record is display; republishing a derived dump is the thing the licence puts
    conditions on, and this pipeline has no code path that does it.
    """
    path, _ = fetch(INCIDENTS, offline=offline)
    try:
        items = _parse_feed(path.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        print(f"  WARNING {INCIDENTS}: feed did not parse ({exc}); skipping")
        return []

    records = []
    for item in items:
        if not item["title"] or not item["url"]:
            continue
        snippet = _snippet(_strip_preamble(item["summary"], item["title"]))
        # The database aggregates press coverage in many languages and files a
        # lot of it under headlines that say nothing about AI on their own
        # ("Paint it black" was in the first run). The same relevance filter the
        # departmental feeds get applies here, which also has the side effect of
        # dropping non-English coverage this English-language site cannot
        # summarise responsibly anyway.
        if not _relevant(item["title"], snippet):
            continue
        if not _looks_english(f'{item["title"]} {snippet}'):
            continue
        records.append(
            {
                "title": item["title"],
                "snippet": snippet,
                "url": item["url"],
                "date": _normalise_date(item["date"]),
                "publisher": "AI Incident Database",
                "jurisdiction": "Incidents",
                "source_id": INCIDENTS,
            }
        )
    return records


def _merge_rolling(fresh: list[dict], keep_days: int = 120) -> list[dict]:
    """Merge today's items into the feed already on disk.

    The feed has to roll rather than be replaced, for a reason that only shows up
    in production: arXiv announces nothing at weekends and government feeds drop
    older items entirely. Replacing wholesale would empty a third of the feed
    every Saturday and lose anything that scrolled off a source. Merging keeps a
    rolling window and makes the dataset the record rather than a snapshot of
    whatever the sources happened to be serving at 06:17.

    Dedupe is on URL, and the FRESH copy wins, so a corrected headline replaces
    the one we stored.
    """
    existing: list[dict] = []
    path = PROCESSED / "news-feed.json"
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("records", [])
        except (json.JSONDecodeError, OSError):
            existing = []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=keep_days)).date().isoformat()

    merged: dict[str, dict] = {}
    for record in existing:
        if record.get("date", "") >= cutoff:
            merged[record["url"]] = record
    for record in fresh:
        merged[record["url"]] = record

    ordered = sorted(merged.values(), key=lambda r: (r.get("date", ""), r["title"]), reverse=True)

    # Cap per source before the global cap, so one prolific feed cannot crowd the
    # others out of the window even when it dominates a given week.
    kept: list[dict] = []
    counts: dict[str, int] = {}
    for record in ordered:
        source = record["source_id"]
        cap = PER_SOURCE_CAP.get(source, DEFAULT_CAP)
        if counts.get(source, 0) >= cap:
            continue
        counts[source] = counts.get(source, 0) + 1
        kept.append(record)

    return kept[:TOTAL_CAP]


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
        (
            "Canada",
            lambda: fetch_xml_feed(
                CANADA,
                "https://api.io.canada.ca/io-server/gc/news/en/v2"
                "?dept=departmentofindustry&sort=publishedDate&orderBy=desc"
                "&publishedDate%3E=2025-01-01&pick=100&format=atom"
                "&atomtitle=Canada%20News%20Centre",
                "Canada", "Government of Canada", offline, needs_filter=True,
            ),
        ),
        ("arXiv cs.AI", lambda: fetch_arxiv(ARXIV_AI, offline)),
        ("arXiv cs.CY", lambda: fetch_arxiv(ARXIV_CY, offline)),
        ("AI Incident Database", lambda: fetch_incidents(offline)),
    ]

    for label, collect in collectors:
        try:
            got = collect()
            print(f"  {label}: {len(got)} relevant items")
            records.extend(got)
        except Exception as exc:  # noqa: BLE001 - one dead feed must not kill the feed
            print(f"  WARNING {label} failed: {type(exc).__name__}: {exc}")

    if not records:
        raise RuntimeError("every news feed failed; refusing to write an empty feed")

    merged = _merge_rolling(records)

    # Normalise and classify AFTER the merge, not before, so records carried
    # over from previous runs are brought up to the current rules rather than
    # keeping whatever the rules were the day they arrived. Categories are a
    # statement about the rule as it stands now, and items already on disk
    # predate fields that were added later.
    for record in merged:
        record["kind"] = KIND_BY_SOURCE.get(record["source_id"], DEFAULT_KIND)
        record.setdefault("doc_type", "")
        record["snippet"] = URL_IN_TEXT.sub(" ", record["snippet"]).strip()
        categories, matched = categorise(record["title"], record["snippet"])
        record["categories"] = categories
        record["matched_terms"] = matched

    counts = {name: sum(name in r["categories"] for r in merged) for name in CATEGORY_ORDER}
    print("  categories: " + ", ".join(f"{k} {v}" for k, v in counts.items()))

    write_dataset(
        "news-feed",
        merged,
        source_ids=sorted({r["source_id"] for r in merged}),
        unit=None,
        notes=(
            f"Headline, a short extract of at most {SNIPPET_CHARS} characters, and a link "
            "back to the original. We do not reproduce full text. A rolling window: items "
            "stay for up to 120 days rather than vanishing when a source drops them, "
            "because arXiv announces nothing at weekends and government feeds are short. "
            "Categories are assigned by keyword rule and each item carries the terms that "
            "matched, so the classification can be checked rather than trusted. "
            "Departmental communications are political statements about policy, not "
            "neutral descriptions of it, and preprints are not peer reviewed."
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

    # Invisible characters. A zero-width space is not whitespace to Python, so it
    # survived the collapse and counted against the copyright cap while showing
    # the reader nothing.
    invisible = _clean("Anth­ropic​ discloses‎ a hacking﻿ incident")
    assert invisible == "Anthropic discloses a hacking incident", repr(invisible)
    assert len(invisible) == 38, f"invisible characters still counted: {len(invisible)}"

    for dashed in ("a — b", "a – b", "x&mdash;y", "p &lt;span&gt;q&lt;/span&gt; r"):
        cleaned = _clean(dashed)
        assert "—" not in cleaned and "–" not in cleaned, (
            f"dash normalisation failed on {dashed!r} -> {cleaned!r}"
        )
        assert "<" not in cleaned and "&" not in cleaned, (
            f"markup leaked through _clean on {dashed!r} -> {cleaned!r}"
        )

    # Live-feed furniture that reached the page before being caught.
    leaked = _strip_preamble(
        "lobacni 11 November 2026 The Drone Tech Forum is a coordination mechanism. "
        "© Marcus Jacobi The European Commission said so.",
        "Join the Inaugural D-TECT Forum",
    )
    assert not leaked.startswith("lobacni"), leaked
    assert "Marcus Jacobi" not in leaked, leaked
    assert leaked.startswith("The Drone Tech"), leaked

    # A bare URL in a summary must not reach the extract, and must not reach the
    # classifier: "incidentdatabase.ai" in the text matched the "incident" rule
    # and filed court filings under safety on the strength of their own link.
    with_url = _strip_preamble(
        "Court document filed in Florida. (https://incidentdatabase.ai/cite/1686#7944)", ""
    )
    assert "http" not in with_url, with_url
    assert "incidentdatabase" not in with_url, with_url
    categories, matched = categorise("Order on Renewed Motion", with_url)
    assert "safety" not in categories, f"URL text still reaching the classifier: {matched}"

    # Language screen, against the real headlines that got through.
    for dutch in (
        "Wel of niet zeggen dat je in een neppornovideo zit? BN'ers worstelen ermee",
        "Vrouwelijke BN'ers overwegen aangifte vanwege deepfake pornovideo's",
        "Meerdere vrouwelijke bekende Nederlanders overwegen juridische stappen omdat zij "
        "zijn opgedoken in gemanipuleerde pornovideo's. Deze video's staan op een website "
        "die al jaren bestaat en waar honderden filmpjes te vinden zijn.",
        "Wat vrouwen ervaren in de Tweede Kamer. Je hebt geluk dat jij een vrouw bent",
    ):
        assert not _looks_english(dutch), f"language screen admitted Dutch: {dutch}"

    for english in (
        "US judge upholds $243 million verdict against Tesla over fatal Autopilot crash",
        "The Commission has adopted the code of practice for general-purpose models",
        "Tesla said it did not have key data from the crash, and a hacker found it",
    ):
        assert _looks_english(english), f"language screen rejected English: {english}"

    ec = ("State of the Union 2026 Anonymous (not verified) Mon, 08/31/2026 - 16:11 "
          "The President set out the priorities.")
    stripped = _strip_preamble(ec, "State of the Union 2026")
    assert "Anonymous" not in stripped and "08/31/2026" not in stripped, stripped
    assert stripped.startswith("The President"), stripped

    # Categorisation. The failure mode here is not a crash, it is a classifier
    # that quietly files everything under one heading and looks like it worked.
    # The first version bounded only the front of each term, so "act" matched
    # "action", "impact" and "interact" and swept the whole feed into policy.
    #
    # Each of these flips if the trailing boundary is dropped, which is the
    # point: a case that passes either way is not testing anything. Verified by
    # removing the boundary and watching every one of them fail.
    for noise, forbidden, why in (
        ("Computer science curriculum for primary schools", "progress", "compute"),
        ("Evaluate the applicants for the grant", "safety", "eval"),
        ("Billing systems modernisation programme", "policy", "bill"),
        ("A senator and a lawyer disagreed", "policy", "senate"),
        ("Congressional district boundaries redrawn", "policy", "congress"),
    ):
        categories, matched = categorise(noise, "")
        assert forbidden not in categories, (
            f"{forbidden!r} matched a word merely containing {why!r}: "
            f"{noise!r} -> {categories} via {matched}"
        )

    cases = [
        ("Commission adopts the AI Act code of practice for general-purpose models",
         "policy", "governance"),
        ("New interpretability results on reward hacking in language models",
         "alignment", None),
        ("Red team evaluation finds jailbreak risk in deployed assistant",
         "safety", None),
        ("Model outperforms prior state of the art on reasoning benchmarks",
         "progress", None),
        ("NIST publishes a risk management framework for generative systems",
         "governance", "safety"),
    ]
    for headline, wanted, also in cases:
        categories, matched = categorise(headline, "")
        assert wanted in categories, f"{headline!r} -> {categories}, wanted {wanted}"
        assert matched[wanted], f"{headline!r} recorded no matched terms for {wanted}"
        if also:
            assert also in categories, f"{headline!r} -> {categories}, also wanted {also}"

    # Named statutes, which no keyword list can catch without bare "act".
    for headline, expected in (
        ("Commission designates ChatGPT under the Digital Services Act", "Digital Services Act"),
        ("Consultation on the Online Safety Act 2023", "Online Safety Act"),
    ):
        categories, matched = categorise(headline, "")
        assert "policy" in categories, f"{headline!r} -> {categories}"
        assert expected in matched["policy"], f"{headline!r} matched {matched['policy']}"

    # Lower case "act" must still not qualify, or the rule reopens the hole that
    # removing bare "act" from the keyword list was there to close.
    categories, _ = categorise("The minister said the plan would act on impact", "")
    assert "policy" not in categories, categories

    # Something about AI and nothing narrower must fall through to general
    # rather than being forced into a category it does not belong in.
    categories, matched = categorise("Minister visits an artificial intelligence startup", "")
    assert categories == ["general"], categories
    assert matched == {}, matched

    # Prefix terms must still work, and must not swallow unrelated words.
    categories, matched = categorise("Fine-tuning and supervisory standards", "")
    assert "progress" in categories and "governance" in categories, categories
    assert any(t.startswith("fine-tun") for t in matched["progress"]), matched

    # Every category the site renders must have a label, or a chip renders blank.
    for name in CATEGORY_ORDER:
        assert CATEGORY_LABELS.get(name), f"category {name!r} has no label"
    assert set(CATEGORY_TERMS) | {"general"} == set(CATEGORY_ORDER), (
        "CATEGORY_ORDER and CATEGORY_TERMS have drifted apart"
    )

    print("fetch_news self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        run(offline="--offline" in sys.argv)
