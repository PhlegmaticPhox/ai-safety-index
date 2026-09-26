"""AI Usage Disclosure Index: how much AI is used, by whom, and for what, as each
company or study states it.

Three datasets, all hand-coded from primary publications:

    token-volumes   every aggregate token count a company has put on the record,
                    normalised to tokens per month, plus the notable developers
                    that have published none
    usage-reach     disclosed user counts per product
    usage-purposes  published shares of use by topic or task

WHY HAND-CODED. Nobody publishes a dataset of this. The figures exist as single
sentences in earnings calls, keynotes and research reports, each with its own
scope, unit and period. Collecting them with the scope written beside each number
is the whole of the value, and it has to be done by reading.

WHAT IT IS NOT. Not a market share estimate. Google counts tokens across every
product it runs, OpenAI counts its API and not ChatGPT, Microsoft counted one
platform, ByteDance counts one model family. A token is also not a fixed unit:
tokenisers differ between companies, and an image or a second of video can be
hundreds of tokens. The figures answer "what has each company said", and the page
prints the scope next to every one of them for that reason.

    python etl/build_usage_index.py                # validate and write
    python etl/build_usage_index.py --self-check   # schema, units, normalisation
    python etl/build_usage_index.py --check-links  # probe every citation
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import check_links, review_stamp, write_dataset

SOURCE = "usage-disclosure-index"
REVIEWED = "2026-09-25"

# Normalisation to a month. A month is a twelfth of a Julian year, so a per-minute
# rate and a per-day rate land on the same calendar. Quarterly and annual totals
# become monthly AVERAGES, which is a different statement from a monthly peak and
# is labelled as such on the page.
MINUTES_PER_MONTH = 60 * 24 * 365.25 / 12
DAYS_PER_MONTH = 365.25 / 12
PER_MONTH = {
    "minute": MINUTES_PER_MONTH,
    "day": DAYS_PER_MONTH,
    "month": 1.0,
    "quarter": 1 / 3,
    "year": 1 / 12,
}

# "company": the company's own publication, or an executive speaking at the
# company's own event with the company's transcript online.
# "reported": an executive statement known only through press reporting.
BASIS = {
    "company": "Published by the company",
    "reported": "Company statement, as reported by the press",
}

# Each series is one company counting one thing, so a line on the chart never
# joins two different scopes.
SERIES = {
    "google-all": {
        "company": "Google",
        "label": "Google, all products",
        "scope": (
            "Every Google product and API: Search, including AI Overviews and AI Mode, "
            "the Gemini app, Workspace, YouTube and Cloud. No split by product is published."
        ),
    },
    "google-api": {
        "company": "Google",
        "label": "Google, API only",
        "scope": "Google's own models called directly through its API by customers.",
    },
    "bytedance-doubao": {
        "company": "ByteDance",
        "label": "ByteDance, Doubao models",
        "scope": (
            "Daily token use of ByteDance's Doubao model family, as stated by its cloud "
            "unit Volcano Engine. Whether ByteDance's own apps are included is not stated."
        ),
    },
    "microsoft-foundry": {
        "company": "Microsoft",
        "label": "Microsoft, Foundry",
        "scope": (
            "Tokens processed through Microsoft's model platform, Foundry. Aggregate "
            "figures stopped after fiscal 2025; later calls report customer counts only."
        ),
    },
    "openai-api": {
        "company": "OpenAI",
        "label": "OpenAI, API only",
        "scope": "OpenAI's API. ChatGPT, its largest product, is not included.",
    },
}

GOOGLE_IO_2025 = "https://blog.google/innovation-and-ai/technology/ai/io-2025-keynote/"
GOOGLE_IO_2026 = "https://blog.google/innovation-and-ai/sundar-pichai-io-2026/"
GOOGLE_EARNINGS = "https://blog.google/company-news/inside-google/message-ceo/alphabet-earnings-{}/"
MICROSOFT_EARNINGS = "https://www.microsoft.com/en-us/investor/events/fy-{}/earnings-fy-{}-{}"
OPENAI_MARCH_2026 = "https://openai.com/index/accelerating-the-next-phase-ai/"

VOLUMES = [
    # Google, every product.
    {
        "series": "google-all", "stated": "9.7 trillion tokens a month", "value": 9.7e12,
        "per": "month", "as_of": "2024-04", "announced": "2025-05",
        "venue": "Google I/O keynote", "basis": "company", "url": GOOGLE_IO_2025,
        "note": "Stated a year later, as the baseline for the 480 trillion figure.",
    },
    {
        "series": "google-all", "stated": "over 480 trillion tokens a month", "value": 480e12,
        "per": "month", "as_of": "2025-04", "announced": "2025-05",
        "venue": "Google I/O keynote", "basis": "company", "url": GOOGLE_IO_2025,
        "note": "",
    },
    {
        "series": "google-all", "stated": "over 980 trillion monthly tokens", "value": 980e12,
        "per": "month", "as_of": "2025-07", "announced": "2025-07",
        "venue": "Alphabet Q2 2025 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q2-2025"), "note": "",
    },
    {
        "series": "google-all", "stated": "over 1.3 quadrillion monthly tokens", "value": 1.3e15,
        "per": "month", "as_of": "2025-10", "announced": "2025-10",
        "venue": "Alphabet Q3 2025 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q3-2025"), "note": "",
    },
    {
        "series": "google-all", "stated": "over 3.2 quadrillion tokens a month", "value": 3.2e15,
        "per": "month", "as_of": "2026-05", "announced": "2026-05",
        "venue": "Google I/O keynote", "basis": "company", "url": GOOGLE_IO_2026,
        "note": "",
    },
    # Google, API only.
    {
        "series": "google-api", "stated": "7 billion tokens per minute", "value": 7e9,
        "per": "minute", "as_of": "2025-10", "announced": "2025-10",
        "venue": "Alphabet Q3 2025 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q3-2025"), "note": "",
    },
    {
        "series": "google-api", "stated": "over 10 billion tokens per minute", "value": 10e9,
        "per": "minute", "as_of": "2026-02", "announced": "2026-02",
        "venue": "Alphabet Q4 2025 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q4-2025"), "note": "",
    },
    {
        "series": "google-api", "stated": "more than 16 billion tokens per minute", "value": 16e9,
        "per": "minute", "as_of": "2026-04", "announced": "2026-04",
        "venue": "Alphabet Q1 2026 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q1-2026"), "note": "",
    },
    {
        "series": "google-api", "stated": "22 billion tokens per minute", "value": 22e9,
        "per": "minute", "as_of": "2026-07", "announced": "2026-07",
        "venue": "Alphabet Q2 2026 earnings call", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q2-2026"), "note": "",
    },
    # ByteDance. Known only through reporting of Volcano Engine's conference
    # statements, which is why every row is marked reported.
    {
        "series": "bytedance-doubao", "stated": "4 trillion tokens a day", "value": 4e12,
        "per": "day", "as_of": "2024-12", "announced": "2025-12",
        "venue": "Volcano Engine FORCE conference", "basis": "reported",
        "url": "https://www.silicon.co.uk/e-innovation/artificial-intelligence/doubao-bytedance-ai-628108",
        "note": "Stated a year later, as the baseline for the 50 trillion figure.",
    },
    {
        "series": "bytedance-doubao", "stated": "over 50 trillion tokens a day", "value": 50e12,
        "per": "day", "as_of": "2025-12", "announced": "2025-12",
        "venue": "Volcano Engine FORCE conference", "basis": "reported",
        "url": "https://www.silicon.co.uk/e-innovation/artificial-intelligence/doubao-bytedance-ai-628108",
        "note": "",
    },
    {
        "series": "bytedance-doubao", "stated": "over 120 trillion tokens a day", "value": 120e12,
        "per": "day", "as_of": "2026-03", "announced": "2026-04",
        "venue": "Volcano Engine statement", "basis": "reported",
        "url": "https://global.chinadaily.com.cn/a/202604/02/WS69ce3326a310d6866eb41733.html",
        "note": "",
    },
    {
        "series": "bytedance-doubao", "stated": "over 180 trillion tokens a day", "value": 180e12,
        "per": "day", "as_of": "2026-06", "announced": "2026-06",
        "venue": "Volcano Engine FORCE conference", "basis": "reported",
        "url": "https://pandaily.com/bytedance-doubao-production-grade-ai-jun2026",
        "note": "Growth attributed by the company to AI video generation and agents.",
    },
    # Microsoft. Two figures, then silence.
    {
        "series": "microsoft-foundry", "stated": "a record 50 trillion tokens last month",
        "value": 50e12, "per": "month", "as_of": "2025-03", "announced": "2025-04",
        "venue": "Microsoft FY25 Q3 earnings call", "basis": "company",
        "url": MICROSOFT_EARNINGS.format("2025", "2025", "q3"),
        "note": "The same call gave over 100 trillion for the quarter.",
    },
    {
        "series": "microsoft-foundry", "stated": "over 500 trillion this year", "value": 500e12,
        "per": "year", "as_of": "2025-06", "announced": "2025-07",
        "venue": "Microsoft FY25 Q4 earnings call", "basis": "company",
        "url": MICROSOFT_EARNINGS.format("2025", "2025", "q4"),
        "note": "Fiscal year to June 2025, so the monthly figure is an average over it.",
    },
    # OpenAI, API only.
    {
        "series": "openai-api", "stated": "over 6 billion tokens per minute", "value": 6e9,
        "per": "minute", "as_of": "2025-10", "announced": "2025-10",
        "venue": "OpenAI DevDay keynote", "basis": "reported",
        "url": "https://techcrunch.com/2025/10/06/sam-altman-says-chatgpt-has-hit-800m-weekly-active-users/",
        "note": "",
    },
    {
        "series": "openai-api", "stated": "more than 15 billion tokens per minute", "value": 15e9,
        "per": "minute", "as_of": "2026-03", "announced": "2026-03",
        "venue": "OpenAI funding announcement", "basis": "company", "url": OPENAI_MARCH_2026,
        "note": "",
    },
]

# Notable developers with no aggregate token count on the record. Listed because
# the absence is part of the answer to "who processes the most": four of the
# developers on this site's framework index could not be placed on the chart at
# all. "None found" means none in the company's own publications at the review
# date, which is a weaker statement than "none exists" and is worded that way.
UNDISCLOSED = [
    {
        "company": "Anthropic",
        "note": "Publishes use by task in the Anthropic Economic Index, but no volume.",
    },
    {"company": "Meta", "note": "Publishes a monthly user count for Meta AI, but no volume."},
    {"company": "xAI", "note": "No volume or user count found."},
    {"company": "DeepSeek", "note": "No volume or user count found."},
]

REACH = [
    {
        "product": "Google AI Overviews", "company": "Google", "users": 2.5e9,
        "measure": "monthly users", "as_of": "2026-05", "basis": "company", "url": GOOGLE_IO_2026,
        "note": "People shown an AI summary at the top of a Search result, not people who chose an assistant.",
    },
    {
        "product": "Google AI Mode", "company": "Google", "users": 1e9,
        "measure": "monthly users", "as_of": "2026-05", "basis": "company",
        "url": "https://blog.google/innovation-and-ai/technology/ai/google-io-2026-all-our-announcements/",
        "note": "Search's conversational mode, launched in the US in 2025.",
    },
    {
        "product": "Meta AI", "company": "Meta", "users": 1e9,
        "measure": "monthly users", "as_of": "2025-05", "basis": "reported",
        "url": "https://www.cnbc.com/2025/05/28/zuckerberg-meta-ai-one-billion-monthly-users.html",
        "note": "Across Meta's apps, where the assistant is built into search and chat.",
    },
    {
        "product": "Gemini app", "company": "Google", "users": 950e6,
        "measure": "monthly users", "as_of": "2026-07", "basis": "company",
        "url": GOOGLE_EARNINGS.format("q2-2026"), "note": "",
    },
    {
        "product": "ChatGPT", "company": "OpenAI", "users": 900e6,
        "measure": "weekly users", "as_of": "2026-03", "basis": "company",
        "url": OPENAI_MARCH_2026,
        "note": "The only figure here counted weekly, which is a stricter test than monthly.",
    },
    {
        "product": "Microsoft AI features", "company": "Microsoft", "users": 900e6,
        "measure": "monthly users", "as_of": "2025-10", "basis": "company",
        "url": MICROSOFT_EARNINGS.format("2026", "2026", "q1"),
        "note": "Every AI feature across Microsoft's products counted together.",
    },
    {
        "product": "Microsoft Copilot family", "company": "Microsoft", "users": 150e6,
        "measure": "monthly users", "as_of": "2025-10", "basis": "company",
        "url": MICROSOFT_EARNINGS.format("2026", "2026", "q1"), "note": "",
    },
    {
        "product": "GitHub Copilot", "company": "Microsoft", "users": 50e6,
        "measure": "users", "as_of": "2026-07", "basis": "company",
        "url": MICROSOFT_EARNINGS.format("2026", "2026", "q4"),
        "note": "Users, with no period stated.",
    },
]

CHATGPT_STUDY = "https://www.nber.org/papers/w34255"
CLAUDE_MARCH_2026 = "https://www.anthropic.com/research/economic-index-march-2026-report"
CLAUDE_SEPT_2025 = "https://www.anthropic.com/research/anthropic-economic-index-september-2025-report"

# Shares of use as each study states them. `share` is None where the source gives
# words rather than a number ("a little less than half"), because a bar drawn at
# an invented 48% would be a figure this site made up. `approx` marks a figure the
# study gives as a round number rather than to a decimal.
PURPOSES = [
    # ChatGPT, consumer plans, sampled messages.
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Practical guidance", "kind": "topic", "share": 0.29, "approx": True,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Seeking information", "kind": "topic", "share": 0.24, "approx": True,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Writing", "kind": "topic", "share": 0.24, "approx": True,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Computer programming", "kind": "coding", "share": 0.042, "approx": False,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Relationships and personal reflection", "kind": "topic", "share": 0.019,
     "approx": False, "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Games and role-play", "kind": "topic", "share": 0.004, "approx": False,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "consumer messages", "period": "2025-06",
     "category": "Not related to work", "kind": "work", "share": 0.73, "approx": False,
     "url": CHATGPT_STUDY},
    {"product": "ChatGPT", "unit": "work-related consumer messages", "period": "2025-06",
     "category": "Writing", "kind": "topic", "share": 0.40, "approx": True,
     "url": CHATGPT_STUDY},
    # Claude.ai, sampled conversations.
    {"product": "Claude.ai", "unit": "conversations", "period": "2026-02",
     "category": "Computer and mathematical tasks", "kind": "coding", "share": 0.35,
     "approx": False, "url": CLAUDE_MARCH_2026},
    {"product": "Claude.ai", "unit": "conversations", "period": "2026-02",
     "category": "Personal use", "kind": "work", "share": 0.42, "approx": False,
     "url": CLAUDE_MARCH_2026},
    {"product": "Claude.ai", "unit": "conversations", "period": "2026-02",
     "category": "Coursework", "kind": "topic", "share": 0.12, "approx": False,
     "url": CLAUDE_MARCH_2026},
    # Claude through Anthropic's own API, sampled transcripts.
    {"product": "Claude API", "unit": "transcripts", "period": "2025-08",
     "category": "Computer and mathematical tasks", "kind": "coding", "share": None,
     "display": "just under half", "approx": True, "url": CLAUDE_SEPT_2025},
    {"product": "Claude API", "unit": "transcripts", "period": "2025-08",
     "category": "Office and administrative tasks", "kind": "topic", "share": 0.10,
     "approx": True, "url": CLAUDE_SEPT_2025},
    {"product": "Claude API", "unit": "transcripts", "period": "2025-08",
     "category": "Automation patterns", "kind": "mode", "share": 0.77, "approx": False,
     "url": CLAUDE_SEPT_2025},
]

# Which company each product belongs to, so the page can say who publishes a
# breakdown of use and who does not.
PRODUCT_COMPANY = {"ChatGPT": "OpenAI", "Claude.ai": "Anthropic", "Claude API": "Anthropic"}

PUBLISHERS = {
    CHATGPT_STUDY: "Chatterji and others, How People Use ChatGPT, NBER working paper 34255",
    CLAUDE_MARCH_2026: "Anthropic Economic Index, March 2026 report",
    CLAUDE_SEPT_2025: "Anthropic Economic Index, September 2025 report",
}


def _https(url: str, what: str) -> None:
    if not url.startswith("https://"):
        raise ValueError(f"{what}: citation must be an https URL, got {url!r}")


def _month(value: str, what: str) -> None:
    year, _, month = value.partition("-")
    if not (len(year) == 4 and year.isdigit() and month.isdigit() and 1 <= int(month) <= 12):
        raise ValueError(f"{what}: expected YYYY-MM, got {value!r}")


def build_volumes() -> list[dict]:
    records = []
    for entry in VOLUMES:
        what = f"{entry['series']} {entry['as_of']}"
        series = SERIES.get(entry["series"])
        if series is None:
            raise ValueError(f"{what}: unknown series")
        if entry["per"] not in PER_MONTH:
            raise ValueError(f"{what}: unknown period {entry['per']!r}")
        if entry["basis"] not in BASIS:
            raise ValueError(f"{what}: unknown basis {entry['basis']!r}")
        if not entry["value"] > 0:
            raise ValueError(f"{what}: a disclosed volume must be positive")
        _https(entry["url"], what)
        _month(entry["as_of"], what)
        _month(entry["announced"], what)
        if entry["announced"] < entry["as_of"]:
            raise ValueError(f"{what}: announced before the period it describes")
        records.append(
            {
                "company": series["company"],
                "series": entry["series"],
                "series_label": series["label"],
                "scope": series["scope"],
                **{k: entry[k] for k in ("stated", "value", "per", "as_of", "announced", "venue")},
                "tokens_per_month": entry["value"] * PER_MONTH[entry["per"]],
                "average": entry["per"] in ("quarter", "year"),
                "basis": entry["basis"],
                "basis_meaning": BASIS[entry["basis"]],
                "note": entry["note"],
                "url": entry["url"],
                "disclosed": True,
                "reviewed": REVIEWED,
                "source_id": SOURCE,
            }
        )
    for entry in UNDISCLOSED:
        records.append(
            {
                "company": entry["company"],
                "series": None,
                "series_label": None,
                "scope": None,
                "stated": None,
                "value": None,
                "per": None,
                "as_of": None,
                "announced": None,
                "venue": None,
                "tokens_per_month": None,
                "average": False,
                "basis": None,
                "basis_meaning": None,
                "note": entry["note"],
                "url": None,
                "disclosed": False,
                "reviewed": REVIEWED,
                "source_id": SOURCE,
            }
        )
    return sorted(
        records,
        key=lambda r: (not r["disclosed"], r["series"] or "", r["as_of"] or "", r["company"]),
    )


def build_reach() -> list[dict]:
    records = []
    for entry in REACH:
        what = entry["product"]
        _https(entry["url"], what)
        _month(entry["as_of"], what)
        if entry["basis"] not in BASIS:
            raise ValueError(f"{what}: unknown basis {entry['basis']!r}")
        if entry["measure"] not in ("monthly users", "weekly users", "users"):
            raise ValueError(f"{what}: unknown measure {entry['measure']!r}")
        records.append(
            {**entry, "basis_meaning": BASIS[entry["basis"]], "reviewed": REVIEWED,
             "source_id": SOURCE}
        )
    return sorted(records, key=lambda r: -r["users"])


def build_purposes() -> list[dict]:
    records = []
    for entry in PURPOSES:
        what = f"{entry['product']} {entry['category']}"
        _https(entry["url"], what)
        _month(entry["period"], what)
        if entry["kind"] not in ("topic", "coding", "work", "mode"):
            raise ValueError(f"{what}: unknown kind {entry['kind']!r}")
        share = entry["share"]
        if share is None and not entry.get("display"):
            raise ValueError(f"{what}: a share given in words needs its words in `display`")
        if share is not None and not 0 < share < 1:
            raise ValueError(f"{what}: share {share!r} is not a fraction")
        display = entry.get("display") or (
            f"{'about ' if entry['approx'] else ''}{share * 100:.{0 if share >= 0.1 else 1}f}%"
        )
        records.append(
            {
                "product": entry["product"],
                "company": PRODUCT_COMPANY[entry["product"]],
                "unit": entry["unit"],
                "period": entry["period"],
                "category": entry["category"],
                "kind": entry["kind"],
                "share": share,
                "approx": entry["approx"],
                "display": display,
                "publisher": PUBLISHERS[entry["url"]],
                "url": entry["url"],
                "reviewed": REVIEWED,
                "source_id": SOURCE,
            }
        )
    return records


def run(offline: bool = False) -> None:
    """Hand-written, so there is nothing to fetch and offline changes nothing."""
    stamp = review_stamp(REVIEWED)
    write_dataset(
        "token-volumes",
        build_volumes(),
        source_ids=[SOURCE],
        unit="tokens per month",
        notes=(
            f"Every aggregate token count a company has published or stated, reviewed "
            f"{REVIEWED}, normalised to tokens per month by this site. Scopes differ: "
            f"read the scope beside each figure before comparing two of them."
        ),
        retrieved=stamp,
    )
    write_dataset(
        "usage-reach",
        build_reach(),
        source_ids=[SOURCE],
        unit="users",
        notes=(
            f"Disclosed user counts per product, reviewed {REVIEWED}. Weekly and monthly "
            f"counts are different measures and are labelled."
        ),
        retrieved=stamp,
    )
    write_dataset(
        "usage-purposes",
        build_purposes(),
        source_ids=[SOURCE],
        unit="share of the stated unit",
        notes=(
            f"Shares of use by topic or task as each study states them, reviewed "
            f"{REVIEWED}. Units differ between studies: messages, conversations and API "
            f"transcripts are not the same thing and none of them is a token."
        ),
        retrieved=stamp,
    )


def _self_check() -> None:
    volumes = build_volumes()
    reach = build_reach()
    purposes = build_purposes()

    disclosed = [r for r in volumes if r["disclosed"]]
    absent = [r for r in volumes if not r["disclosed"]]
    assert len(disclosed) >= 10, f"only {len(disclosed)} disclosed volumes"
    assert absent, "no undisclosed developer listed; the absence is part of the finding"
    assert not {r["company"] for r in absent} & {r["company"] for r in disclosed}, (
        "a company is listed both as disclosing and as not disclosing"
    )

    # Normalisation, against the one case where the company did the arithmetic
    # itself: 22 billion a minute was described on the Q2 2026 call as over one
    # quadrillion a month. If the constant drifts, this is where it shows.
    google_api = next(r for r in disclosed if r["series"] == "google-api" and r["value"] == 22e9)
    assert 0.9e15 < google_api["tokens_per_month"] < 1.1e15, google_api["tokens_per_month"]
    daily = next(r for r in disclosed if r["per"] == "day")
    assert abs(daily["tokens_per_month"] / daily["value"] - 30.4375) < 1e-9
    annual = next(r for r in disclosed if r["per"] == "year")
    assert annual["average"], "an annual total normalised to a month must be flagged as an average"

    # Every series must be one company and one scope, or a line on the chart
    # would join two different things.
    for key in SERIES:
        rows = [r for r in disclosed if r["series"] == key]
        assert rows, f"series {key} has no figures"
        assert len({r["scope"] for r in rows}) == 1

    # A share stated in words must never be drawn as a number.
    worded = [p for p in purposes if p["share"] is None]
    assert worded and all("%" not in p["display"] for p in worded)
    # Shares of one unit in one period cannot sum past the whole.
    by_unit: dict[tuple, float] = {}
    for p in purposes:
        if p["share"] is not None and p["kind"] in ("topic", "coding"):
            key = (p["product"], p["unit"], p["period"])
            by_unit[key] = by_unit.get(key, 0) + p["share"]
    for key, total in by_unit.items():
        assert total <= 1.0 + 1e-9, f"{key}: topic shares sum to {total:.2f}"

    assert reach == sorted(reach, key=lambda r: -r["users"])
    weekly = [r for r in reach if r["measure"] == "weekly users"]
    assert weekly, "ChatGPT's weekly measure must stay labelled weekly"

    # The validator has to reject a volume given for an unknown period, because
    # that is what a typo in `per` looks like, and it would otherwise normalise
    # silently to nothing.
    VOLUMES.append({**VOLUMES[0], "per": "fortnight"})
    try:
        build_volumes()
    except ValueError:
        pass
    else:
        raise AssertionError("build_volumes accepted an unknown period")
    finally:
        VOLUMES.pop()

    print(
        f"build_usage_index self-check passed: {len(disclosed)} volumes in "
        f"{len(SERIES)} series, {len(absent)} developers with none, {len(reach)} user "
        f"counts, {len(purposes)} use shares"
    )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    elif "--check-links" in sys.argv:
        entries = [(f"{r['series']} {r['as_of']}", r["url"]) for r in build_volumes() if r["url"]]
        entries += [(r["product"], r["url"]) for r in build_reach()]
        entries += [(r["category"][:30], r["url"]) for r in build_purposes()]
        raise SystemExit(1 if check_links(entries) else 0)
    else:
        _self_check()
        run()
