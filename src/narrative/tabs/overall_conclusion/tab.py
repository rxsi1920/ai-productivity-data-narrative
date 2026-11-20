import streamlit as st

from narrative.story import GROUP_ANSWER, GROUP_QUESTION

from ..human_practice import views
from ..human_practice.tab import load_tables
from ..moral_degradation.tab import ai_reports_data
from ..moral_degradation.views import render_moral_summary
from ..profitability.tab import render_decision_points as render_profitability_decision

ANSWER_LABEL = "Elaborated answer"

# Same wording and figures as the answer box on the Profitability page, which computes them from data/processed/.
PROFITABILITY_ANSWER = (
    f"**{ANSWER_LABEL}: only partly, so far.** Productivity grew fastest in the industries that use AI most "
    "(EU, r = +0.73, 6 industries), and US corporate profits rose 49% from 2022Q4 to 2026Q2 while employee pay "
    "rose 19%. But economy-wide productivity growth slowed (2.4% → 1.9% a year worldwide, 2015–19 vs 2022–25), "
    "and countries that use AI most did not grow faster — so the measured gain is narrow and, in the US, goes more "
    "to profits than to pay."
)


def overall_conclusion_tab():
    tables = load_tables()

    st.title("Overall conclusion")
    st.markdown(f"**Group question:** {GROUP_QUESTION}")
    with st.container(border=True, key="group_answer"):
        st.markdown(GROUP_ANSWER)

    st.caption("Profitability")
    with st.container(border=True, key="profitability_answer"):
        st.markdown(PROFITABILITY_ANSWER)

    st.caption("Feedback loop and cognition")
    views.render_answer_text(tables, label=ANSWER_LABEL)

    st.caption("Moral degradation")
    render_moral_summary(ai_reports_data, label=ANSWER_LABEL)

    st.title("So What?")

    st.header("Decision points: Profitability")
    render_profitability_decision()

    st.header("Decision points: Feedback loop and cognition")
    views.render_decision(tables)
    st.divider()
    views.render_rollout(tables)
    views.render_questions_and_changes()

    st.header("Decision points: Moral degradation")
    st.info("Placeholder: decision points for a CEO or CFO deciding on AI governance.")  # TODO: replace