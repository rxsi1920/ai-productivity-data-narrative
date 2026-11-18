import streamlit as st

from .tabs.moral_degradation.tab import *

st.set_page_config(page_title=PAGE_TITLE, layout="wide")


def main():
    moral_degradation_tab()
