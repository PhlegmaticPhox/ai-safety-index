"""The instrument lists behind the AI Law and Policy Index.

Separated from `build_policy_index.py` so that the validation, the self-check and
the link prober stay readable next to each other rather than at the bottom of two
thousand lines of data. Nothing here executes: it is a source list, and every
entry carries the link it was read from.

Each entry is:

    title   as the instrument calls itself, including its number
    force   one of the levels in build_policy_index.FORCE
    year    when it was made, not when it commences
    body    who made it
    topics  from build_policy_index.TOPICS
    url     the primary source, https only
    note    what it actually does, and what a reader would get wrong about it

Selection rule, applied to every jurisdiction: an instrument belongs here if it
constrains or authorises AI systems in practice, whether or not it mentions AI.
An index of things with "AI" in the title would be four entries long for most of
these jurisdictions and would badly mislead anyone who read it.
"""

from __future__ import annotations

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
    {
        "title": "Australian AI Safety Institute",
        "force": "agency-binding",
        "year": 2025,
        "body": "Department of Industry, Science and Resources",
        "topics": ["safety"],
        "url": "https://www.industry.gov.au/science-technology-and-innovation/technology/artificial-intelligence/ai-safety-institute",
        "note": (
            "Announced in November 2025 and operating from early 2026, with the Australian "
            "Signals Directorate as a technical partner. It began testing frontier models in "
            "July 2026."
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
            "framework legislation, or amendments to existing law. The December 2025 "
            "National AI Plan set it aside in favour of existing law. In July 2026 the "
            "government announced it would legislate Australian Standards for AI instead, "
            "with legislation expected in 2027. Nothing has been legislated, which is the "
            "single most important fact in this index."
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

# ---------------------------------------------------------------------------
# European Union, coded at bloc level. The AI Act is a regulation, so it applies
# directly in all 27 member states without transposition.
# ---------------------------------------------------------------------------
EU = [
    {
        "title": "Regulation (EU) 2024/1689 (Artificial Intelligence Act)",
        "force": "statute",
        "year": 2024,
        "body": "European Parliament and Council",
        "topics": ["safety", "transparency", "labelling", "consumer"],
        "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        "note": (
            "The only horizontal AI statute in force anywhere. Bans a short list of "
            "practices, imposes conformity assessment on high-risk uses, sets transparency "
            "duties on systems people interact with, and adds obligations for "
            "general-purpose models above 1e25 FLOP of training compute. It applies in "
            "stages rather than at once, and those stages have since moved."
        ),
    },
    {
        "title": "Digital Omnibus on AI",
        "force": "statute",
        "year": 2026,
        "body": "European Parliament and Council",
        "topics": ["safety", "transparency"],
        "url": "https://digital-strategy.ec.europa.eu/en/policies/digital-omnibus",
        "note": (
            "Amends the AI Act, in force from July 2026, six days before the high-risk "
            "obligations were due to bite. Stand-alone high-risk systems move to December "
            "2027 and systems embedded in regulated products to August 2028. The Article 50 "
            "transparency duties were not delayed. Treat any compliance date published "
            "before July 2026 as out of date."
        ),
    },
    {
        "title": "Regulation (EU) 2016/679 (General Data Protection Regulation)",
        "force": "statute",
        "year": 2016,
        "body": "European Parliament and Council",
        "topics": ["privacy", "transparency"],
        "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "note": (
            "Predates the AI Act and reaches further in practice. Article 22 restricts "
            "decisions based solely on automated processing that produce legal or similarly "
            "significant effects, and it is the provision most European automated-decision "
            "disputes are actually fought under."
        ),
    },
    {
        "title": "Regulation (EU) 2022/2065 (Digital Services Act)",
        "force": "statute",
        "year": 2022,
        "body": "European Parliament and Council",
        "topics": ["safety", "transparency", "elections"],
        "url": "https://eur-lex.europa.eu/eli/reg/2022/2065/oj",
        "note": (
            "Systemic-risk assessment and mitigation duties on very large platforms and "
            "search engines, explicitly including risks from recommender and generative "
            "features. Where a model ships inside a large platform, this usually binds "
            "before the AI Act does."
        ),
    },
    {
        "title": "Directive (EU) 2024/2853 on liability for defective products",
        "force": "statute",
        "year": 2024,
        "body": "European Parliament and Council",
        "topics": ["liability", "consumer", "safety"],
        "url": "https://eur-lex.europa.eu/eli/dir/2024/2853/oj",
        "note": (
            "Brings software and AI systems inside the product liability regime and eases "
            "the burden of proof where a claimant could not reasonably be expected to "
            "explain how a complex system failed. The separate AI Liability Directive was "
            "withdrawn in 2025, so this is what remains."
        ),
    },
    {
        "title": "Directive (EU) 2019/790 on copyright in the Digital Single Market",
        "force": "statute",
        "year": 2019,
        "body": "European Parliament and Council",
        "topics": ["copyright"],
        "url": "https://eur-lex.europa.eu/eli/dir/2019/790/oj",
        "note": (
            "Article 4 permits text and data mining of lawfully accessible works unless the "
            "rightsholder reserved the right in a machine-readable way. That reservation is "
            "the legal basis for most European objections to training on web data."
        ),
    },
    {
        "title": "European AI Office",
        "force": "agency-binding",
        "year": 2024,
        "body": "European Commission",
        "topics": ["safety", "government use"],
        "url": "https://digital-strategy.ec.europa.eu/en/policies/ai-office",
        "note": (
            "Supervises general-purpose model obligations directly rather than leaving them "
            "to national authorities. It is the only body anywhere with statutory "
            "supervisory powers aimed specifically at frontier models."
        ),
    },
    {
        "title": "General-Purpose AI Code of Practice",
        "force": "voluntary",
        "year": 2025,
        "body": "European Commission and independent experts",
        "topics": ["safety", "transparency", "copyright"],
        "url": "https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai",
        "note": (
            "Voluntary, but signing it is the route to presumed conformity with the AI Act's "
            "general-purpose model obligations. A voluntary instrument with that consequence "
            "sits between guidance and regulation, which is why it is indexed."
        ),
    },
]

# ---------------------------------------------------------------------------
# United States. Federal level, plus the two state statutes that bind more
# frontier developers than anything federal does. Omitting those would
# misrepresent the position rather than simplify it.
# ---------------------------------------------------------------------------
UNITED_STATES = [
    {
        "title": "Executive Order 14179, Removing Barriers to American Leadership in AI",
        "force": "agency-binding",
        "year": 2025,
        "body": "President of the United States",
        "topics": ["government use"],
        "url": "https://www.federalregister.gov/executive-order/14179",
        "note": (
            "Revoked Executive Order 14110 and reset federal policy toward removing "
            "regulatory barriers. Executive orders bind the executive branch, not the "
            "market, and a successor can revoke them in a day, as this one did."
        ),
    },
    {
        "title": "Executive Order 14110, Safe, Secure, and Trustworthy AI (revoked)",
        "force": "review",
        "year": 2023,
        "body": "President of the United States",
        "topics": ["safety", "security"],
        "url": "https://www.federalregister.gov/executive-order/14110",
        "note": (
            "Listed because it is still widely cited as current US policy and is not. It "
            "introduced the 1e26 FLOP reporting threshold, the second compute threshold "
            "written into any official instrument, and was revoked in January 2025."
        ),
    },
    {
        "title": "TAKE IT DOWN Act",
        "force": "statute",
        "year": 2025,
        "body": "US Congress",
        "topics": ["safety", "children"],
        "url": "https://www.congress.gov/bill/119th-congress/senate-bill/146",
        "note": (
            "Criminalises publication of non-consensual intimate imagery including "
            "AI-generated depictions, and requires covered platforms to remove it on notice. "
            "One of very few federal statutes that names AI-generated material at all."
        ),
    },
    {
        "title": "Federal Trade Commission Act, section 5",
        "force": "statute",
        "year": 1914,
        "body": "US Congress",
        "topics": ["consumer", "competition"],
        "url": "https://www.ftc.gov/legal-library/browse/statutes/federal-trade-commission-act",
        "note": (
            "The general prohibition on unfair or deceptive acts and practices. With no AI "
            "statute in place it is the main federal hook for AI claims that do not hold up, "
            "and the FTC has used it against several AI products."
        ),
    },
    {
        "title": "NIST AI Risk Management Framework 1.0",
        "force": "voluntary",
        "year": 2023,
        "body": "National Institute of Standards and Technology",
        "topics": ["safety", "government use"],
        "url": "https://www.nist.gov/itl/ai-risk-management-framework",
        "note": (
            "No legal force, and the most widely adopted AI governance document in the "
            "United States. State bills and procurement rules incorporate it by reference, "
            "which is how a voluntary framework acquires teeth."
        ),
    },
    {
        "title": "California SB 53, Transparency in Frontier Artificial Intelligence Act",
        "force": "statute",
        "year": 2025,
        "body": "California State Legislature",
        "topics": ["safety", "transparency"],
        "url": "https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53",
        "note": (
            "State law, and the first binding frontier-model transparency statute anywhere: "
            "developers above a compute threshold must publish a safety framework and report "
            "critical safety incidents. It reaches most frontier labs because most of them "
            "are in California."
        ),
    },
    {
        "title": "New York RAISE Act, Responsible AI Safety and Education Act",
        "force": "statute",
        "year": 2025,
        "body": "New York State Legislature",
        "topics": ["safety", "transparency"],
        "url": "https://www.nysenate.gov/legislation/bills/2025/S6953/amendment/B",
        "note": (
            "Signed in December 2025 and narrowed by a chapter amendment in March 2026 to "
            "track California's SB 53: developers with over $500 million in annual revenue "
            "that train models above 1e26 FLOP must publish safety protocols and report "
            "safety incidents to the state. Applies from January 2027."
        ),
    },
    {
        "title": "Colorado SB24-205, Artificial Intelligence Act",
        "force": "statute",
        "year": 2024,
        "body": "Colorado General Assembly",
        "topics": ["discrimination", "consumer", "transparency"],
        "url": "https://leg.colorado.gov/bills/sb24-205",
        "note": (
            "The first US state statute imposing duties on developers and deployers of "
            "high-risk AI in consequential decisions. Its commencement date has been amended "
            "more than once; check the current one before relying on it."
        ),
    },
    {
        "title": "Advanced computing and semiconductor export controls",
        "force": "delegated",
        "year": 2022,
        "body": "Bureau of Industry and Security, Department of Commerce",
        "topics": ["export control", "security"],
        "url": "https://www.bis.doc.gov/index.php/policy-guidance/advanced-computing-and-semiconductor-manufacturing-items",
        "note": (
            "The most materially binding AI rules the United States has, and the least "
            "discussed as AI policy. They restrict which accelerators can be sold where, "
            "which decides who can train large models at all."
        ),
    },
]

# ---------------------------------------------------------------------------
# United Kingdom. No AI statute by choice, which is a position rather than a gap.
# ---------------------------------------------------------------------------
UNITED_KINGDOM = [
    {
        "title": "A pro-innovation approach to AI regulation",
        "force": "voluntary",
        "year": 2023,
        "body": "Department for Science, Innovation and Technology",
        "topics": ["safety", "government use"],
        "url": "https://www.gov.uk/government/publications/ai-regulation-a-pro-innovation-approach",
        "note": (
            "The white paper setting out the decision not to legislate horizontally, and to "
            "have existing regulators apply five cross-sectoral principles inside their own "
            "remits instead. Everything else in this list follows from it."
        ),
    },
    {
        "title": "Data Protection Act 2018",
        "force": "statute",
        "year": 2018,
        "body": "Parliament of the United Kingdom",
        "topics": ["privacy", "transparency"],
        "url": "https://www.legislation.gov.uk/ukpga/2018/12/contents",
        "note": (
            "With the UK GDPR, the binding constraint on most AI systems processing personal "
            "data, including the restriction on solely automated decisions with legal or "
            "similarly significant effects."
        ),
    },
    {
        "title": "Data (Use and Access) Act 2025",
        "force": "statute",
        "year": 2025,
        "body": "Parliament of the United Kingdom",
        "topics": ["privacy", "transparency"],
        "url": "https://www.legislation.gov.uk/ukpga/2025/18/contents",
        "note": (
            "Relaxes the automated-decision rules outside special-category data, moving from "
            "a general prohibition toward a safeguards model. The direction of travel is "
            "opposite to the EU's, which matters to anyone assuming the two regimes still "
            "track each other."
        ),
    },
    {
        "title": "Online Safety Act 2023",
        "force": "statute",
        "year": 2023,
        "body": "Parliament of the United Kingdom",
        "topics": ["safety", "children"],
        "url": "https://www.legislation.gov.uk/ukpga/2023/50/contents",
        "note": (
            "Duties of care on user-to-user and search services, enforced by Ofcom. "
            "Generative AI chatbots that let users share content fall inside scope, which is "
            "the main route by which UK law reaches consumer AI products."
        ),
    },
    {
        "title": "Equality Act 2010",
        "force": "statute",
        "year": 2010,
        "body": "Parliament of the United Kingdom",
        "topics": ["discrimination"],
        "url": "https://www.legislation.gov.uk/ukpga/2010/15/contents",
        "note": (
            "The indirect discrimination provisions apply to automated decisions without "
            "naming them. In a jurisdiction with no AI statute, this is what an unfair "
            "hiring or credit model is most likely to be challenged under."
        ),
    },
    {
        "title": "AI Security Institute",
        "force": "agency-binding",
        "year": 2023,
        "body": "Department for Science, Innovation and Technology",
        "topics": ["safety"],
        "url": "https://www.aisi.gov.uk/",
        "note": (
            "State capacity to test frontier models, established before any comparable body "
            "elsewhere and renamed from AI Safety Institute in 2025. It cannot compel "
            "access: testing happens by agreement with developers."
        ),
    },
    {
        "title": "ICO guidance on AI and data protection",
        "force": "regulator-guidance",
        "year": 2023,
        "body": "Information Commissioner's Office",
        "topics": ["privacy", "transparency"],
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/",
        "note": (
            "How the data regulator says it will apply existing law to AI. Not law, and the "
            "closest thing to an operational compliance standard the UK has."
        ),
    },
]

# ---------------------------------------------------------------------------
# China. Binding rules arrive as administrative measures rather than as one
# statute, which is why searching for "China AI law" finds a draft and misses
# the instruments that have actually been in force for years.
#
# Citations are to China Law Translate rather than to the issuing bodies. Their
# translations are the reference the English-language legal literature uses, and
# the issuing sites are not reliably reachable from outside China: a citation
# nobody can open is not a citation. Every entry names the issuing body.
# ---------------------------------------------------------------------------
CHINA = [
    {
        "title": "Interim Measures for the Management of Generative AI Services",
        "force": "delegated",
        "year": 2023,
        "body": "Cyberspace Administration of China and six other bodies",
        "topics": ["safety", "transparency", "security"],
        "url": "https://www.chinalawtranslate.com/en/generative-ai-interim/",
        "note": (
            "The first binding national rules addressed to generative AI anywhere: security "
            "assessment and algorithm filing before public launch, content obligations, and "
            "duties on training data."
        ),
    },
    {
        "title": "Provisions on Deep Synthesis Internet Information Services",
        "force": "delegated",
        "year": 2022,
        "body": "Cyberspace Administration of China",
        "topics": ["labelling", "transparency", "safety"],
        "url": "https://www.chinalawtranslate.com/en/deep-synthesis/",
        "note": (
            "Required labelling of synthetic media two years before any comparable Western "
            "obligation, and requires consent before generating a likeness of a real person."
        ),
    },
    {
        "title": "Measures for Labelling AI-Generated Synthetic Content",
        "force": "delegated",
        "year": 2025,
        "body": "Cyberspace Administration of China and three other bodies",
        "topics": ["labelling", "transparency"],
        "url": "https://www.chinalawtranslate.com/en/ai-labeling/",
        "note": (
            "In force from September 2025, with a mandatory national standard alongside it. "
            "Requires both a label the reader can see and one embedded in file metadata, "
            "which is a stronger requirement than the EU's Article 50."
        ),
    },
    {
        "title": "Provisions on Algorithmic Recommendation of Internet Information Services",
        "force": "delegated",
        "year": 2021,
        "body": "Cyberspace Administration of China",
        "topics": ["transparency", "consumer"],
        "url": "https://www.chinalawtranslate.com/en/algorithms/",
        "note": (
            "Created the algorithm filing regime that the later measures build on, and gave "
            "users a right to switch recommendation off. The filing register is the closest "
            "thing any jurisdiction has to a public inventory of deployed systems."
        ),
    },
    {
        "title": "Personal Information Protection Law",
        "force": "statute",
        "year": 2021,
        "body": "National People's Congress",
        "topics": ["privacy", "transparency"],
        "url": "https://www.chinalawtranslate.com/en/pipl/",
        "note": (
            "China's general data protection statute, including rules on automated "
            "decision-making and a right to an explanation where a decision has a "
            "significant effect on an individual."
        ),
    },
    {
        "title": "Data Security Law",
        "force": "statute",
        "year": 2021,
        "body": "National People's Congress",
        "topics": ["security", "export control"],
        "url": "https://www.chinalawtranslate.com/en/datasecuritylaw/",
        "note": (
            "Classifies data by importance and restricts cross-border transfer of important "
            "data, which constrains where training corpora can be assembled and processed."
        ),
    },
    {
        "title": "Cybersecurity Law",
        "force": "statute",
        "year": 2016,
        "body": "National People's Congress",
        "topics": ["security"],
        "url": "https://www.chinalawtranslate.com/en/cybersecuritylaw/",
        "note": (
            "The statute the administrative measures are made under. Network operators carry "
            "security obligations and a real-name requirement, which is what makes the "
            "algorithm filing and security assessment regimes enforceable."
        ),
    },
]

# ---------------------------------------------------------------------------
# Canada. The AI statute died with the Parliament that was considering it, which
# makes the binding instruments the general ones plus a government-only directive.
# ---------------------------------------------------------------------------
CANADA = [
    {
        "title": "Personal Information Protection and Electronic Documents Act",
        "force": "statute",
        "year": 2000,
        "body": "Parliament of Canada",
        "topics": ["privacy"],
        "url": "https://laws-lois.justice.gc.ca/eng/acts/P-8.6/",
        "note": (
            "The federal private-sector privacy statute, and with provincial equivalents the "
            "main binding constraint on commercial AI in Canada. Its reform was bundled into "
            "the same bill as the AI statute, so both fell together."
        ),
    },
    {
        "title": "Directive on Automated Decision-Making",
        "force": "agency-binding",
        "year": 2019,
        "body": "Treasury Board of Canada Secretariat",
        "topics": ["government use", "transparency"],
        "url": "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32592",
        "note": (
            "Requires an Algorithmic Impact Assessment before a federal department deploys an "
            "automated decision system, with obligations scaled to the assessed impact level. "
            "The first instrument of its kind anywhere and still among the most concrete, and "
            "it binds government rather than the market."
        ),
    },
    {
        "title": "Bill C-27, Artificial Intelligence and Data Act (died on the order paper)",
        "force": "review",
        "year": 2022,
        "body": "Parliament of Canada",
        "topics": ["safety", "discrimination"],
        "url": "https://www.parl.ca/legisinfo/en/bill/44-1/c-27",
        "note": (
            "Would have been the second comprehensive national AI statute after the EU's. It "
            "died when Parliament was prorogued in January 2025 and has not been "
            "reintroduced. Listed because it is still frequently cited as Canadian law."
        ),
    },
    {
        "title": "Voluntary Code of Conduct on Advanced Generative AI Systems",
        "force": "voluntary",
        "year": 2023,
        "body": "Innovation, Science and Economic Development Canada",
        "topics": ["safety", "transparency"],
        "url": "https://ised-isde.canada.ca/site/ised/en/voluntary-code-conduct-responsible-development-and-management-advanced-generative-ai-systems",
        "note": (
            "Signed by a list of named Canadian developers. With the statute gone this is the "
            "operative federal expectation of generative AI developers, and it carries no "
            "consequence for ignoring it."
        ),
    },
]

# ---------------------------------------------------------------------------
# Japan. Has an AI Act, and it imposes no penalties. That combination is the
# single most misread fact in international AI policy coverage.
# ---------------------------------------------------------------------------
JAPAN = [
    {
        "title": "Act on Promotion of Research, Development and Utilization of AI-Related Technologies",
        "force": "statute",
        "year": 2025,
        "body": "National Diet of Japan",
        "topics": ["safety", "government use"],
        "url": "https://www.japaneselawtranslation.go.jp/en/laws/view/5019",
        "note": (
            "In full effect from September 2025. It is a promotion statute: it establishes an "
            "AI Strategy Headquarters, sets out a basic plan and assigns roles, and creates "
            "no prohibitions and no monetary penalties. Japan has an AI Act and does not have "
            "AI obligations, and both halves of that matter."
        ),
    },
    {
        "title": "Act on the Protection of Personal Information",
        "force": "statute",
        "year": 2003,
        "body": "National Diet of Japan",
        "topics": ["privacy"],
        "url": "https://www.ppc.go.jp/en/legal/",
        "note": (
            "The binding constraint on AI systems handling personal data in Japan, enforced "
            "by the Personal Information Protection Commission. Where the AI Act creates no "
            "duties, this one does."
        ),
    },
    {
        "title": "Copyright Act, Article 30-4",
        "force": "statute",
        "year": 1970,
        "body": "National Diet of Japan",
        "topics": ["copyright"],
        "url": "https://www.bunka.go.jp/english/policy/copyright/",
        "note": (
            "One of the most permissive text and data mining provisions in the world: use of "
            "a work for machine learning is generally permitted where it is not for enjoying "
            "the expression itself. The Agency for Cultural Affairs has since narrowed how "
            "widely it reads that, which is what the linked guidance covers."
        ),
    },
    {
        "title": "AI Guidelines for Business",
        "force": "voluntary",
        "year": 2024,
        "body": "Ministry of Economy, Trade and Industry, and Ministry of Internal Affairs and Communications",
        "topics": ["safety", "transparency"],
        "url": "https://www.meti.go.jp/english/press/2024/0419_002.html",
        "note": (
            "The practical governance expectation on Japanese developers and deployers, "
            "covering the whole lifecycle. Voluntary, and in a jurisdiction with a "
            "penalty-free AI Act it does most of the work."
        ),
    },
]

# ---------------------------------------------------------------------------
# South Korea. The second comprehensive AI statute in force anywhere, and the
# first outside the EU.
# ---------------------------------------------------------------------------
SOUTH_KOREA = [
    {
        "title": "Framework Act on the Development of AI and Establishment of Trust",
        "force": "statute",
        "year": 2024,
        "body": "National Assembly of the Republic of Korea",
        "topics": ["safety", "transparency", "labelling"],
        "url": "https://cset.georgetown.edu/wp-content/uploads/t0625_south_korea_ai_law_EN.pdf",
        "note": (
            "In force from January 2026. Duties on high-impact AI in listed sectors, "
            "labelling of generative output, and a domestic representative requirement for "
            "large foreign providers. Administrative fines were given a grace period of about "
            "a year, so the obligations bind before the penalties do. Cited in the CSET "
            "translation, because Korea's own statute database returns no stable English URL."
        ),
    },
    {
        "title": "Personal Information Protection Act",
        "force": "statute",
        "year": 2011,
        "body": "National Assembly of the Republic of Korea",
        "topics": ["privacy", "transparency"],
        "url": "https://www.pipc.go.kr/eng/",
        "note": (
            "Includes a right to refuse or seek an explanation of a fully automated decision, "
            "added in 2023. Enforced by the Personal Information Protection Commission, which "
            "has been among the more active regulators on generative AI."
        ),
    },
    {
        "title": "Korea AI Safety Institute",
        "force": "agency-binding",
        "year": 2024,
        "body": "Ministry of Science and ICT",
        "topics": ["safety"],
        "url": "https://www.aisi.re.kr/",
        "note": (
            "National evaluation capacity, established alongside the framework Act. Korea is "
            "one of a small number of jurisdictions with both a horizontal AI statute and a "
            "body able to test models against it."
        ),
    },
]

# ---------------------------------------------------------------------------
# Singapore. No AI statute and unusually concrete tooling, which is the
# combination the rest of the region tends to copy.
# ---------------------------------------------------------------------------
SINGAPORE = [
    {
        "title": "Model AI Governance Framework for Generative AI",
        "force": "voluntary",
        "year": 2024,
        "body": "Infocomm Media Development Authority and AI Verify Foundation",
        "topics": ["safety", "transparency"],
        "url": "https://aiverifyfoundation.sg/resources/mgf-gen-ai/",
        "note": (
            "Nine dimensions from accountability and data to incident reporting and security. "
            "Voluntary, and widely used as a template outside Singapore, which gives it "
            "influence well beyond its legal force."
        ),
    },
    {
        "title": "Personal Data Protection Act 2012",
        "force": "statute",
        "year": 2012,
        "body": "Parliament of Singapore",
        "topics": ["privacy"],
        "url": "https://sso.agc.gov.sg/Act/PDPA2012",
        "note": (
            "The binding instrument. Singapore's AI governance work is voluntary; its data "
            "protection law is not, and that is where enforcement actually happens."
        ),
    },
    {
        "title": "Advisory Guidelines on Use of Personal Data in AI Systems",
        "force": "regulator-guidance",
        "year": 2024,
        "body": "Personal Data Protection Commission",
        "topics": ["privacy", "transparency"],
        "url": "https://www.pdpc.gov.sg/guidelines-and-consultation",
        "note": (
            "How the regulator reads consent, legitimate interests and business improvement "
            "exceptions when personal data is used to train or run a model. The operative "
            "compliance document for anyone deploying AI in Singapore. Linked to the "
            "guidelines index rather than the document, because the PDPC moves its own "
            "document URLs and the deep link 404s."
        ),
    },
    {
        "title": "AI Verify",
        "force": "voluntary",
        "year": 2022,
        "body": "AI Verify Foundation",
        "topics": ["safety", "transparency"],
        "url": "https://aiverifyfoundation.sg/",
        "note": (
            "A testing toolkit rather than a document: it runs technical tests and produces a "
            "report against the governance principles. Few jurisdictions have turned AI "
            "principles into something executable, and this is the clearest attempt."
        ),
    },
]

# ---------------------------------------------------------------------------
# India. The largest population of AI users with no AI statute, governed through
# intermediary liability rules and a data protection Act that is not yet fully
# commenced.
# ---------------------------------------------------------------------------
INDIA = [
    {
        "title": "Digital Personal Data Protection Act 2023",
        "force": "statute",
        "year": 2023,
        "body": "Parliament of India",
        "topics": ["privacy"],
        "url": "https://www.meity.gov.in/data-protection-framework",
        "note": (
            "India's first comprehensive data protection statute. Consent-centred, with "
            "narrow exemptions and no explicit automated-decision right. Its rules were "
            "notified in stages, so the date it binds a given duty is not the date it passed."
        ),
    },
    {
        "title": "Information Technology Act 2000",
        "force": "statute",
        "year": 2000,
        "body": "Parliament of India",
        "topics": ["safety", "security"],
        "url": "https://www.indiacode.nic.in/handle/123456789/1999",
        "note": (
            "The statute everything else is made under, including the intermediary rules. "
            "Section 79 safe harbour is the lever the government uses on platforms, and by "
            "extension on the generative features inside them."
        ),
    },
    {
        "title": "Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules 2021",
        "force": "delegated",
        "year": 2021,
        "body": "Ministry of Electronics and Information Technology",
        "topics": ["safety", "labelling", "elections"],
        "url": "https://www.meity.gov.in/content/information-technology-intermediary-guidelines-and-digital-media-ethics-code-rules-2021",
        "note": (
            "Due diligence duties on intermediaries, amended to reach synthetically generated "
            "information and to require it to be labelled. This, not an AI statute, is how "
            "India regulates deepfakes."
        ),
    },
    {
        "title": "India AI Governance Guidelines",
        "force": "voluntary",
        "year": 2025,
        "body": "Ministry of Electronics and Information Technology",
        "topics": ["safety", "transparency"],
        "url": "https://indiaai.gov.in/",
        "note": (
            "The national framing: govern AI through existing law and institutions rather "
            "than a new statute, with voluntary commitments and a techno-legal approach. "
            "India's position is closer to the UK's than to the EU's."
        ),
    },
]

# ---------------------------------------------------------------------------
# Brazil. The most advanced AI bill outside the EU, and still a bill.
# ---------------------------------------------------------------------------
BRAZIL = [
    {
        "title": "Lei 13.709/2018 (Lei Geral de Protecao de Dados)",
        "force": "statute",
        "year": 2018,
        "body": "National Congress of Brazil",
        "topics": ["privacy", "transparency"],
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
        "note": (
            "Brazil's data protection statute, closely modelled on the GDPR, including a "
            "right to review of decisions taken solely on automated processing. Enforced by "
            "the ANPD, which is also the proposed AI supervisor."
        ),
    },
    {
        "title": "PL 2338/2023 (Marco Legal da Inteligencia Artificial)",
        "force": "proposal",
        "year": 2023,
        "body": "National Congress of Brazil",
        "topics": ["safety", "discrimination", "copyright"],
        "url": "https://www25.senado.leg.br/web/atividade/materias/-/materia/157233",
        "note": (
            "Risk-tiered like the EU AI Act, with additions the EU does not have: rights for "
            "affected people, and remuneration for copyright holders whose works are used in "
            "training. Passed the Senate in December 2024 and is still before the Chamber of "
            "Deputies. It creates no duties yet."
        ),
    },
    {
        "title": "Lei 12.965/2014 (Marco Civil da Internet)",
        "force": "statute",
        "year": 2014,
        "body": "National Congress of Brazil",
        "topics": ["safety", "privacy"],
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm",
        "note": (
            "The internet civil rights framework, including platform liability. A 2025 "
            "Supreme Court ruling narrowed its safe harbour, which changes the exposure of "
            "any platform hosting AI-generated content in Brazil."
        ),
    },
    {
        "title": "Lei 8.078/1990 (Codigo de Defesa do Consumidor)",
        "force": "statute",
        "year": 1990,
        "body": "National Congress of Brazil",
        "topics": ["consumer", "liability"],
        "url": "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm",
        "note": (
            "Strict supplier liability for defective products and services. Where an AI "
            "product causes harm to a consumer in Brazil, this applies now and does not wait "
            "for the AI bill."
        ),
    },
]

# ---------------------------------------------------------------------------
# The index itself. Order is by how much binding AI-specific law is in force,
# most first, because that is the comparison the page is for.
# ---------------------------------------------------------------------------
JURISDICTIONS = {
    "european-union": {
        "name": "European Union",
        "code": "EUR",
        "summary": (
            "The only jurisdiction with a horizontal AI statute in force. The AI Act bans a "
            "short list of practices, sets conformity requirements for high-risk uses and "
            "adds duties for general-purpose models above a compute threshold. Its high-risk "
            "obligations were deferred to 2027 and 2028 by the Digital Omnibus in July 2026; "
            "the transparency duties were not."
        ),
        "instruments": EU,
    },
    "south-korea": {
        "name": "South Korea",
        "code": "KOR",
        "summary": (
            "The second comprehensive AI statute in force anywhere and the first outside the "
            "EU. Duties on high-impact AI and labelling of generative output applied from "
            "January 2026, with administrative fines held back for roughly a year."
        ),
        "instruments": SOUTH_KOREA,
    },
    "china": {
        "name": "China",
        "code": "CHN",
        "summary": (
            "Binding AI rules since 2021, arriving as administrative measures rather than one "
            "statute: algorithm filing, security assessment before public launch, and "
            "labelling of synthetic content. A comprehensive AI Law has been drafted and not "
            "passed, so the measures are what binds."
        ),
        "instruments": CHINA,
    },
    "united-states": {
        "name": "United States",
        "code": "USA",
        "summary": (
            "No federal AI statute. Federal policy runs through executive orders, agency "
            "guidance and the general prohibition on deceptive practices, while the binding "
            "obligations on frontier developers are state law, most consequentially "
            "California's. Federal policy since December 2025 has been directed at preempting "
            "that state law."
        ),
        "instruments": UNITED_STATES,
    },
    "japan": {
        "name": "Japan",
        "code": "JPN",
        "summary": (
            "Has an AI Act with no penalties. The 2025 statute promotes research and use, "
            "creates a strategy headquarters and assigns roles; it imposes no prohibitions. "
            "Binding constraints come from data protection and copyright law instead, and "
            "Japan's text and data mining exception is among the world's most permissive."
        ),
        "instruments": JAPAN,
    },
    "united-kingdom": {
        "name": "United Kingdom",
        "code": "GBR",
        "summary": (
            "No AI statute by deliberate choice, with existing regulators applying five "
            "cross-sectoral principles inside their own remits. Built national evaluation "
            "capacity before anyone else, and has since moved its automated-decision rules "
            "away from the EU position rather than toward it."
        ),
        "instruments": UNITED_KINGDOM,
    },
    "canada": {
        "name": "Canada",
        "code": "CAN",
        "summary": (
            "Had the second comprehensive national AI bill in the world and lost it: the "
            "Artificial Intelligence and Data Act died when Parliament was prorogued in "
            "January 2025. What remains is privacy law, a voluntary code, and a mandatory "
            "impact-assessment directive that binds federal departments only."
        ),
        "instruments": CANADA,
    },
    "brazil": {
        "name": "Brazil",
        "code": "BRA",
        "summary": (
            "The most advanced AI bill outside the EU, and still a bill. PL 2338 passed the "
            "Senate in December 2024 and remains before the Chamber of Deputies. Until it "
            "passes, AI in Brazil is governed by data protection, consumer and platform law, "
            "all of which apply strictly."
        ),
        "instruments": BRAZIL,
    },
    "australia": {
        "name": "Australia",
        "code": "AUS",
        "summary": (
            "No AI statute and no AI regulator. Australia governs AI through law that does "
            "not mention it: privacy, consumer, online safety, therapeutic goods, "
            "corporations and criminal law. The one genuinely binding AI-specific obligation "
            "applies to Commonwealth agencies rather than to the market. Mandatory guardrails "
            "for high-risk AI were proposed in 2024 and have not been legislated."
        ),
        "instruments": AUSTRALIA,
    },
    "india": {
        "name": "India",
        "code": "IND",
        "summary": (
            "The largest population of AI users of any jurisdiction here, and no AI statute. "
            "Governance runs through intermediary liability rules, amended to reach "
            "synthetically generated content, and a data protection Act commenced in stages. "
            "The stated national position is to use existing law rather than write new law."
        ),
        "instruments": INDIA,
    },
    "singapore": {
        "name": "Singapore",
        "code": "SGP",
        "summary": (
            "No AI statute, and the most concrete voluntary tooling anywhere: a governance "
            "framework for generative AI and a testing toolkit that produces an actual report "
            "rather than a principle. Binding obligations come from data protection law."
        ),
        "instruments": SINGAPORE,
    },
}
