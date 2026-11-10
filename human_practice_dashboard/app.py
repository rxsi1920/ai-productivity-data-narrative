from __future__ import annotations

import streamlit as st

from src.page import render_page

st.set_page_config(page_title="Is AI weakening human practice and knowledge?", layout="wide")
render_page()
