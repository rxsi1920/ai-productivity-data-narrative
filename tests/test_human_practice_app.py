from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "No observations match the selected filters."
GROUP_QUESTION = "Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?"


def _feedback_loop_page():
    import streamlit as st

    from narrative.tabs.human_practice.tab import human_practice_tab

    st.set_page_config(layout="wide")
    human_practice_tab()


def run() -> AppTest:
    # Home is the default page in app.py, so test the feedback-loop page on its own
    return AppTest.from_function(_feedback_loop_page, default_timeout=120).run()


def infos(app: AppTest) -> list[str]:
    return [i.value for i in app.info]

def evidence_headline(app: AppTest) -> str:
    return next(
        m.value
        for m in app.markdown
        if "output findings show a gain" in m.value and "show a loss" in m.value
    )

def test_opening_screen_states_question_answer_and_story():
    app = run()
    assert not app.exception
    assert app.title[0].value == "What cost does the AI efficiency we are gaining now have on the expertise that tomorrow's workers and models need?"
    text = " ".join(m.value for m in app.markdown)
    assert GROUP_QUESTION in text and "Our answer" in text
    assert [h.value[0] for h in app.header] == list("1234")
    assert len(app.get("vega_lite_chart")) == 5  # evidence, entry level, web composition, loss, compute


def test_evidence_filter_rewrites_headline_and_empty_state():
    app = run()
    full = evidence_headline(app)
    assert "3 of 3 output findings" in full and "2 show a loss and 1 a gain" in full
    app.multiselect(key="evidence_strength").set_value(["High"]).run()
    high = evidence_headline(app)
    assert "2 of 2 output findings" in high and "1 show a loss and 0 a gain" in high
    app.multiselect(key="evidence_strength").set_value([]).run()
    assert EMPTY in infos(app) and not app.exception


def test_composition_basis_changes_the_figures():
    app = run()
    tokens = [m.value for m in app.metric if m.label.startswith("Human-labelled share,")]
    app.radio(key="composition_basis").set_value("Documents").run()
    documents = [m.value for m in app.metric if m.label.startswith("Human-labelled share,")]
    assert tokens == ["63.5%"] and documents != tokens and not app.exception


def test_one_strength_keeps_both_group_headers():
    app = run()
    app.multiselect(key="evidence_strength").set_value(["Low"]).run()  # only one skill finding is rated Low
    assert not app.exception and EMPTY not in infos(app)
    assert any("0 of 0 output findings" in m.value for m in app.markdown)


def test_loss_chart_labels_every_point_by_default():
    app = run()
    assert app.multiselect(key="fig3_sizes").value == ["268M"]
    assert any("The value is printed at every point" in c.value for c in app.caption)
    app.multiselect(key="fig3_sizes").set_value(["86.2M", "135M", "268M"]).run()
    assert any("only the largest is labelled" in c.value for c in app.caption)


def test_loss_budget_changes_metrics_and_empty_state():
    app = run()
    base = [m.value for m in app.metric if "AI text" in m.label]
    app.select_slider(key="fig3_budget").set_value(4.72).run()
    low_budget = [m.value for m in app.metric if "AI text" in m.label]
    assert base != low_budget
    app.multiselect(key="fig3_sizes").set_value([]).run()
    assert EMPTY in infos(app)


def test_cost_target_changes_headline():
    app = run()
    human = [m.value for m in app.metric if "AI)" in m.label]
    app.radio(key="cost_target").set_value("AI-written text (Cosmopedia)").run()
    ai_text = [m.value for m in app.metric if "AI)" in m.label]
    assert human != ai_text and not app.exception
