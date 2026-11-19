import streamlit as st

from narrative.story import GROUP_QUESTION

from ..human_practice.src import views_people
from ..human_practice.src.page import load_tables


def overall_conclusion_tab():
    tables = load_tables()

    st.title("Overall conclusion")
    st.markdown(f"**Group question:** {GROUP_QUESTION}")

    st.caption("Feedback loop and cognition")
    views_people.render_answer_text(tables)
    # moral degradation summary goes here once it is written (Part 2)

    st.header("Decision points: Feedback loop and cognition")
    views_people.render_decision(tables)
    st.divider()
    views_people.render_rollout(tables)
    views_people.render_questions_and_changes()