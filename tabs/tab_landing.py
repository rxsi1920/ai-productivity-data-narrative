import pandas as pd
import streamlit as st
from src.story import GROUP_ANSWER, GROUP_QUESTION
from src.utils import get_proc_data_dir

DATA = get_proc_data_dir()

INTRO = (
    "Regardless of proof, the use of Artificial Intelligence is spreading rapidly, and that comes with implications on resources, "
    "business continuity, and ethics. This dashboard brings the following to the attention of decision-makers:"
)

STORIES = [
    (
        "As a C-suite executive deciding on AI investment (i.e., CEO or CFO), I want to see whether AI adoption has "
        "raised productivity and profits, so that I can judge the expected return."
    ),
    (
        "As a C-suite executive deciding on AI policy (i.e., COO or CTO), I want to see how AI use is affecting staff "
        "training and model training, so that I can decide where to prioritise human skilled input vs. AI-efficient "
        "output for business continuity."
    ),
    (
        "As a C-suite executive deciding on AI governance (i.e., CEO or CFO), I want to see how AI-related incidents and "
        "ethical risks are changing, so that I can price risk and guardrails into the business case."
    ),
]

# One line per page: what part of the group question it answers.
PAGE_BLURBS = {
    "profitability": "Does AI pay for itself?",
    "feedback-loop": "What cost does the AI efficiency we are gaining now have on the expertise that tomorrow's workers and models need?",
    "moral-degradation": "What does AI cost in judgement, responsibility and trust?",
    "overall-conclusion": "Weighing the measured gains against the hidden costs beyond financial and present impact.",
}

PAGE_CARD_CSS = """
<style>
div[class*="st-key-page_card_"] {
    background-color: #EEF2FF;
    border: 1px solid #6082FF !important;
}
</style>
"""

LIMITS = [
    (
        "**Cause and effect.** Every comparison is a before/after break or a correlation. Other forces, such as the 2022 "
        "energy shock, rate rises and the post-COVID recovery, moved at the same time."
    ),
    (
        "**AI use worldwide.** Firm-level AI use is measured consistently only for Europe (Eurostat) and the US (Census "
        "Bureau); the world figure is Microsoft's estimate from its own platform data."
    ),
    (
        "**Skills.** No dataset here measures skill over time. The link from fewer early-career jobs to less learning is "
        "our inference."
    ),
    (
        "**Incidents.** Reports count what is submitted to the AI Incident Database, not every incident, so a rise can "
        "also reflect more reporting."
    ),
    (
        "**Single firms and provisional data.** Many findings come from single firms or tasks, and the latest ILO and US "
        "national-accounts values are provisional."
    ),
]

from src.views import (
    LAST_REFRESH as MORAL_REFRESH,  # same date as the Moral degradation page
)

SOURCES = [
    (
        "Profitability",
        "22 Oct 2026",
        (
            "US Bureau of Economic Analysis and Bureau of Labor Statistics (via FRED); Eurostat; ILO (ILOSTAT); "
            "Our World in Data (incl. Microsoft AI Economy Institute, CSET, IEA); Stanford HAI AI Index 2026"
        ),
    ),
    (
        "Feedback loop and cognition",
        "11 Nov 2026",
        (
            "US Census Bureau Business Trends and Outlook Survey; Brynjolfsson, Chandar and Chen (2026); "
            "WildAI and Russell et al. (2026); Schaeffer et al. (2025); five output and skill studies (2023 to 2025)"
        ),
    ),
    (
        "Moral degradation",
        MORAL_REFRESH,
        (
            "[AI Incident Database](https://incidentdatabase.ai/); "
            "[Scientometric LLM Ethics Benchmark](https://github.com/universe-szw/scientometric-llm-ethics-benchmark); "
            "[Global Index on Responsible AI](https://www.global-index.ai/); [Ipsos AI Monitor](https://www.ipsos.com/); "
            "[Global AI Adoption and Workforce Impact Survey](https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26); "
            "[Cheng et al. (2025)](https://arxiv.org/abs/2510.01395)"
        ),
    ),
]


@st.cache_data(show_spinner=False)
def headline_figures() -> dict:
    """The three opening figures, computed from data/processed the same way each page computes them."""
    genai = pd.read_csv(DATA / "owid_estimated-share-people-generative-ai.csv")
    world = genai[genai["Entity"] == "World"].sort_values("Day")
    share = "Estimated share of working-age adults who use generative AI"
    g0, g1 = world.iloc[0], world.iloc[-1]

    adoption = pd.read_csv(DATA / "human_practice" / "adoption.csv")
    yes = adoption[adoption["answer"] == "Yes"].sort_values("period_order")
    a0, a1 = yes.iloc[0], yes.iloc[-1]

    reports = pd.read_csv(DATA / "ai_reports.csv")
    years = pd.to_datetime(
        reports["date_published"], errors="coerce", utc=True
    ).dt.year  # same rule as the moral page
    counts = years.value_counts()
    r_now, r_prev = int(counts.get(2025, 0)), int(counts.get(2024, 0))

    return {
        "genai_now": float(g1[share]),
        "genai_then": float(g0[share]),
        "genai_now_label": f"{pd.Timestamp(g1['Day']):%b %Y}",
        "genai_then_label": f"{pd.Timestamp(g0['Day']):%b %Y}",
        "adopt_now": float(a1["share_pct"]),
        "adopt_then": float(a0["share_pct"]),
        "adopt_now_label": a1["period_label"],
        "adopt_then_label": a0["period_label"],
        "reports_now": r_now,
        "reports_prev": r_prev,
        "reports_pct": (r_now - r_prev) / r_prev * 100 if r_prev else 0.0,
    }


def _headline(col, label, value, delta, note, delta_color="normal"):
    with col, st.container(border=True):
        st.metric(label, value, delta, delta_color=delta_color)
        st.caption(note)


def render_landing(pages):
    st.title("The Rise of Artificial Intelligence")
    st.subheader(GROUP_QUESTION)
    with st.container(border=True, key="group_answer"):
        st.markdown(GROUP_ANSWER)
    st.markdown(INTRO)

    h = headline_figures()
    c1, c2, c3 = st.columns(3)
    _headline(
        c1,
        f"Working-age adults using gen AI · world · {h['genai_now_label']}",
        f"{h['genai_now']:.1f}%",
        f"+{h['genai_now'] - h['genai_then']:.1f} pp from {h['genai_then']:.1f}% in {h['genai_then_label']}",
        "Ages 15 to 64. Microsoft AI Economy Institute via Our World in Data. See Profitability.",
    )
    _headline(
        c2,
        f"US firms using AI · {h['adopt_now_label']}",
        f"{h['adopt_now']:.1f}%",
        f"+{h['adopt_now'] - h['adopt_then']:.1f} pp from {h['adopt_then']:.1f}% in {h['adopt_then_label']}",
        "Share of US businesses answering yes. Census Bureau BTOS survey periods. See Feedback loop and cognition.",
    )
    _headline(
        c3,
        "AI incident reports · 2025",
        f"{h['reports_now']:,} reports",
        f"+{h['reports_pct']:.1f}% vs 2024 ({h['reports_prev']:,})",
        "Reports logged in the AI Incident Database, by publication year. See Moral degradation.",
        delta_color="inverse",
    )

    st.markdown(
        "We invite decision-makers to explore the gains and hidden costs of AI from the following lenses:"
    )
    st.markdown("\n".join(f"- {s}" for s in STORIES))

    st.markdown(
        "Each page is a deep-dive on a part of the story. Start with profitability:"
    )
    st.markdown(PAGE_CARD_CSS, unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for col, page in zip(cols, pages):
        with col, st.container(border=True, key=f"page_card_{page.url_path}"):
            st.page_link(page, label=page.title)
            st.caption(PAGE_BLURBS.get(page.url_path, ""))

    st.divider()

    st.caption(
        "**What this data can't show**\n\n" + "\n".join(f"- {item}" for item in LIMITS)
    )

    st.caption(
        "**Sources and last data refresh**\n\n"
        + "\n".join(
            f"- **{page}** (last data refresh: {refresh}): {src}"
            for page, refresh, src in SOURCES
        )
        + "\n\nThe figures above are computed from `data/processed/` each time the app loads. "
        "Each page lists its full sources, transforms and limits."
    )
