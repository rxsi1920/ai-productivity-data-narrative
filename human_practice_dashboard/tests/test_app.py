from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "No observations match the selected filters."
GROUP_QUESTION = "Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?"


def run() -> AppTest:
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()


def infos(app: AppTest) -> list[str]:
    return [i.value for i in app.info]


def test_opening_screen_states_question_answer_and_story():
    app = run()
    assert not app.exception
    assert app.title[0].value == "Is AI weakening the human practice and knowledge that both people and AI learn from?"
    text = " ".join(m.value for m in app.markdown)
    assert GROUP_QUESTION in text and "Our answer" in text
    assert [h.value[0] for h in app.header] == list("12345")
    assert len(app.get("vega_lite_chart")) >= 8


def test_adoption_answers_empty_state():
    app = run()
    app.multiselect(key="adoption_answers").set_value([]).run()
    assert EMPTY in infos(app) and not app.exception
    app.multiselect(key="adoption_answers").set_value(["Yes", "No"]).run()
    assert EMPTY not in infos(app)


def test_evidence_filter_rewrites_headline_and_empty_state():
    app = run()
    full = [m.value for m in app.markdown if "output findings show a gain" in m.value][0]
    assert "3 of 3 output findings" in full and "2 show a loss and 1 a gain" in full
    app.multiselect(key="evidence_strength").set_value(["High"]).run()
    high = [m.value for m in app.markdown if "output findings show a gain" in m.value][0]
    assert "2 of 2 output findings" in high and "1 show a loss and 0 a gain" in high
    app.multiselect(key="evidence_strength").set_value([]).run()
    assert EMPTY in infos(app) and not app.exception


def test_composition_basis_changes_the_figures():
    app = run()
    tokens = [m.value for m in app.metric if m.label.startswith("Human-labelled share,")]
    app.radio(key="composition_basis").set_value("Documents").run()
    documents = [m.value for m in app.metric if m.label.startswith("Human-labelled share,")]
    assert tokens == ["63.5%"] and documents != tokens and not app.exception


def test_forecast_band_changes_the_chart():
    app = run()
    specs = lambda a: [c.proto.spec for c in a.get("vega_lite_chart")]
    before = specs(app)
    app.radio(key="ai_share_band").set_value("95%").run()
    assert specs(app) != before


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
