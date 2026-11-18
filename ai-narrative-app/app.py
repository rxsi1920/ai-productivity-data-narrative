"""Data Narrative Studio, Team 3: "The Rise of Artificial Intelligence".

A three-page story.  Page 1 financial profitability, page 2 feedback-loop degradation and the cognitive ability
of employees (implemented), page 3 moral degradation.

    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="The Rise of Artificial Intelligence", layout="wide")

pages = [
    st.Page("app_pages/1_financial_profitability.py", title="1 · Financial profitability", icon=":material/payments:", url_path="profitability"),
    st.Page("app_pages/2_feedback_loop_and_cognition.py", title="2 · Feedback loop and cognition", icon=":material/psychology:", default=True),
    st.Page("app_pages/3_moral_degradation.py", title="3 · Moral degradation", icon=":material/balance:", url_path="moral-degradation"),
]
st.navigation(pages).run()
