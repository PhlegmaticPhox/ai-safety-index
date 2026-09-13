"""OpenAlex: how much published research goes into each corner of the AI field.

Answers a question none of the other sources here can: safety work is always
described as lagging capability work, and this is what that looks like as a
count. It is the only dataset on the site whose subject is the research effort
rather than the systems it studies.

Why OpenAlex and not arXiv: arXiv's API rate-limits an unauthenticated caller to
the point of unusability (three consecutive 429s from a single sequential run
here), and it covers preprints only. OpenAlex is CC0, needs no key, answers a
grouped count in one request, and indexes journals and conferences too.

What the numbers are, precisely: the count of indexed works whose title or
abstract matches a stated search phrase, by publication year. That is a keyword
match, not a field classification. A paper doing alignment work without using
the word is missed; one mentioning it in passing is counted. This is why the
literal query string travels with every series and is printed on the page: the
reader can disagree with the definition and see exactly what to disagree with.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from common import SSL_CONTEXT, USER_AGENT, write_dataset, utcnow

SOURCE_ID = "openalex"
API = "https://api.openalex.org/works"

# Indexing lags publication by months, and the current year is partial by
# definition. Both are stated on the page rather than smoothed away.
FIRST_YEAR = 2015

# Each area is one OpenAlex search expression, stored verbatim so it can be
# printed next to its own number. "|" is OR inside a single search term, and a
# second `title_and_abstract.search` clause ANDs with the first, which is how
# `scope` narrows a phrase that other fields also use.
#
# The phrases were chosen to be the terms the communities actually use about
# themselves, not the terms an outsider would pick. They are deliberately narrow:
# a broad query like "artificial intelligence" returns six decades of unrelated
# work and would make every series meaningless.
AREAS = [
    {
        "key": "capability",
        "label": "Frontier model research",
        "role": "capability",
        "query": '"large language model"|"foundation model"|"generative AI"',
        "about": "Work on the systems themselves.",
    },
    {
        "key": "safety",
        "label": "Safety and alignment",
        "role": "safety",
        "query": '"AI safety"|"AI alignment"|"model alignment"|"aligned AI"',
        "about": "Work that names safety or alignment of AI systems as its subject.",
    },
    {
        "key": "interpretability",
        "label": "Interpretability",
        "role": "safety",
        "query": '"mechanistic interpretability"|"model interpretability"|"interpretable machine learning"',
        "about": "Work on reading what a model has learned. Excludes the older explainable-AI literature.",
    },
    {
        "key": "evaluation",
        "label": "Evaluation and red teaming",
        "role": "safety",
        "query": '"red teaming"|"jailbreak"|"adversarial prompt"|"prompt injection"',
        "about": "Work on finding out what a model will do when someone tries to make it misbehave.",
    },
    {
        "key": "governance",
        "label": "Governance and regulation",
        "role": "governance",
        "query": '"AI governance"|"AI regulation"|"algorithmic accountability"',
        "about": "Work on the rules around AI systems rather than the systems.",
    },
    {
        "key": "catastrophic",
        "label": "Catastrophic and existential risk",
        "role": "safety",
        "query": '"existential risk"|"catastrophic risk"|"loss of control"',
        # Climate, biosecurity, finance and disaster research all use these
        # phrases. Unscoped, the series ran at roughly a thousand works a year
        # in 2015, before an AI existential-risk literature meaningfully existed,
        # which told you about the other fields and nothing about this one.
        "scope": '"artificial intelligence"|"machine learning"|"AI system"',
        "about": (
            "Narrowed to works that also name AI, because these phrases belong to climate "
            "and biosecurity research too. Still the loosest series here."
        ),
    },
]


def _filter(query: str, scope: str | None = None) -> str:
    """The filter expression for one area, built in one place.

    Repeating `title_and_abstract.search` ANDs the two clauses, which OpenAlex
    confirms in the `x_query` it echoes back.
    """
    parts = [f"title_and_abstract.search:{query}"]
    if scope:
        parts.append(f"title_and_abstract.search:{scope}")
    parts.append(f"from_publication_date:{FIRST_YEAR}-01-01")
    return ",".join(parts)


def _get(params: dict[str, str], retries: int = 3) -> dict:
    url = f"{API}?{urllib.parse.urlencode(params)}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=60, context=SSL_CONTEXT) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(2**attempt)
    raise RuntimeError(f"OpenAlex request failed: {url}\n  {last}")


def counts_by_year(query: str, scope: str | None = None) -> dict[int, int]:
    """Works per publication year matching `query`, in one request.

    group_by returns the whole histogram at once, so the six series here cost six
    requests rather than six times seventy. OpenAlex allows 100,000 credits a day
    and this run spends six of them.
    """
    payload = _get(
        {
            "filter": _filter(query, scope),
            "group_by": "publication_year",
            "per_page": "50",
        }
    )
    out: dict[int, int] = {}
    this_year = date.today().year
    for group in payload.get("group_by", []):
        try:
            year = int(group["key"])
        except (TypeError, ValueError):
            continue
        # OpenAlex carries a handful of works stamped with impossible publication
        # years from bad upstream metadata: a 2036 row appeared in the first run
        # of this. Silently plotting it would put a bar in the future.
        if year < FIRST_YEAR or year > this_year:
            continue
        out[year] = group["count"]
    return out


def run(offline: bool = False) -> None:
    if offline:
        print("  skipped openalex: grouped counts are computed live, nothing cached to rebuild")
        return

    this_year = date.today().year
    years = list(range(FIRST_YEAR, this_year + 1))
    retrieved = utcnow()

    series = {}
    for area in AREAS:
        series[area["key"]] = counts_by_year(area["query"], area.get("scope"))
        print(f"  {area['key']}: {sum(series[area['key']].values()):,} works")
        time.sleep(1)

    records = []
    for area in AREAS:
        by_year = series[area["key"]]
        records.append(
            {
                "key": area["key"],
                "label": area["label"],
                "role": area["role"],
                "about": area["about"],
                "query": area["query"],
                "scope": area.get("scope"),
                # The URL a reader can open to check the number themselves. This is
                # the citation-first rule applied to a computed figure rather than
                # a downloaded one.
                "query_url": (
                    "https://openalex.org/works?"
                    + urllib.parse.urlencode(
                        {
                            "filter": _filter(area["query"], area.get("scope")),
                            "group_by": "publication_year",
                        }
                    )
                ),
                "points": [{"year": y, "count": by_year.get(y, 0)} for y in years],
                "total": sum(by_year.values()),
                "latest_complete": by_year.get(this_year - 1, 0),
                "partial_year": this_year,
                "source_id": SOURCE_ID,
            }
        )

    write_dataset(
        "research-volume",
        records,
        source_ids=[SOURCE_ID],
        unit="indexed works per year",
        notes=(
            f"Works indexed by OpenAlex whose title or abstract matches the stated search "
            f"phrase, by publication year, {FIRST_YEAR} onward. Keyword match, not a field "
            f"classification. {this_year} is a partial year and indexing lags publication, "
            f"so the last two points understate."
        ),
        retrieved=retrieved,
    )


def _self_check() -> None:
    """Check the two things that can go wrong quietly.

    1. The year filter. An impossible year from bad upstream metadata would plot
       a bar in the future, and nothing about the chart would look wrong.
    2. The query actually narrowing. A malformed expression that OpenAlex ignores
       returns the whole index, which looks like an enormous and exciting number
       rather than an error.
    """
    this_year = date.today().year

    safety = counts_by_year(AREAS[1]["query"])
    assert safety, "safety query returned no years at all"
    assert all(FIRST_YEAR <= y <= this_year for y in safety), f"year outside range: {sorted(safety)}"

    total_index = _get({"filter": "from_publication_date:2015-01-01", "per_page": "1"})
    whole = total_index["meta"]["count"]
    narrow = sum(safety.values())
    assert narrow < whole / 100, (
        f"the safety query matched {narrow:,} of {whole:,} works since {FIRST_YEAR}. "
        f"That is too large a share to be a phrase match: the query is probably being "
        f"ignored rather than applied."
    )

    # Sabotage check: a query that cannot match anything must come back empty,
    # which proves the filter is reaching the server rather than being dropped.
    time.sleep(1)
    nonsense = counts_by_year('"zzzznotarealphrasezzzz"')
    assert sum(nonsense.values()) == 0, f"impossible phrase matched {nonsense}"

    # The scope clause has to narrow. If OpenAlex ever stops ANDing a repeated
    # filter key, the catastrophic-risk series silently reverts to counting
    # climate and biosecurity papers, and the chart still looks entirely normal.
    time.sleep(1)
    risk = AREAS[-1]
    assert risk.get("scope"), "expected the last area to be the scoped one"
    wide = sum(counts_by_year(risk["query"]).values())
    time.sleep(1)
    narrowed = sum(counts_by_year(risk["query"], risk["scope"]).values())
    assert narrowed < wide * 0.5, (
        f"scoping changed {wide:,} to {narrowed:,}, which is not a real narrowing. "
        f"The second title_and_abstract.search clause is not being ANDed."
    )

    print(
        f"  openalex self-check passed: {narrow:,} safety works of {whole:,} indexed "
        f"since {FIRST_YEAR}, years {min(safety)}-{max(safety)}; "
        f"scoping narrowed {wide:,} to {narrowed:,}"
    )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        run(offline="--offline" in sys.argv)
