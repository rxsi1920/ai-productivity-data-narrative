"""Smoke test: every page of the app runs without raising an exception.

Each page is opened on its own (Home is the default page in app.py), so a broken import or a changed function
signature on any page fails here instead of on the deployed app.
"""

import pytest
from streamlit.testing.v1 import AppTest


def _home():
    import streamlit as st
    from narrative.tabs.landing.tab import render_landing

    st.set_page_config(layout="wide")
    pages = [
        st.Page(lambda: None, title=t, url_path=u)
        for t, u in [
            ("Profitability", "profitability"),
            ("Feedback loop and cognition", "feedback-loop"),
            ("Moral degradation", "moral-degradation"),
            ("Overall conclusion", "overall-conclusion"),
        ]
    ]
    render_landing(pages)


def _profitability():
    import streamlit as st
    from narrative.tabs.profitability.tab import profitability_tab

    st.set_page_config(layout="wide")
    profitability_tab()


def _moral_degradation():
    import streamlit as st
    from narrative.tabs.moral_degradation.tab import moral_degradation_tab

    st.set_page_config(layout="wide")
    moral_degradation_tab()


def _overall_conclusion():
    import streamlit as st
    from narrative.tabs.overall_conclusion.tab import overall_conclusion_tab

    st.set_page_config(layout="wide")
    overall_conclusion_tab()


@pytest.mark.parametrize(
    "page",
    [_home, _profitability, _moral_degradation, _overall_conclusion],
    ids=lambda f: f.__name__,
)
def test_page_runs_without_error(page):
    app = AppTest.from_function(page, default_timeout=180).run()
    assert not app.exception, [e.message for e in app.exception]


def test_overall_conclusion_has_every_part():
    app = AppTest.from_function(_overall_conclusion, default_timeout=180).run()
    headers = [h.value for h in app.header]
    for part in ["Profitability", "Feedback loop and cognition", "Moral Degradation"]:
        assert f"Decision points: {part}" in headers


def test_moral_report_count_matches_home():
    # The moral answer and the Home KPI must quote the same number of 2025 incident reports.
    import pandas as pd
    from src.utils import get_proc_data_dir

    reports = pd.read_csv(get_proc_data_dir() / "ai_reports.csv")
    published = pd.to_datetime(reports["date_published"], errors="coerce", utc=True)
    expected = f"{(published.dt.year == 2025).sum():,}"

    app = AppTest.from_function(_overall_conclusion, default_timeout=180).run()
    text = " ".join(m.value for m in app.markdown)
    assert f"incidents reached {expected} in 2025" in text
