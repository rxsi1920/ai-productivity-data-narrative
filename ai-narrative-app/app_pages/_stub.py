"""Placeholder body for pages that are not built yet."""
from __future__ import annotations

import streamlit as st

from story import GROUP_QUESTION, STORY


def render_stub(number: str, covers: str) -> None:
    _, title, question = next(s for s in STORY if s[0] == number)
    st.title(f"Page {number}: {title}")
    st.markdown(f"**Group question:** {GROUP_QUESTION}")
    st.markdown(f"**This page's question:** {question}")
    st.info(f"Not built yet. {covers}")
    st.caption("Story order: 1 financial profitability → 2 feedback-loop degradation and cognitive ability of employees → 3 moral degradation.")
