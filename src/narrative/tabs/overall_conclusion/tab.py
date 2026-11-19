import streamlit as st

from narrative.story import GROUP_ANSWER, GROUP_QUESTION

from ..human_practice import views
from ..human_practice.tab import load_tables
from ..moral_degradation.tab import ai_reports_data
from ..moral_degradation.views import render_moral_summary


def overall_conclusion_tab():
    tables = load_tables()

    st.title("Overall conclusion")
    st.markdown(f"**Group question:** {GROUP_QUESTION}")

    with st.container(border=True, key="group_answer"):
        st.markdown(GROUP_ANSWER)

    st.caption("Feedback loop and cognition")
    views.render_answer_text(tables)

    st.caption("Moral Degradation")
    render_moral_summary(ai_reports_data)

    st.caption("Profitability")

    st.header("Decision points: Feedback loop and cognition")
    views.render_decision(tables)
    st.divider()
    views.render_rollout(tables)
    views.render_questions_and_changes()

    st.header("Decision points: Moral Degradation")

    st.header("Decision points: Profitability")
