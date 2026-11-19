import streamlit as st

from narrative.story import GROUP_QUESTION, GROUP_ANSWER

from ..human_practice import views
from ..human_practice.tab import load_tables


def overall_conclusion_tab():
    tables = load_tables()

    st.title("Overall conclusion")
    st.markdown(f"**Group question:** {GROUP_QUESTION}")

    st.markdown(f"**Group question:** {GROUP_QUESTION}")
    with st.container(border=True, key="group_answer"):
        st.markdown(GROUP_ANSWER)

    st.caption("Feedback loop and cognition")
    views.render_answer_text(tables)
    # moral degradation summary goes here once it is written

    st.header("Decision points: Feedback loop and cognition")
    views.render_decision(tables)
    st.divider()
    views.render_rollout(tables)
    views.render_questions_and_changes()