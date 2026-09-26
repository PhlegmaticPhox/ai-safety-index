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
# re-read on 25 September and New York's RAISE Act added. Every framework was
# re-read on 26 September 2026 from the version each developer publishes now:
# Anthropic RSP v3.4 (8 July 2026), OpenAI Preparedness Framework v2 (15 April
# 2025, still its latest), Google DeepMind FSF v3.1 (17 April 2026), Meta
# Advanced AI Scaling Framework v2 (April 2026), Microsoft Frontier Governance
# Framework (February 2026), Amazon (17 September 2026 revision) and xAI Frontier
# Artificial Intelligence Framework (30 June 2026). METR's list of published
# policies, read the same day, carries no later version of any of them and
# nothing from DeepSeek.
FRAMEWORKS_REVIEWED = "2026-09-26"
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

# One label per kind of risk, whatever each developer calls it, because
# /alignment/ counts the distinct labels and eight vocabularies would count the
# same risk several times.
#
#   CBRN             chemical and biological weapons, with radiological and
#                    nuclear where the framework names them
#   cyber            offensive cyber operations
#   loss of control  misalignment, sabotage, undermining human control
#   AI R&D           automating AI research, or expert work generally
#                    (Microsoft's "advanced autonomy")
#   manipulation     harmful manipulation, formerly called persuasion
#
# Only a domain the framework sets a threshold or tracked level for is listed;
# research categories without one are not.
DOMAINS = {"CBRN", "cyber", "loss of control", "AI R&D", "manipulation"}

DEVELOPERS = [
    {
        "developer": "Anthropic",
        "framework": "Responsible Scaling Policy",
        "scale": "Four capability thresholds, each paired with recommended mitigations; AI Safety Levels now name present safeguards only",
        "levels": 0,
        "domains": ["CBRN", "loss of control", "AI R&D"],
        "external": True,
        "halt": "qualified",
        "since": 2023,
        "url": "https://www-cdn.anthropic.com/files/4zrzovbb/website/0bacdc8440ea96e62a8766d99ebe1d4eea6d5f3a.pdf",
        "note": (
            "Rewritten as version 3 in February 2026; version 3.4 took effect on 8 July 2026. "
            "The earlier commitment not to train or deploy without adequate safeguards is "
            "gone: it commits to delay development and deployment only while Anthropic leads "
            "or its competitors have strong safety measures, and otherwise publishes Risk "
            "Reports with a risk-benefit determination by its chief executive and Responsible "
            "Scaling Officer. It no longer has a cyber threshold."
        ),
        # v3.4. Thresholds (section 1): non-novel and novel chemical/biological
        # weapons, misaligned AI in high-stakes settings, automated R&D; no cyber.
        # halt: "we cannot unilaterally and unconditionally commit to staying in
        # line with the industry-wide recommendations" (section 1); "We will delay
        # AI development and deployment as needed" only in the two competitor
        # scenarios of Appendix A; "The CEO and RSO will make the ultimate
        # determination" (3.4). external: a full external review of Risk Reports on
        # highly capable models when significantly redacted (3.6), and an annual
        # third-party review of procedural compliance (4.7).
    },
    {
        "developer": "OpenAI",
        "framework": "Preparedness Framework",
        "scale": "Capability thresholds: High and Critical",
        "levels": 2,
        "domains": ["CBRN", "cyber", "AI R&D"],
        "external": True,
        "halt": "yes",
        "since": 2023,
        "url": "https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf",
        "note": (
            "Version 2, April 2025, is still the published version. OpenAI's Frontier "
            "Governance Framework of May 2026 sets out how it meets EU and Californian law "
            "and leaves this as its own standard. Three tracked categories at two thresholds: "
            "persuasion was dropped in 2025, and long-range autonomy and nuclear risk are "
            "research categories without thresholds. At a Critical threshold it commits to "
            "halt further development until safeguards are specified."
        ),
        # v2. Tracked: biological and chemical, cybersecurity, AI self-improvement.
        # "we are removing terms 'low' and 'medium' from the Framework" (1.1).
        # halt: "Until we have specified safeguards and security controls that
        # would meet a Critical standard, halt further development" (Table 1), and
        # "We won't deploy these very capable models until we've built safeguards"
        # (introduction). external: "OpenAI will work with third-parties to
        # independently evaluate models" where it deems deeper testing warranted
        # (5.2). The May 2026 Frontier Governance Framework is a compliance
        # document and states that the Preparedness Framework continues.
    },
    {
        "developer": "Google DeepMind",
        "framework": "Frontier Safety Framework",
        "scale": "Critical Capability Levels per domain, with lower Tracked Capability Levels for some",
        "levels": 0,
        "domains": ["CBRN", "cyber", "manipulation", "AI R&D", "loss of control"],
        "external": False,
        "halt": "qualified",
        "since": 2024,
        "url": "https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3-1.pdf",
        "note": (
            "Version 3.1 took effect on 17 April 2026. Adds Tracked Capability Levels below "
            "the critical ones, for CBRN and for a domain that now merges machine-learning "
            "R&D with misalignment. Risk acceptance weighs what other publicly available "
            "models can do, and for misuse risks applies to external deployment only, not "
            "to internal use or further development."
        ),
        # v3.1. Domains (1.2): CBRN, cyber, harmful manipulation, and ML R&D and
        # misalignment, whose Stealth and Situational Awareness TCL concerns a model
        # "significantly undermining human control". halt: a model "will be deemed
        # to pose an acceptable level of residual risk" if mitigations bring risk to
        # an acceptable level, weighing "what capabilities and mitigations are
        # available on other publicly available models"; "required only for
        # external deployment, not internal deployment or further development"
        # (1.3.5). external: "involving internal and external experts as needed"
        # (1.3.3), which is not a commitment.
    },
    {
        "developer": "Meta",
        "framework": "Advanced AI Scaling Framework",
        "scale": "Risk thresholds: moderate or lower, high, critical",
        "levels": 3,
        "domains": ["CBRN", "cyber", "loss of control"],
        "external": False,
        "halt": "yes",
        "since": 2025,
        "url": "https://ai.meta.com/static-resource/Meta_Advanced-AI-Scaling-Framework-v2",
        "note": (
            "Version 2, April 2026, renamed from the Frontier AI Framework. The critical tier "
            "changed from Stop to Develop with Mitigations, so every tier now permits "
            "development and deployment once mitigations are validated to bring risk down to "
            "moderate. Adds loss of control, and covers any model trained with 1e26 FLOP or "
            "more."
        ),
        # v2. Domains (section 1): chemical and biological, cybersecurity, loss of
        # control; nuclear, radiological and physical autonomy are emerging areas
        # without thresholds. halt: "Proceed with deployment of the Frontier AI
        # only if sufficient mitigations are defined, implemented and validated to
        # reduce risk to that of a moderate or lower model" (Table 1), and the
        # change log: "Critical threshold changed from 'Stop' to 'Develop with
        # Mitigations.'" external: works with external experts "where appropriate";
        # no commitment.
    },
    {
        "developer": "Microsoft",
        "framework": "Frontier Governance Framework",
        "scale": "Risk levels per capability: low, medium, high, critical",
        "levels": 4,
        "domains": ["CBRN", "cyber", "AI R&D", "loss of control", "manipulation"],
        "external": True,
        "halt": "yes",
        "since": 2025,
        "url": "https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/Frontier-Governance-Framework-Feb-2026.pdf",
        "note": (
            "Revised in February 2026 to align with the EU Code of Practice and the "
            "Californian and New York frontier AI laws, adding loss of control and harmful "
            "manipulation. Commits to pause development and deployment of a model whose risk "
            "cannot be sufficiently mitigated. Covers models in scope of those laws, and "
            "Microsoft's substantial fine-tunes of other developers' models."
        ),
        # February 2026. halt: "If, during the implementation of this framework, we
        # identify a risk we cannot sufficiently mitigate, we will pause development
        # and deployment until the point at which mitigation practices evolve to meet
        # the risk" (section 4). external: "We engage qualified third parties to
        # conduct evaluations in ways that are appropriate to the risk profile of the
        # model" (section 3). Advanced autonomy, "including AI research and
        # development", is coded AI R&D.
    },
    {
        "developer": "Amazon",
        "framework": "Frontier Model Safety Framework",
        "scale": "Critical capability thresholds",
        "levels": 0,
        "domains": ["CBRN", "cyber", "loss of control", "manipulation"],
        "external": True,
        "halt": "yes",
        "since": 2025,
        "url": "https://www.amazon.science/publications/amazons-frontier-model-safety-framework",
        "note": (
            "Revised in September 2026. Names four critical risk domains, adding harmful "
            "manipulation, and commits not to deploy a model that meets a threshold until "
            "safeguards appropriately mitigate the risks."
        ),
        # 17 September 2026 revision, read 26 September. halt: "we will not deploy
        # the model until safeguards appropriately mitigate the risks" (section 2).
        # external: "We will therefore use a range of internal and external
        # evaluation approaches" (section 2), alongside red teaming by outside
        # vendors.
    },
    {
        "developer": "xAI",
        "framework": "Frontier Artificial Intelligence Framework",
        "scale": "Risk tiers per domain, not published",
        "levels": 0,
        "domains": ["CBRN", "cyber", "loss of control", "manipulation"],
        "external": False,
        "halt": "yes",
        "since": 2025,
        "url": "https://media.x.ai/v1/website/xai-frontier-artificial-intelligence-framework-30-june-2026-99c40684.pdf",
        "note": (
            "Effective 30 June 2026, replacing the 2025 Risk Management Framework, and "
            "written in the terms of the EU Code of Practice. Commits to proceed with "
            "development or release only if systemic risks are determined acceptable. Refers "
            "to risk tiers and benchmarks without publishing either."
        ),
        # 30 June 2026. Domains (2.1): CBRN, offensive cybersecurity, loss of
        # control, harmful manipulation. halt: "xAI will only proceed with the
        # development, the making available on the market, and/or the use of the
        # model, if the systemic risks stemming from the model are determined to be
        # acceptable" (2.3). No thresholds are defined; "we review the risk tiers
        # for each systemic risk category". external: none committed.
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
        unknown = set(entry["domains"]) - DOMAINS
        if unknown:
            raise ValueError(
                f"{entry['developer']}: domain label(s) {sorted(unknown)} are not in DOMAINS. "
                f"Map the developer's term onto an existing label, or add one on purpose."
            )
        records.append(
            {
                **entry,
                "halt_meaning": HALT[entry["halt"]],
                "reviewed": entry.get("reviewed", FRAMEWORKS_REVIEWED),
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

    # A domain label outside the vocabulary would count as a new risk domain on
    # /alignment/, which is how "persuasion" and "manipulation" became two.
    DEVELOPERS[0]["domains"].append("persuasion")
    try:
        build_frameworks()
    except ValueError:
        pass
    else:
        raise AssertionError("build_frameworks accepted a domain label outside DOMAINS")
    finally:
        DEVELOPERS[0]["domains"].pop()

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
