"""AI law and policy index, jurisdiction by jurisdiction. Australia first.

Why this is written by hand rather than scraped: the two established policy
trackers, OECD.AI and IAPP, are protected by the EU sui generis database right
on top of copyright, and bulk-extracting either is the fastest route to a
letter. Reading the primary instruments and writing our own index avoids that
entirely, and the result is ours to license CC BY 4.0.

Australia is first because it is where this site is written, and because the
Australian position is genuinely interesting: no AI statute, no AI regulator,
and a large body of existing law that already applies to AI without mentioning
it. An index that only listed instruments with "AI" in the title would show
almost nothing and mislead anyone who read it.

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
]

AUSTRALIA = [
    # --- Statutes ---
    {
        "title": "Privacy Act 1988",
        "force": "statute",
        "year": 1988,
        "body": "Parliament of Australia",
        "topics": ["privacy", "transparency"],
        "url": "https://www.legislation.gov.au/C2004A03712/latest/text",
        "note": (
            "The main constraint on AI systems that handle personal information. The "
            "Australian Privacy Principles apply to collection, use and disclosure "
            "regardless of whether a model is involved, which is why an Australian AI "
            "compliance question is usually a privacy question first."
        ),
    },
    {
        "title": "Privacy and Other Legislation Amendment Act 2024",
        "force": "statute",
        "year": 2024,
        "body": "Parliament of Australia",
        "topics": ["privacy", "transparency"],
        "url": "https://www.legislation.gov.au/C2024A00125/asmade/text",
        "note": (
            "The first tranche of reform from the Privacy Act Review. Creates a statutory "
            "tort for serious invasions of privacy, and requires privacy policies to "
            "disclose where personal information is used in automated decisions that "
            "significantly affect someone. The automated-decision transparency duty is "
            "the closest thing Australia has to an AI transparency obligation, and it "
            "commences in December 2026."
        ),
    },
    {
        "title": "Online Safety Act 2021",
        "force": "statute",
        "year": 2021,
        "body": "Parliament of Australia",
        "topics": ["safety", "children"],
        "url": "https://www.legislation.gov.au/C2021A00076/latest/text",
        "note": (
            "Gives the eSafety Commissioner removal powers and the ability to register "
            "industry codes and make standards. The codes and standards made under it now "
            "reach generative AI services, which is how Australia regulates AI-generated "
            "harmful material without an AI statute."
        ),
    },
    {
        "title": "Criminal Code Amendment (Deepfake Sexual Material) Act 2024",
        "force": "statute",
        "year": 2024,
        "body": "Parliament of Australia",
        "topics": ["safety", "children"],
        "url": "https://www.legislation.gov.au/C2024A00081/asmade/text",
        "note": (
            "Criminalises transmitting sexual material depicting an adult without consent, "
            "including material that has been generated or altered. One of the few "
            "Australian statutes written with generative models in view."
        ),
    },
    {
        "title": "Competition and Consumer Act 2010, Schedule 2 (Australian Consumer Law)",
        "force": "statute",
        "year": 2010,
        "body": "Parliament of Australia",
        "topics": ["consumer"],
        "url": "https://www.legislation.gov.au/C2004A00109/latest/text",
        "note": (
            "Misleading or deceptive conduct and the consumer guarantees apply to claims "
            "made about AI products and to products that fail because of them. The ACCC "
            "has been explicit that overstating what a model does is ordinary consumer law "
            "territory, with no AI-specific provision needed."
        ),
    },
    {
        "title": "Copyright Act 1968",
        "force": "statute",
        "year": 1968,
        "body": "Parliament of Australia",
        "topics": ["copyright"],
        "url": "https://www.legislation.gov.au/C1968A00063/latest/text",
        "note": (
            "Australia has fair dealing for specified purposes, not fair use, and no text "
            "and data mining exception. Training on copyright material in Australia has a "
            "narrower set of defences available than in the United States, which is the "
            "central question the Copyright and AI Reference Group was set up to examine."
        ),
    },
    {
        "title": "Security of Critical Infrastructure Act 2018",
        "force": "statute",
        "year": 2018,
        "body": "Parliament of Australia",
        "topics": ["security"],
        "url": "https://www.legislation.gov.au/C2018A00029/latest/text",
        "note": (
            "Risk management obligations for responsible entities in eleven critical "
            "sectors. Where an AI system is part of a critical infrastructure asset, the "
            "hazard categories and the reporting duties apply to it like anything else."
        ),
    },
    {
        "title": "Therapeutic Goods Act 1989",
        "force": "statute",
        "year": 1989,
        "body": "Parliament of Australia",
        "topics": ["health", "safety"],
        "url": "https://www.legislation.gov.au/C2004A03952/latest/text",
        "note": (
            "Clinical decision-support and diagnostic software can be a medical device and "
            "require TGA inclusion in the Register. This is the one area where an "
            "Australian AI developer faces pre-market approval rather than after-the-fact "
            "enforcement."
        ),
    },
    {
        "title": "Corporations Act 2001",
        "force": "statute",
        "year": 2001,
        "body": "Parliament of Australia",
        "topics": ["finance", "government use"],
        "url": "https://www.legislation.gov.au/C2004A00818/latest/text",
        "note": (
            "Directors' duties of care and diligence, and the obligation on financial "
            "services licensees to provide services efficiently, honestly and fairly, both "
            "reach board-level decisions about deploying AI. ASIC has said so directly."
        ),
    },
    {
        "title": "Digital ID Act 2024",
        "force": "statute",
        "year": 2024,
        "body": "Parliament of Australia",
        "topics": ["privacy", "security"],
        "url": "https://www.legislation.gov.au/C2024A00025/asmade/text",
        "note": (
            "Accreditation for digital identity providers, with restrictions on biometric "
            "information and on using it for anything beyond verification. Relevant to any "
            "face-matching or liveness system operating in the accredited scheme."
        ),
    },
    # --- Binding on government ---
    {
        "title": "Policy for the responsible use of AI in government",
        "force": "agency-binding",
        "year": 2024,
        "body": "Digital Transformation Agency",
        "topics": ["government use", "transparency"],
        "url": "https://www.digital.gov.au/policy/ai/policy",
        "note": (
            "Mandatory for non-corporate Commonwealth entities from September 2024. "
            "Requires an accountable official and a public transparency statement. This is "
            "the most concrete binding AI obligation in Australia, and it binds the "
            "government rather than the market."
        ),
    },
    {
        "title": "National framework for the assurance of artificial intelligence in government",
        "force": "agency-binding",
        "year": 2024,
        "body": "Data and Digital Ministers Meeting",
        "topics": ["government use"],
        "url": "https://www.finance.gov.au/publications/national-framework-assurance-artificial-intelligence-government",
        "note": (
            "Agreed by Commonwealth, state and territory ministers. Applies the AI Ethics "
            "Principles to government use and sets a common assurance approach across "
            "jurisdictions, which matters because most public-facing AI in Australia is "
            "deployed by states, not the Commonwealth."
        ),
    },
    # --- Voluntary ---
    {
        "title": "Voluntary AI Safety Standard",
        "force": "voluntary",
        "year": 2024,
        "body": "Department of Industry, Science and Resources",
        "topics": ["safety", "transparency"],
        "url": "https://www.industry.gov.au/publications/voluntary-ai-safety-standard",
        "note": (
            "Ten guardrails covering accountability, risk management, testing, human "
            "oversight and disclosure. Written to line up with the mandatory guardrails "
            "that were proposed at the same time, so an organisation that adopts it is "
            "positioned for legislation that has not arrived."
        ),
    },
    {
        "title": "Australia's AI Ethics Principles",
        "force": "voluntary",
        "year": 2019,
        "body": "Department of Industry, Science and Resources",
        "topics": ["safety", "discrimination"],
        "url": "https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles",
        "note": (
            "Eight principles, voluntary since 2019. Their practical significance is that "
            "later binding government policy adopts them by reference, which gives them "
            "force inside the public sector that they do not have outside it."
        ),
    },
    {
        "title": "National AI Capability Plan",
        "force": "voluntary",
        "year": 2025,
        "body": "Department of Industry, Science and Resources",
        "topics": ["government use"],
        "url": "https://www.industry.gov.au/publications/national-ai-capability-plan",
        "note": (
            "The economic strategy rather than the regulatory one: skills, compute, "
            "adoption and sovereign capability. Included here because it sets the policy "
            "frame the regulatory decisions are being made inside."
        ),
    },
    # --- Proposals ---
    {
        "title": "Proposals paper: introducing mandatory guardrails for AI in high-risk settings",
        "force": "proposal",
        "year": 2024,
        "body": "Department of Industry, Science and Resources",
        "topics": ["safety", "transparency"],
        "url": "https://consult.industry.gov.au/ai-mandatory-guardrails",
        "note": (
            "Consulted on in late 2024. Proposed a risk-based regime with ten mandatory "
            "guardrails and canvassed three options for giving them effect: a new AI act, "
            "framework legislation, or amendments to existing law. Nothing has been "
            "legislated, which is the single most important fact in this index."
        ),
    },
    # --- Regulator guidance ---
    {
        "title": "Guidance on privacy and the use of commercially available AI products",
        "force": "regulator-guidance",
        "year": 2024,
        "body": "Office of the Australian Information Commissioner",
        "topics": ["privacy"],
        "url": "https://www.oaic.gov.au/privacy/privacy-guidance-for-organisations-and-government-agencies/guidance-on-privacy-and-the-use-of-commercially-available-ai-products",
        "note": (
            "What the Australian Privacy Principles require of an organisation buying in a "
            "model rather than building one. Includes the OAIC's position that entering "
            "personal information into a public generative AI tool is a disclosure."
        ),
    },
    {
        "title": "Guidance on privacy and developing and training generative AI models",
        "force": "regulator-guidance",
        "year": 2024,
        "body": "Office of the Australian Information Commissioner",
        "topics": ["privacy", "copyright"],
        "url": "https://www.oaic.gov.au/privacy/privacy-guidance-for-organisations-and-government-agencies/guidance-on-privacy-and-developing-and-training-generative-ai-models",
        "note": (
            "The regulator's view on scraping and on training with personal information, "
            "including that publicly available does not mean freely usable under the "
            "Privacy Act. Directly relevant to anyone training on Australian web data."
        ),
    },
    {
        "title": "REP 798 Beware the gap: governance arrangements in the face of AI innovation",
        "force": "regulator-guidance",
        "year": 2024,
        "body": "Australian Securities and Investments Commission",
        "topics": ["finance", "consumer"],
        "url": "https://asic.gov.au/regulatory-resources/find-a-document/reports/rep-798-beware-the-gap-governance-arrangements-in-the-face-of-ai-innovation/",
        "note": (
            "A review of AI use across 23 licensees which found governance lagging "
            "deployment. ASIC's position is that existing obligations already bite and "
            "that boards cannot wait for AI-specific law."
        ),
    },
    {
        "title": "Prudential Standard CPS 230 Operational Risk Management",
        "force": "delegated",
        "year": 2023,
        "body": "Australian Prudential Regulation Authority",
        "topics": ["finance", "security"],
        "url": "https://www.apra.gov.au/sites/default/files/2023-07/Prudential%20Standard%20CPS%20230%20Operational%20Risk%20Management%20-%20clean.pdf",
        "note": (
            "Binding on APRA-regulated entities from July 2025. Requires identification of "
            "critical operations and management of material service provider risk, which "
            "captures dependence on a third-party model provider."
        ),
    },
    {
        "title": "Copyright and Artificial Intelligence Reference Group",
        "force": "review",
        "year": 2023,
        "body": "Attorney-General's Department",
        "topics": ["copyright"],
        "url": "https://www.ag.gov.au/rights-and-protections/copyright/copyright-and-artificial-intelligence-reference-group",
        "note": (
            "The standing forum on whether Australian copyright law needs changing for AI "
            "training and AI output. No statutory change has followed, so the Copyright Act "
            "as it stands remains the answer."
        ),
    },
    # --- Reviews and inquiries ---
    {
        "title": "Select Committee on Adopting Artificial Intelligence, final report",
        "force": "review",
        "year": 2024,
        "body": "Senate of Australia",
        "topics": ["safety", "consumer", "discrimination"],
        "url": "https://www.aph.gov.au/Parliamentary_Business/Committees/Senate/Adopting_Artificial_Intelligence_AI/AdoptingAI/Report",
        "note": (
            "Recommended that general-purpose models be declared high-risk and that "
            "Australia legislate a dedicated AI act. The government has not adopted the "
            "recommendation, and the gap between this report and the statute book is worth "
            "understanding before reading Australian AI coverage."
        ),
    },
    {
        "title": "Royal Commission into the Robodebt Scheme, final report",
        "force": "review",
        "year": 2023,
        "body": "Commonwealth of Australia",
        "topics": ["government use", "transparency"],
        "url": "https://robodebt.royalcommission.gov.au/publications/report",
        "note": (
            "Not an AI inquiry, and the most important document here for understanding "
            "Australian automated decision-making. An automated income-averaging scheme "
            "unlawfully raised debts against hundreds of thousands of people. Its "
            "recommendations on transparency and on a legislative basis for automated "
            "decisions are the reason government AI policy here is as cautious as it is."
        ),
    },
    {
        "title": "Privacy Act Review Report",
        "force": "review",
        "year": 2023,
        "body": "Attorney-General's Department",
        "topics": ["privacy", "transparency"],
        "url": "https://www.ag.gov.au/rights-and-protections/publications/privacy-act-review-report",
        "note": (
            "116 proposals, agreed or agreed in principle by the government in 2023. The "
            "2024 amendment act delivered the first tranche; the proposals on automated "
            "decisions, a fair and reasonable test, and small business exemptions are still "
            "outstanding and would change the AI picture substantially."
        ),
    },
    # --- State ---
    {
        "title": "NSW Artificial Intelligence Assessment Framework",
        "force": "agency-binding",
        "year": 2024,
        "body": "Digital NSW",
        "topics": ["government use"],
        "url": "https://www.digital.nsw.gov.au/policy/artificial-intelligence/nsw-artificial-intelligence-assessment-framework",
        "note": (
            "Mandatory for NSW government AI projects and the most developed state-level "
            "instrument. Most public-facing government AI in Australia is deployed by "
            "states, so Commonwealth policy alone does not describe what citizens meet."
        ),
    },
]

JURISDICTIONS = {
    "australia": {
        "name": "Australia",
        "code": "AUS",
        "summary": (
            "No AI statute and no AI regulator. Australia governs AI through law that does "
            "not mention it: privacy, consumer, online safety, therapeutic goods, "
            "corporations and criminal law. The one genuinely binding AI-specific "
            "obligation applies to Commonwealth agencies rather than to the market. "
            "Mandatory guardrails for high-risk AI were proposed in 2024 and have not been "
            "legislated."
        ),
        "instruments": AUSTRALIA,
    },
}


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
            f"Our own index of instruments relevant to AI, reviewed {REVIEWED}. Each entry "
            "links to the primary source and is tagged by how binding it is, because a "
            "voluntary standard and an Act of Parliament are not the same kind of object "
            "however similar their contents look. Not legal advice, not a compliance "
            "checklist, and not exhaustive. Instruments that never mention AI are included "
            "where they apply to it, which for Australia is most of the list."
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

    print(f"build_policy_index self-check passed: {len(records)} instruments, {len(forces)} force levels")


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
