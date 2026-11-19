import streamlit as st

from .tabs.human_practice.tab import human_practice_tab
from .tabs.moral_degradation.tab import *
from .tabs.overall_conclusion.tab import overall_conclusion_tab

st.set_page_config(page_title=PAGE_TITLE, layout="wide")


def main():
    pages = [
        st.Page(
            human_practice_tab,
            title="Feedback loop and cognition",
            url_path="feedback-loop",
            default=True,
        ),
        st.Page(
            moral_degradation_tab,
            title="Moral degradation",
            url_path="moral-degradation",
        ),
        st.Page(
            overall_conclusion_tab,
            title="Overall conclusion",
            url_path="overall-conclusion",
        ),
    ]
    st.navigation(pages).run()
