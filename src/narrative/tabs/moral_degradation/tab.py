from narrative.utils import *

from .views import *
from narrative.story import GROUP_QUESTION

DATA_ROOT = get_proc_data_dir()

ai_reports_data = get_csv(DATA_ROOT / "ai_reports.csv")
ai_inc_data = get_csv(DATA_ROOT / "ai_incidents.csv")
human_validation_data = get_csv(DATA_ROOT / "human_validation_scores_merged.csv")
ai_validation_data = get_csv(DATA_ROOT / "ai_validation_scores_merged.csv")
soft_eng_sat_data = get_csv(DATA_ROOT / "salary_and_satisfaction.csv")
soft_eng_trust_data = get_csv(DATA_ROOT / "ai_policy_and_ethics.csv")
gmf_class_data = get_csv(DATA_ROOT / "classifications_GMF.csv")

frameworks_data = pd.read_csv(DATA_ROOT / "GIRAI_Frameworks.csv")
classifications_data = pd.read_csv(DATA_ROOT / "GIRAI_Classifications.csv")

gov_trust_ipsos_data = pd.read_csv(DATA_ROOT / "Ipsos_gov_trust.csv")
comp_trust_ipsos_data = pd.read_csv(DATA_ROOT / "Ipsos_comp_trust.csv")
ai_env_trust_ipsos_data = pd.read_csv(DATA_ROOT / "Ipsos_ai_env_trust.csv")
job_sec_trust_ipsos_data = pd.read_csv(DATA_ROOT / "Ipsos_job_sec_trust.csv")

syco_study2_data = pd.read_csv(DATA_ROOT / "study2_responses.csv")
syco_study3_data = pd.read_csv(DATA_ROOT / "study3_responses.redacted.csv")

PERSONA_STR = "<div style='font-size: 16px;'> <strong>Persona:</strong> C-suite of data center operators</div>"
TQ_STR = """
AI delivers substantial value, but what does it cost when AI shapes our judgement, responsibility and trust?
"""

BG = "#404e51"
PANEL = "rgba(24, 34, 46, 0.72)"
LINE = "rgba(150, 180, 210, 0.4)"
TEXT = "#d9e4ef"
MUTED = "#7d8fa3"
ACCENT = "#4fc3e8"
ALARM = "#ff4d5a"


def moral_degradation_tab():

    st.title(TQ_STR)
    st.markdown(f"**Group question**: {GROUP_QUESTION}", unsafe_allow_html=True)
    with st.container(key="answer", border=True):
        st.markdown("""
            **Our answer:** Early on, AI weakens our moral judgement and the safeguards are thin, but does not have a proveable cause. In controlled experiments, people who talked to a flattering AI felt more in the right and were less willing to repair the conflict, and this held in more than one study. Around that, the safety net is clean, in that reported AI incidents reached 1,536 in 2025 and are still accelerating, models differ widely in how closely their moral scores match human validation, and in most areas of responsible AI only a minority of countries have a binding national framework. The first is a single-conversation experiment, the second is a count of reports, and the third is a snapshot of policy status. The effect on judgement is measured in surveys, the failures and gaps are indicators, and more importantly lacks a time-series data that indicates people's moral judgement erodes over time.
        """)

    st.header("1. A slow burning threat to humanity")
    render_reports_timeseries(ai_inc_data, ai_reports_data)

    render_gmf_failures(gmf_class_data)

    st.header("2. AI models vary in their ability to score moral behaviour reliably")
    st.subheader("Human validation against AI")
    render_human_validation_scores(human_validation_data)

    st.subheader("AI validation against AI")
    render_judge_agreement_heatmap(ai_validation_data)

    st.header("3. AI Guardrails")
    render_ai_framework_coverage(frameworks_data, classifications_data)

    st.header("4. General sentiment of AI is uncertainty")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        render_trust_chart(soft_eng_trust_data)
    with c2:
        render_ai_replacement(soft_eng_sat_data)
    with c3:
        pass

    render_ai_trust_choropleth(
        trust_gov_df=gov_trust_ipsos_data,
        trust_comp_df=comp_trust_ipsos_data,
        ai_env_trust_df=ai_env_trust_ipsos_data,
        job_sec_df=job_sec_trust_ipsos_data,
    )

    render_syco_effects(syco_study2_data, syco_study3_data)
    render_syco_rightness_distribution(syco_study2_data, syco_study3_data)
    render_syco_scenario_effects(syco_study2_data, syco_study3_data)

    st.header("Data and Limitations")
