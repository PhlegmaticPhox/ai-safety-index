"""Environmental Disclosure Index: what frontier developers and the companies that
run their data centres have published about energy, emissions and power sources.

Five datasets, all hand-coded from primary publications:

    environment-developers   one record per developer: its training footprint,
                             where it computes, what powers those sites, and its
                             energy per prompt, each marked disclosed, partly
                             disclosed, reported by others, or not disclosed
    training-footprints      every published training energy or emissions figure
    inference-energy         every published per-prompt energy or emissions figure
    operator-energy          data-centre electricity and clean-energy claims from
                             the operators' own sustainability reports
    grid-carbon-free         Google's hourly carbon-free share by grid region, the
                             only per-region figure any operator publishes

WHY IT IS MOSTLY ABSENCES. The question a reader brings, "which models pollute
most, and do they run on renewables or fossil fuels", has no dataset behind it.
No developer publishes energy use for its largest models. The largest training
runs are known from Epoch AI's compute estimates, the power behind them from
permits and press reporting, and the clean-energy claims from company reports
that cover the whole company rather than any one model. This index records each
of those separately and says which is which, because a cell that reads "not
disclosed" is the finding for most of the frontier.

TWO WAYS TO COUNT A TONNE. Location-based emissions use the average carbon
intensity of the grid a data centre draws from. Market-based emissions subtract
the renewable energy a company has bought by contract, wherever and whenever it
was generated. A company matching 100% of its annual use with renewable purchases
reports near-zero market-based emissions while the grid under it burns gas at
night. Both are recorded wherever a source gives both.

    python etl/build_environment_index.py                # validate and write
    python etl/build_environment_index.py --self-check   # schema and arithmetic
    python etl/build_environment_index.py --check-links  # probe every citation
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import check_links, review_stamp, write_dataset

SOURCE = "environmental-disclosure-index"
REVIEWED = "2026-09-25"

STATUS = {
    "disclosed": "Published by the developer",
    "partial": "Partly published by the developer",
    "reported": "Reported by others, not the developer",
    "none": "Not disclosed",
}

# The four questions asked of every developer, in the order the page prints them.
QUESTIONS = {
    "training": "Training energy or emissions",
    "sites": "Where it trains and serves",
    "power": "What powers those sites",
    "inference": "Energy per prompt",
}

GOOGLE_REPORT = (
    "https://storage.googleapis.com/gweb-mobius-cdn/sustainability/uploads/"
    "7f477eb723fe0c23d03f94b90a08882b9f28187d.pdf"
)
GOOGLE_PROMPT = (
    "https://cloud.google.com/blog/products/infrastructure/"
    "measuring-the-environmental-impact-of-ai-inference"
)
GEMMA_CARD = "https://ai.google.dev/gemma/docs/core/model_card_3"
LLAMA_2_CARD = "https://github.com/meta-llama/llama/blob/main/MODEL_CARD.md"
LLAMA_3_CARD = "https://github.com/meta-llama/llama-models/blob/main/models/llama3/MODEL_CARD.md"
LLAMA_31_CARD = "https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/MODEL_CARD.md"
LLAMA_4_CARD = "https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md"
MISTRAL_LCA = "https://mistral.ai/news/our-contribution-to-a-global-environmental-standard-for-ai"
ALTMAN_POST = "https://blog.samaltman.com/the-gentle-singularity"
DEEPSEEK_V3 = "https://arxiv.org/abs/2412.19437"
BLOOM_PAPER = "https://arxiv.org/abs/2211.02001"
GPT3_ESTIMATE = "https://arxiv.org/abs/2104.10350"
XAI_PERMIT = "https://www.datacenterdynamics.com/en/news/elon-musk-xai-gas-turbines-memphis/"
AMAZON_REPORT = "https://www.aboutamazon.com/news/sustainability/amazon-sustainability-report-2025"
MICROSOFT_REPORT = (
    "https://www.microsoft.com/en-us/corporate-responsibility/topics/sustainability/report/"
)


def cell(status: str, text: str, *links: tuple[str, str]) -> dict:
    return {
        "status": status,
        "status_meaning": STATUS[status],
        "text": text,
        "links": [{"label": label, "url": url} for label, url in links],
    }


DEVELOPERS = [
    {
        "developer": "OpenAI",
        "epoch_orgs": ["OpenAI"],
        "training": cell("none", "No energy or emissions figure for any model."),
        "sites": cell(
            "disclosed",
            "Stargate sites built with Oracle and SoftBank. The first, at Abilene, Texas, "
            "runs on Oracle Cloud Infrastructure.",
            ("OpenAI", "https://openai.com/index/five-new-stargate-sites/"),
        ),
        "power": cell(
            "reported",
            "Permits filed for on-site natural-gas turbines at the Abilene campus. OpenAI "
            "publishes no energy figure for any site.",
            ("DCD", "https://www.datacenterdynamics.com/en/news/natural-gas-plant-planned-for-stargate-ai-data-center-campus-report/"),
        ),
        "inference": cell(
            "disclosed",
            "0.34 Wh for an average ChatGPT query, June 2025, stated without a method.",
            ("Sam Altman", ALTMAN_POST),
        ),
    },
    {
        "developer": "Google DeepMind",
        "epoch_orgs": ["Google DeepMind", "Google", "DeepMind"],
        "training": cell(
            "partial",
            "1,497 tCO2e to pre-train the open Gemma 3 models. No figure for any Gemini model.",
            ("Gemma 3 model card", GEMMA_CARD),
        ),
        "sites": cell(
            "partial",
            "Google's own data centres. Which sites train or serve a given model is not stated.",
            ("Google", GOOGLE_REPORT),
        ),
        "power": cell(
            "disclosed",
            "65% carbon-free energy hour by hour across Google's data centres in 2025, and "
            "100% matched with renewable purchases over the year.",
            ("Google", GOOGLE_REPORT),
        ),
        "inference": cell(
            "disclosed",
            "0.24 Wh, 0.03 gCO2e and 0.26 mL of water for the median Gemini Apps text "
            "prompt, May 2025, with a published method.",
            ("Google", GOOGLE_PROMPT),
        ),
    },
    {
        "developer": "Anthropic",
        "epoch_orgs": ["Anthropic"],
        "training": cell("none", "No energy or emissions figure for any model."),
        "sites": cell(
            "disclosed",
            "Amazon's Trainium clusters including Project Rainier, Google TPUs, and from "
            "May 2026 all of SpaceX's Colossus 1 in Memphis, over 300 MW.",
            ("Amazon", "https://www.anthropic.com/news/anthropic-amazon-compute"),
            ("Google", "https://www.anthropic.com/news/google-broadcom-partnership-compute"),
            ("SpaceX", "https://www.anthropic.com/news/higher-limits-spacex"),
        ),
        "power": cell(
            "reported",
            "Colossus 1 holds a permit for 15 on-site gas turbines. Amazon and Google state "
            "100% annual renewable matching for their own consumption. Anthropic publishes "
            "no energy figure.",
            ("DCD", XAI_PERMIT),
            ("Amazon", AMAZON_REPORT),
            ("Google", GOOGLE_REPORT),
        ),
        "inference": cell("none", "No per-prompt figure."),
    },
    {
        "developer": "Meta",
        "epoch_orgs": ["Meta AI"],
        "training": cell(
            "disclosed",
            "GPU hours and emissions in every Llama model card since Llama 2. Llama 3.1 405B: "
            "8,930 tCO2e location-based.",
            ("Llama 3.1 model card", LLAMA_31_CARD),
        ),
        "sites": cell(
            "partial",
            "Meta's own GPU clusters. Which site trained a given model is not stated.",
            ("Llama 3.1 model card", LLAMA_31_CARD),
        ),
        "power": cell(
            "disclosed",
            "100% of electricity matched with renewable energy since 2020, so market-based "
            "training emissions are reported as zero.",
            ("Llama 3.1 model card", LLAMA_31_CARD),
        ),
        "inference": cell("none", "No per-prompt figure."),
    },
    {
        "developer": "xAI",
        "epoch_orgs": ["xAI"],
        "training": cell("none", "No energy or emissions figure for any model."),
        "sites": cell(
            "reported",
            "Grok 3 was trained on Colossus, a converted factory in Memphis, Tennessee.",
            ("R&D World", "https://www.rdworldonline.com/how-xai-turned-a-factory-shell-into-an-ai-colossus-to-power-grok-3-and-beyond/"),
        ),
        "power": cell(
            "reported",
            "15 on-site gas turbines, 247 MW, permitted in July 2025. Around 35 ran before "
            "the permit was granted.",
            ("DCD", XAI_PERMIT),
        ),
        "inference": cell("none", "No per-prompt figure."),
    },
    {
        "developer": "DeepSeek",
        "epoch_orgs": ["DeepSeek"],
        "training": cell(
            "partial",
            "GPU hours only: 2.788 million H800 GPU hours for DeepSeek-V3. No energy or "
            "emissions figure.",
            ("DeepSeek-V3 report", DEEPSEEK_V3),
        ),
        "sites": cell("none", "Not stated."),
        "power": cell("none", "Not stated."),
        "inference": cell("none", "No per-prompt figure."),
    },
    {
        "developer": "Mistral AI",
        "epoch_orgs": ["Mistral AI"],
        "training": cell(
            "disclosed",
            "Lifecycle analysis of Mistral Large 2: 20.4 ktCO2e and 281,000 m3 of water for "
            "training and 18 months of use, to January 2025.",
            ("Mistral AI", MISTRAL_LCA),
        ),
        "sites": cell("none", "Not stated in the lifecycle analysis."),
        "power": cell("none", "Not stated in the lifecycle analysis."),
        "inference": cell(
            "disclosed",
            "1.14 gCO2e and 45 mL of water for a 400-token Le Chat response.",
            ("Mistral AI", MISTRAL_LCA),
        ),
    },
]

# Every published training figure. `energy_mwh` is the publisher's own number
# where one exists; for Meta it is derived here as GPU hours times the stated
# per-device power, which the model cards define as peak power adjusted for data
# centre efficiency, and `energy_derived` says so. `epoch_model` joins to Epoch's
# compute estimate so the page can print emissions per unit of compute.
FOOTPRINTS = [
    {
        "model": "GPT-3 175B", "developer": "OpenAI", "year": 2020, "epoch_model": "GPT-3 175B (davinci)",
        "hardware": "NVIDIA V100", "gpu_hours": None, "device_w": None,
        "energy_mwh": 1287.0, "energy_derived": False,
        "tco2e": 552.0, "tco2e_basis": "location-based",
        "market_tco2e": None,
        "who": "third-party estimate",
        "scope": "Final training run, estimated by Google researchers from published details. OpenAI has published no figure.",
        "url": GPT3_ESTIMATE,
    },
    {
        "model": "BLOOM 176B", "developer": "BigScience", "year": 2022, "epoch_model": "BLOOM-176B",
        "hardware": "NVIDIA A100", "gpu_hours": None, "device_w": None,
        "energy_mwh": 433.0, "energy_derived": False,
        "tco2e": 24.7, "tco2e_basis": "location-based",
        "market_tco2e": None,
        "who": "developer study",
        "scope": "Final training run, dynamic power only, on the Jean Zay supercomputer in France. 50.5 tCO2e including idle power and hardware manufacture.",
        "url": BLOOM_PAPER,
    },
    {
        "model": "Llama 2 70B", "developer": "Meta", "year": 2023, "epoch_model": "Llama 2-70B",
        "hardware": "NVIDIA A100 80GB", "gpu_hours": 1_720_320, "device_w": 400,
        "energy_mwh": None, "energy_derived": True,
        "tco2e": 291.42, "tco2e_basis": "location-based",
        "market_tco2e": None,
        "who": "developer model card",
        "scope": "Pre-training. The card states the emissions were fully offset.",
        "url": LLAMA_2_CARD,
    },
    {
        "model": "Llama 3 70B", "developer": "Meta", "year": 2024, "epoch_model": "Llama 3-70B",
        "hardware": "NVIDIA H100 80GB", "gpu_hours": 6_400_000, "device_w": 700,
        "energy_mwh": None, "energy_derived": True,
        "tco2e": 1900.0, "tco2e_basis": "location-based",
        "market_tco2e": None,
        "who": "developer model card",
        "scope": "Pre-training. The card states the emissions were fully offset.",
        "url": LLAMA_3_CARD,
    },
    {
        "model": "Llama 3.1 405B", "developer": "Meta", "year": 2024, "epoch_model": "Llama 3.1-405B",
        "hardware": "NVIDIA H100 80GB", "gpu_hours": 30_840_000, "device_w": 700,
        "energy_mwh": None, "energy_derived": True,
        "tco2e": 8930.0, "tco2e_basis": "location-based",
        "market_tco2e": 0.0,
        "who": "developer model card",
        "scope": "Training. The largest training run with a published emissions figure.",
        "url": LLAMA_31_CARD,
    },
    {
        "model": "Llama 4 Scout", "developer": "Meta", "year": 2025, "epoch_model": "Llama 4 Scout",
        "hardware": "NVIDIA H100 80GB", "gpu_hours": 5_000_000, "device_w": 700,
        "energy_mwh": None, "energy_derived": True,
        "tco2e": 1354.0, "tco2e_basis": "location-based",
        "market_tco2e": 0.0,
        "who": "developer model card",
        "scope": "Pre-training. No figure is published for Llama 4 Behemoth, the largest Llama 4 run.",
        "url": LLAMA_4_CARD,
    },
    {
        "model": "Llama 4 Maverick", "developer": "Meta", "year": 2025, "epoch_model": "Llama 4 Maverick",
        "hardware": "NVIDIA H100 80GB", "gpu_hours": 2_380_000, "device_w": 700,
        "energy_mwh": None, "energy_derived": True,
        "tco2e": 645.0, "tco2e_basis": "location-based",
        "market_tco2e": 0.0,
        "who": "developer model card",
        "scope": "Pre-training.",
        "url": LLAMA_4_CARD,
    },
    {
        "model": "Gemma 3", "developer": "Google DeepMind", "year": 2025, "epoch_model": None,
        "hardware": "Google TPU", "gpu_hours": None, "device_w": None,
        "energy_mwh": None, "energy_derived": False,
        "tco2e": 1497.13, "tco2e_basis": "unstated",
        "market_tco2e": None,
        "who": "developer model card",
        "scope": "Pre-training of the Gemma 3 family together. The card states Google's data centres are carbon neutral through renewable purchases and offsets.",
        "url": GEMMA_CARD,
    },
    {
        "model": "Mistral Large 2", "developer": "Mistral AI", "year": 2024, "epoch_model": None,
        "hardware": None, "gpu_hours": None, "device_w": None,
        "energy_mwh": None, "energy_derived": False,
        "tco2e": 20400.0, "tco2e_basis": "lifecycle",
        "market_tco2e": None,
        "who": "developer lifecycle analysis",
        "scope": "Training and 18 months of use to January 2025 together, on a lifecycle basis, so not comparable with a training-only figure.",
        "url": MISTRAL_LCA,
    },
    {
        "model": "DeepSeek-V3", "developer": "DeepSeek", "year": 2024, "epoch_model": "DeepSeek-V3",
        "hardware": "NVIDIA H800", "gpu_hours": 2_788_000, "device_w": None,
        "energy_mwh": None, "energy_derived": False,
        "tco2e": None, "tco2e_basis": None,
        "market_tco2e": None,
        "who": "developer technical report",
        "scope": "GPU hours only. No power, energy, location or emissions figure.",
        "url": DEEPSEEK_V3,
    },
]

INFERENCE = [
    {
        "developer": "Google", "product": "Gemini Apps", "statistic": "median text prompt",
        "wh": 0.24, "gco2e": 0.03, "water_ml": 0.26, "as_of": "2025-05",
        "method": "published",
        "note": "Counts idle machines and data-centre overhead. Emissions use Google's market-based fleet average for 2024.",
        "url": GOOGLE_PROMPT,
    },
    {
        "developer": "OpenAI", "product": "ChatGPT", "statistic": "average query",
        "wh": 0.34, "gco2e": None, "water_ml": None, "as_of": "2025-06",
        "method": "not published",
        "note": "Stated in a blog post by OpenAI's chief executive. Which models and which queries are averaged is not stated.",
        "url": ALTMAN_POST,
    },
    {
        "developer": "Mistral AI", "product": "Le Chat", "statistic": "400-token response",
        "wh": None, "gco2e": 1.14, "water_ml": 45.0, "as_of": "2025-01",
        "method": "published",
        "note": "Marginal impact of one response from Mistral Large 2, from an ISO 14040/44 lifecycle analysis. Energy is not given separately.",
        "url": MISTRAL_LCA,
    },
]

# Company-wide figures from each operator's own report. `hourly_cfe_pct` is the
# share of electricity that was carbon-free in the same hour on the same grid it
# was used, which only Google publishes. `renewable_match_pct` is annual
# contractual matching, which all four publish, and which is compatible with a
# data centre drawing gas-fired power every night of the year.
OPERATORS = [
    {
        "operator": "Google", "period": "2025",
        "dc_twh": 42.4158, "dc_twh_prior": 30.6371,
        "renewable_match_pct": 100, "hourly_cfe_pct": 65,
        "scope2_location_t": 15_148_700, "scope2_market_t": 2_815_000,
        "note": "Data-centre electricity rose 38% on 2024. The hourly carbon-free share was 13% across Google's Asia Pacific grid regions and 68% in the United States.",
        "url": GOOGLE_REPORT,
    },
    {
        "operator": "Microsoft", "period": "FY2025",
        "dc_twh": None, "dc_twh_prior": None,
        "renewable_match_pct": 100, "hourly_cfe_pct": None,
        "scope2_location_t": None, "scope2_market_t": None,
        "note": "Matched 100% of annual electricity with renewable energy in fiscal 2025. No hourly or per-region figure is published.",
        "url": MICROSOFT_REPORT,
    },
    {
        "operator": "Amazon", "period": "2025",
        "dc_twh": None, "dc_twh_prior": None,
        "renewable_match_pct": 100, "hourly_cfe_pct": None,
        "scope2_location_t": None, "scope2_market_t": None,
        "note": "Matched 100% of electricity with renewable energy for a third year. Runs AWS, where Anthropic trains and serves on Trainium chips.",
        "url": AMAZON_REPORT,
    },
    {
        "operator": "Meta", "period": "since 2020",
        "dc_twh": None, "dc_twh_prior": None,
        "renewable_match_pct": 100, "hourly_cfe_pct": None,
        "scope2_location_t": None, "scope2_market_t": None,
        "note": "Stated in its Llama model cards: net zero operations and 100% renewable matching since 2020.",
        "url": LLAMA_31_CARD,
    },
]

# Google's own table, 2025: Google CFE is the hourly carbon-free share of what
# Google's data centres consumed in that grid region, counting its contracts;
# grid CFE is the carbon-free share of the regional grid itself.
GRID_REGIONS = [
    ("Finland", "Fingrid", 98, 95),
    ("Denmark", "Energinet", 92, 89),
    ("Chile", "Sistema Interconectado Central", 90, 62),
    ("United States", "MISO", 88, 36),
    ("United States", "Salt River Project, Arizona", 86, 56),
    ("United States", "Southwest Power Pool", 84, 47),
    ("United States", "Bonneville Power Administration", 83, 84),
    ("United States", "ERCOT, Texas", 83, 46),
    ("Netherlands", "TenneT", 82, 55),
    ("Belgium", "Elia", 79, 72),
    ("United Kingdom", "National Grid ESO", 75, 71),
    ("Germany", "Germany", 70, 64),
    ("United States", "Duke Energy Carolinas", 65, 57),
    ("United States", "NV Energy", 65, 32),
    ("Ireland", "EirGrid", 60, 50),
    ("United States", "Tennessee Valley Authority", 58, 47),
    ("United States", "PJM", 57, 40),
    ("United States", "Southern Company", 42, 33),
    ("United States", "South Carolina", 31, 25),
    ("Japan", "TEPCO", 23, 18),
    ("Taiwan", "Taiwan Power Company", 15, 15),
    ("Singapore", "Energy Market Authority", 5, 5),
]


def _https(url: str, what: str) -> None:
    if not url.startswith("https://"):
        raise ValueError(f"{what}: citation must be an https URL, got {url!r}")


def build_developers() -> list[dict]:
    records = []
    for entry in DEVELOPERS:
        for key in QUESTIONS:
            item = entry[key]
            what = f"{entry['developer']} {key}"
            if item["status"] not in STATUS:
                raise ValueError(f"{what}: unknown status {item['status']!r}")
            # A claim needs a citation; an absence cannot have one. A cell that
            # says "not disclosed" while linking to a disclosure is what a
            # half-finished edit looks like.
            if item["status"] == "none" and item["links"]:
                raise ValueError(f"{what}: marked not disclosed but carries a citation")
            if item["status"] != "none" and not item["links"]:
                raise ValueError(f"{what}: a {item['status']} claim needs a citation")
            for link in item["links"]:
                _https(link["url"], what)
        records.append({**entry, "reviewed": REVIEWED, "source_id": SOURCE})
    return records


def build_footprints() -> list[dict]:
    records = []
    for entry in FOOTPRINTS:
        what = entry["model"]
        _https(entry["url"], what)
        energy = entry["energy_mwh"]
        if entry["energy_derived"]:
            if energy is not None or not (entry["gpu_hours"] and entry["device_w"]):
                raise ValueError(f"{what}: a derived energy figure needs GPU hours and power, and no published one")
            energy = round(entry["gpu_hours"] * entry["device_w"] / 1e6, 1)
        if entry["tco2e_basis"] not in (None, "location-based", "lifecycle", "unstated"):
            raise ValueError(f"{what}: unknown emissions basis {entry['tco2e_basis']!r}")
        if (entry["tco2e"] is None) != (entry["tco2e_basis"] is None):
            raise ValueError(f"{what}: an emissions figure needs a basis, and a basis needs a figure")
        records.append(
            {**entry, "energy_mwh": energy, "reviewed": REVIEWED, "source_id": SOURCE}
        )
    return sorted(records, key=lambda r: (r["year"], r["model"]))


def build_inference() -> list[dict]:
    for entry in INFERENCE:
        _https(entry["url"], entry["product"])
        if entry["wh"] is None and entry["gco2e"] is None:
            raise ValueError(f"{entry['product']}: neither energy nor emissions given")
    return [{**e, "reviewed": REVIEWED, "source_id": SOURCE} for e in INFERENCE]


def build_operators() -> list[dict]:
    for entry in OPERATORS:
        _https(entry["url"], entry["operator"])
        cfe = entry["hourly_cfe_pct"]
        if cfe is not None and not cfe <= entry["renewable_match_pct"]:
            raise ValueError(f"{entry['operator']}: hourly CFE cannot exceed annual matching")
    return [{**e, "reviewed": REVIEWED, "source_id": SOURCE} for e in OPERATORS]


def build_grid() -> list[dict]:
    records = []
    for country, grid, google_cfe, grid_cfe in GRID_REGIONS:
        for value in (google_cfe, grid_cfe):
            if not 0 <= value <= 100:
                raise ValueError(f"{grid}: {value} is not a percentage")
        records.append(
            {
                "operator": "Google", "year": 2025, "country": country, "grid": grid,
                "google_cfe_pct": google_cfe, "grid_cfe_pct": grid_cfe,
                "url": GOOGLE_REPORT, "reviewed": REVIEWED, "source_id": SOURCE,
            }
        )
    return sorted(records, key=lambda r: (-r["google_cfe_pct"], r["grid"]))


def run(offline: bool = False) -> None:
    """Hand-written, so there is nothing to fetch and offline changes nothing."""
    stamp = review_stamp(REVIEWED)
    common_note = f"Our own reading of primary publications, reviewed {REVIEWED}."
    write_dataset(
        "environment-developers", build_developers(), source_ids=[SOURCE], unit=None,
        notes=f"{common_note} Each cell is marked disclosed, partly disclosed, reported by others, or not disclosed.",
        retrieved=stamp,
    )
    write_dataset(
        "training-footprints", build_footprints(), source_ids=[SOURCE], unit="tCO2e",
        notes=f"{common_note} Every published training energy or emissions figure, with its basis. Energy for Meta models is derived from GPU hours and stated power.",
        retrieved=stamp,
    )
    write_dataset(
        "inference-energy", build_inference(), source_ids=[SOURCE], unit="Wh per prompt",
        notes=f"{common_note} Every published per-prompt figure. Median, mean and per-response figures are different statistics.",
        retrieved=stamp,
    )
    write_dataset(
        "operator-energy", build_operators(), source_ids=[SOURCE], unit=None,
        notes=f"{common_note} Company-wide figures from each operator's own sustainability report, not figures for any model.",
        retrieved=stamp,
    )
    write_dataset(
        "grid-carbon-free", build_grid(), source_ids=[SOURCE], unit="percent",
        notes=f"{common_note} Google's hourly carbon-free energy by data-centre grid region, 2025, from its 2026 Environmental Report.",
        retrieved=stamp,
    )


def _self_check() -> None:
    developers = build_developers()
    footprints = build_footprints()
    inference = build_inference()
    operators = build_operators()
    grid = build_grid()

    assert len(developers) >= 6, f"only {len(developers)} developers indexed"
    for record in developers:
        assert set(QUESTIONS) <= set(record), f"{record['developer']} is missing a question"
    none_cells = sum(r[k]["status"] == "none" for r in developers for k in QUESTIONS)
    assert none_cells, "no cell reads 'not disclosed', which cannot be right"

    # Derived energy, against the one figure that can be checked by hand: the
    # Llama 3.1 card's 30.84M GPU hours at 700 W is 21,588 MWh, and its 8,930
    # tCO2e over that is 0.41 t/MWh, a plausible US grid average. If the
    # arithmetic drifts by a factor of a thousand, this is where it shows.
    llama = next(r for r in footprints if r["model"] == "Llama 3.1 405B")
    assert llama["energy_mwh"] == 21588.0, llama["energy_mwh"]
    assert 0.3 < llama["tco2e"] / llama["energy_mwh"] < 0.6
    # A lifecycle figure must never be mistaken for a training figure.
    assert all(r["epoch_model"] is None for r in footprints if r["tco2e_basis"] == "lifecycle")

    assert any(r["method"] == "not published" for r in inference)
    google = next(r for r in operators if r["operator"] == "Google")
    assert google["scope2_location_t"] > google["scope2_market_t"], (
        "Google's location-based scope 2 should exceed its market-based figure"
    )
    assert len(grid) >= 20 and grid[0]["google_cfe_pct"] >= grid[-1]["google_cfe_pct"]

    # The validator must reject a "not disclosed" cell carrying a citation.
    DEVELOPERS[0]["training"]["links"].append({"label": "x", "url": "https://example.com"})
    try:
        build_developers()
    except ValueError:
        pass
    else:
        raise AssertionError("build_developers accepted a citation on an absence")
    finally:
        DEVELOPERS[0]["training"]["links"].pop()

    print(
        f"build_environment_index self-check passed: {len(developers)} developers "
        f"({none_cells} cells not disclosed), {len(footprints)} training footprints, "
        f"{len(inference)} per-prompt figures, {len(operators)} operators, "
        f"{len(grid)} grid regions"
    )


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    elif "--check-links" in sys.argv:
        entries = []
        for r in build_developers():
            for key in QUESTIONS:
                entries += [(f"{r['developer']} {key}", link["url"]) for link in r[key]["links"]]
        entries += [(r["model"], r["url"]) for r in build_footprints()]
        entries += [(r["product"], r["url"]) for r in build_inference()]
        entries += [(r["operator"], r["url"]) for r in build_operators()]
        raise SystemExit(1 if check_links(entries) else 0)
    else:
        _self_check()
        run()
