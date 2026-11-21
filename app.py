import streamlit as st

from .tabs.human_practice.tab import human_practice_tab
from .tabs.landing.tab import render_landing
from .tabs.moral_degradation.tab import *
from .tabs.overall_conclusion.tab import overall_conclusion_tab
from .tabs.profitability.tab import *

APP_TITLE = "AI: Gains vs Hidden Costs"


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    content_pages = [
        st.Page(profitability_tab, title="Profitability", url_path="profitability"),
        st.Page(
            human_practice_tab,
            title="Feedback loop and cognition",
            url_path="feedback-loop",
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

    def landing():
        render_landing(content_pages)

    home = st.Page(landing, title="Home", default=True)
    st.navigation([home, *content_pages]).run()
