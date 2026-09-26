"""Two hand-coded indexes about frontier models: who promises what, and what law
actually bites at what size.

Both exist because nobody else joins them up. Capability data lives at Epoch,
safety frameworks live as PDFs on eight different company websites, and compute
thresholds live inside statutes. The question a reader actually has, which is
"at what point does a model become someone's legal problem, and who has said
what they will do about it", needs all three in one place.

    safety-frameworks   one record per developer that has published a frontier
                        safety framework, plus the notable developers that have not
    legal-thresholds    every training-compute threshold written into law,
                        executive action or an official policy document

WHAT THE FIRST ONE IS NOT. Not a ranking and not a verification. Every field is
what a developer says about itself, under a framework it wrote itself, with no
common scale and no external audit. That is precisely the fact worth indexing:
eight companies have written eight different scales, and none of them is
comparable to any other. Where this index says a developer commits to something,
it means the document says so, not that it happened.

    python etl/build_frontier_index.py                # validate and write
    python etl/build_frontier_index.py --self-check   # schema and coverage
    python etl/build_frontier_index.py --check-links  # probe every citation
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import check_links, review_stamp, write_dataset

FRAMEWORK_SOURCE = "safety-frameworks-index"
THRESHOLD_SOURCE = "legal-thresholds-index"
# Reviewed separately, because they move separately. The thresholds were
# re-read on the later date and New York's RAISE Act added. The frameworks were
# not: Amazon revised its framework on 17 September 2026, and until someone reads
# the revision the index says when it was last read rather than claiming a review
# that did not happen.
FRAMEWORKS_REVIEWED = "2026-09-13"
THRESHOLDS_REVIEWED = "2026-09-25"

# The four things worth comparing across frameworks, because they are the four
# that differ. Everything else in these documents is close to boilerplate.
#
#   scale         what the developer calls its risk levels, and how many there are
#   domains       which capabilities it says it evaluates for
#   external      whether the document commits to evaluation by someone else
#   halt          whether the document commits to not deploying, or not training,
#                 if a threshold is reached without mitigations
#
# "halt" is the one that matters most and the one most often softened in the
# wording. Where a framework says it will pause, this records "yes"; where it
# says it will consider, weigh or take appropriate action, it records "qualified".
HALT = {
    "yes": "Commits to not deploying, or not continuing, until mitigations are in place.",
    "qualified": "Commits to a decision process rather than to an outcome.",
    "none": "No stated commitment to stop.",
    "no-framework": "No published framework, so nothing to commit to.",
}

DEVELOPERS = [
    {
        "developer": "Anthropic",
        "framework": "Responsible Scaling Policy",
        "scale": "AI Safety Levels, ASL-1 to ASL-4 and above",
        "levels": 4,
        "domains": ["CBRN", "cyber", "autonomy"],
        "external": True,
        "halt": "yes",
        "since": 2023,
        "url": "https://www.anthropic.com/news/anthropics-responsible-scaling-policy",
        "note": (
            "The first of these frameworks, and the one the others are written against. "
            "Ties defined capability thresholds to required security and deployment "
            "standards, and commits to holding deployment until the corresponding standard "
            "is met."
        ),
    },
    {
        "developer": "OpenAI",
        "framework": "Preparedness Framework",
        "scale": "Capability levels: Low, Medium, High, Critical",
        "levels": 4,
        "domains": ["CBRN", "cyber", "autonomy", "persuasion"],
        "external": True,
        "halt": "yes",
        "since": 2023,
        "url": "https://openai.com/index/updating-our-preparedness-framework/",
        "note": (
            "Tracked categories have changed between versions, with persuasion removed as a "
            "tracked category in the 2025 revision. A framework that can be revised by its "
            "author is a different kind of object from a statute, which is the general "
            "point of this index."
        ),
    },
    {
        "developer": "Google DeepMind",
        "framework": "Frontier Safety Framework",
        "scale": "Critical Capability Levels",
        "levels": 0,
        "domains": ["CBRN", "cyber", "ML R&D", "deceptive alignment"],
        "external": False,
        "halt": "qualified",
        "since": 2024,
        "url": "https://deepmind.google/discover/blog/strengthening-our-frontier-safety-framework/",
        "note": (
            "Defines capability levels per domain rather than one ladder, so it has no single "
            "level count. The only framework here that names deceptive alignment as a tracked "
            "domain in its own right."
        ),
    },
    {
        "developer": "Meta",
        "framework": "Frontier AI Framework",
        "scale": "Outcomes-led: moderate, high, critical risk",
        "levels": 3,
        "domains": ["CBRN", "cyber"],
        "external": False,
        "halt": "yes",
        "since": 2025,
        "url": "https://ai.meta.com/static-resource/meta-frontier-ai-framework/",
        "note": (
            "Matters more than its length suggests, because Meta releases open weights. A "
            "decision not to release is the only mitigation available once weights are out, "
            "which makes the pre-release threshold the whole of the policy."
        ),
    },
    {
        "developer": "Microsoft",
        "framework": "Frontier Governance Framework",
        "scale": "Leading indicator thresholds per capability",
        "levels": 0,
        "domains": ["CBRN", "cyber", "autonomy"],
        "external": True,
        "halt": "qualified",
        "since": 2025,
        "url": "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/final/en-us/microsoft-brand/documents/Microsoft-Frontier-Governance-Framework.pdf",
        "note": (
            "Published as a Seoul commitment signatory. Covers models Microsoft itself "
            "develops, which is a narrower set than the models it deploys."
        ),
    },
    {
        "developer": "Amazon",
        "framework": "Frontier Model Safety Framework",
        "scale": "Critical capability thresholds",
        "levels": 0,
        "domains": ["CBRN", "cyber", "autonomy"],
        "external": False,
        "halt": "qualified",
        "since": 2025,
        "url": "https://www.amazon.science/publications/amazons-frontier-model-safety-framework",
        "note": "Published as a Seoul commitment signatory ahead of the Paris AI Action Summit.",
    },
    {
        "developer": "xAI",
        "framework": "Risk Management Framework",
        "scale": "Benchmark thresholds per risk area",
        "levels": 0,
        "domains": ["CBRN", "cyber"],
        "external": False,
        "halt": "qualified",
        "since": 2025,
        "url": "https://x.ai/documents/2025.02.20-RMF-Draft.pdf",
        "note": (
            "The shortest of the frameworks here, and the only one published as a draft. "
            "Ties thresholds to specific public benchmark scores, which is more falsifiable "
            "than most and also easier to saturate."
        ),
    },
    {
        "developer": "DeepSeek",
        "framework": None,
        "scale": None,
        "levels": 0,
        "domains": [],
        "external": False,
        "halt": "no-framework",
        "since": None,
        "url": "https://www.gov.uk/government/publications/frontier-ai-safety-commitments-ai-seoul-summit-2024",
        "note": (
            "Listed as an absence. DeepSeek releases open-weight models at or near the "
            "frontier and has published no safety framework, and is not among the Seoul "
            "signatories. The linked document is the commitment list it is absent from."
        ),
    },
]

# Every training-compute threshold written into an instrument. Five exist. Four
# of them are the same number, 1e26, of which one is revoked, one was vetoed and
# one is enacted but not yet applicable. The EU's is the only one in force in
# binding law that applies to a market rather than to a single US state.
#
# An enacted threshold carries the date it applies from, which the page prints.
# Its status is not flipped automatically on that date: commencement dates move
# (Colorado's has moved more than once), and a status a script changed without
# anyone reading the law would be a guess presented as a fact.
THRESHOLDS = [
    {
        "jurisdiction": "European Union",
        "instrument": "Regulation (EU) 2024/1689, Article 51(2)",
        "flop": 1e25,
        "status": "in force",
        "applies_to": "General-purpose AI models placed on the EU market",
        "consequence": (
            "Presumption of systemic risk, bringing model evaluation, adversarial testing, "
            "incident reporting and cybersecurity obligations."
        ),
        "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "note": (
            "A rebuttable presumption rather than a hard line: a developer can argue its "
            "model does not carry systemic risk despite the compute, and the Commission can "
            "designate a model that falls below it."
        ),
    },
    {
        "jurisdiction": "United States (California)",
        "instrument": "SB 53, Transparency in Frontier Artificial Intelligence Act",
        "flop": 1e26,
        "status": "in force",
        "applies_to": "Frontier developers training models above the threshold",
        "consequence": (
            "Duty to publish a frontier AI framework and transparency report, and to report "
            "critical safety incidents to the state."
        ),
        "url": "https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53",
        "note": (
            "Counts the initial training run plus later fine-tuning and material "
            "modification, so it is a cumulative figure rather than a single-run one. Larger "
            "obligations attach above an annual revenue threshold as well."
        ),
    },
    {
        "jurisdiction": "United States (federal)",
        "instrument": "Executive Order 14110, section 4.2",
        "flop": 1e26,
        "status": "revoked",
        "applies_to": "Developers of dual-use foundation models",
        "consequence": "Reporting of training runs, results of red-team testing and security measures.",
        "url": "https://www.federalregister.gov/executive-order/14110",
        "note": (
            "The first compute threshold in any official instrument, revoked in January 2025. "
            "Included because it is still widely quoted as current, and because California "
            "later adopted the same number."
        ),
    },
    {
        "jurisdiction": "United States (California)",
        "instrument": "SB 1047, Safe and Secure Innovation for Frontier AI Models Act",
        "flop": 1e26,
        "status": "vetoed",
        "applies_to": "Developers of covered models above the threshold and above $100m training cost",
        "consequence": "Would have required a safety protocol, third-party audit and a shutdown capability.",
        "url": "https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB1047",
        "note": (
            "Vetoed in September 2024. Its successor, SB 53, kept the compute threshold and "
            "dropped the audit and shutdown requirements."
        ),
    },
    {
        "jurisdiction": "United States (New York)",
        "instrument": "RAISE Act, Responsible AI Safety and Education Act",
        "flop": 1e26,
        "status": "enacted",
        "applies_to": (
            "Frontier developers with over $500 million in annual revenue, for models trained "
            "above the threshold and above $100m in compute cost"
        ),
        "consequence": (
            "Duty to publish safety and security protocols and to report safety incidents "
            "to the state."
        ),
        "applies_from": "2027-01-01",
        "url": "https://www.nysenate.gov/legislation/bills/2025/S6953/amendment/B",
        "note": (
            "Signed in December 2025 and amended in March 2026 to track California's SB 53. "
            "It applies from 1 January 2027, so it is counted here as enacted rather than in "
            "force."
        ),
    },
]


def build_frameworks() -> list[dict]:
    records = []
    for entry in DEVELOPERS:
        if entry["halt"] not in HALT:
            raise ValueError(f"{entry['developer']}: unknown halt value {entry['halt']!r}")
        if not entry["url"].startswith("https://"):
            raise ValueError(f"{entry['developer']}: citation must be an https URL")
        if bool(entry["framework"]) != (entry["halt"] != "no-framework"):
            raise ValueError(
                f"{entry['developer']}: a developer with a framework cannot be marked "
                f"no-framework, and one without cannot be marked anything else"
            )
        records.append(
            {
                **entry,
                "halt_meaning": HALT[entry["halt"]],
                "reviewed": FRAMEWORKS_REVIEWED,
                "source_id": FRAMEWORK_SOURCE,
            }
        )
    return records


def build_thresholds() -> list[dict]:
    records = []
    for entry in THRESHOLDS:
        if entry["status"] not in ("in force", "enacted", "revoked", "vetoed", "proposed"):
            raise ValueError(f"{entry['instrument']}: unknown status {entry['status']!r}")
        if not entry["url"].startswith("https://"):
            raise ValueError(f"{entry['instrument']}: citation must be an https URL")
        if (entry["status"] == "enacted") != bool(entry.get("applies_from")):
            raise ValueError(
                f"{entry['instrument']}: an enacted threshold needs the date it applies "
                f"from, and only an enacted one carries it"
            )
        records.append(
            {
                "applies_from": None,
                **entry,
                # Carried alongside the float so a page never has to reconstruct the
                # exponent for display and get it subtly wrong.
                "exponent": round(math.log10(entry["flop"])),
                "reviewed": THRESHOLDS_REVIEWED,
                "source_id": THRESHOLD_SOURCE,
            }
        )
    return sorted(records, key=lambda r: (r["status"] != "in force", r["flop"]))


def run(offline: bool = False) -> None:
    """Hand-written, so there is nothing to fetch and offline changes nothing."""
    write_dataset(
        "safety-frameworks",
        build_frameworks(),
        source_ids=[FRAMEWORK_SOURCE],
        unit=None,
        notes=(
            f"Our own reading of each developer's published frontier safety framework, "
            f"reviewed {FRAMEWORKS_REVIEWED}. Self-assessment under self-written frameworks "
            f"with no common scale and no external audit. Not a ranking."
        ),
        retrieved=review_stamp(FRAMEWORKS_REVIEWED),
    )
    write_dataset(
        "legal-thresholds",
        build_thresholds(),
        source_ids=[THRESHOLD_SOURCE],
        unit="FLOP of training compute",
        notes=(
            f"Every training-compute threshold written into law, executive action or an "
            f"official policy document, reviewed {THRESHOLDS_REVIEWED}. Whether a model "
            f"crosses one is arithmetic on compute estimates and is not a legal finding."
        ),
        retrieved=review_stamp(THRESHOLDS_REVIEWED),
    )


def _self_check() -> None:
    frameworks = build_frameworks()
    thresholds = build_thresholds()

    assert len(frameworks) >= 6, f"only {len(frameworks)} developers indexed"
    assert len(thresholds) >= 4, f"only {len(thresholds)} thresholds indexed"

    # The absence is the point. An index of frameworks that only lists developers
    # who wrote one answers a different and much less interesting question.
    without = [r for r in frameworks if not r["framework"]]
    assert without, "no developer is listed as having no framework, which cannot be right"

    # Exactly one threshold is in force in a law that applies market-wide. If a
    # second ever appears, the pages that say "the only one" need rewriting, and
    # this is where that gets noticed.
    in_force = [t for t in thresholds if t["status"] == "in force"]
    assert len(in_force) == 2, (
        f"{len(in_force)} thresholds now in force: {[t['instrument'] for t in in_force]}. "
        f"Check the pages that describe how many there are."
    )
    assert any(t["flop"] == 1e25 for t in in_force), "the EU threshold is missing"

    # An exponent that does not match its float would put the wrong number on a
    # chart axis while the tooltip stayed right.
    for record in thresholds:
        # float() on the int power, not the other way round: 10**25 is an exact
        # integer and 1e25 is the nearest double to it, and those two are not
        # equal in Python. Comparing them directly fails on correct data.
        assert float(10 ** record["exponent"]) == record["flop"], record["instrument"]

    # The validator has to reject a developer marked as having no framework while
    # naming one, because that pair is what a half-finished edit looks like.
    DEVELOPERS.append(
        {
            "developer": "Test", "framework": "Something", "scale": None, "levels": 0,
            "domains": [], "external": False, "halt": "no-framework", "since": None,
            "url": "https://example.com", "note": "",
        }
    )
    try:
        build_frameworks()
    except ValueError:
        pass
    else:
        raise AssertionError("build_frameworks accepted a framework marked no-framework")
    finally:
        DEVELOPERS.pop()

    print(
        f"build_frontier_index self-check passed: {len(frameworks)} developers "
        f"({len(without)} with no framework), {len(thresholds)} thresholds, "
        f"{len(in_force)} in force"
    )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    elif "--check-links" in sys.argv:
        entries = [(r["developer"], r["url"]) for r in build_frameworks()]
        entries += [(r["instrument"][:40], r["url"]) for r in build_thresholds()]
        raise SystemExit(1 if check_links(entries) else 0)
    else:
        _self_check()
        run()
