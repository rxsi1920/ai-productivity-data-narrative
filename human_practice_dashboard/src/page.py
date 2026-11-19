"""The page.  `render_page()` can be called from the group app's navigation."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from . import views, views_people
from .data import BUILDERS, PROCESSED, read_processed, validate

GROUP_QUESTION = "Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?"
PAGE_QUESTION = "Is AI weakening the human practice and knowledge that both people and AI learn from?"
USER_STORY = (
    "As a C-suite executive deciding on AI policy, I want to see how AI use is affecting staff training and model "
    "training, so that I can decide where to prioritise human skilled input vs. AI-efficient output for business continuity."
)


@st.cache_data(show_spinner=False)
def load_tables() -> dict[str, pd.DataFrame]:
    missing = [name for name in BUILDERS if not (PROCESSED / f"{name}.csv").exists()]
    if missing:
        st.error(f"Processed data missing: {', '.join(missing)}. Run `python -m src.data` first.")
        st.stop()
    tables = {name: read_processed(name) for name in BUILDERS}
    validate(tables)
    return tables


def render_page() -> None:
    tables = load_tables()
    share = tables["ai_share"].copy()
    share["month"] = pd.to_datetime(share["month"])
    latest = share[share["kind"] == "observed"].sort_values("month").iloc[-1]

    st.title(PAGE_QUESTION)
    st.markdown(f"**Group question:** {GROUP_QUESTION}")
    st.caption(f"User story: {USER_STORY}")
    views_people.render_answer(tables)

    st.header("1. Today: measured output is rising")
    st.markdown(
        "The gain is real and measured. The same studies carry the first warnings about judgement and learning."
    )
    views_people.render_evidence(tables["evidence"])

    st.header("2. People: the places where skills are practised are thinning")
    st.markdown("People learn a job by doing its entry-level work. That work is where AI use is concentrated.")
    views_people.render_entry_level(tables["entry_level"])

    st.header("3. Knowledge: human writing is a falling share of the web")
    st.markdown(
        "What people write is also what models are trained on. As more text is produced with AI, less of what a crawler "
        "collects is written by people alone."
    )
    views_people.render_web_composition(tables["web_composition"], tables["ai_share"])

    st.header("4. Models: learning from AI text costs more")
    st.markdown(
        "If left unchecked, the next models are trained on a web with less fresh human text. The experiments below show "
        "what that does: AI text is a poor substitute for human text, and the difference has to be bought back with compute."
    )
    views.render_loss_effect(tables["fig3_points"].assign(in_figure=lambda f: f["in_figure"].astype(bool)), float(latest["share"]), latest["month"])
    st.divider()
    views.render_cost(tables["cost"], tables["ai_share"])

    st.header("5. The decision")
    views_people.render_decision(tables)
    views_people.render_limits()
    with st.expander('Reference: the eight meanings of "model collapse" (Schaeffer et al. 2025)'):
        views.render_definitions(tables["definitions"])
    views_people.render_sources(tables)
