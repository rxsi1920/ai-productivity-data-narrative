from narrative.utils import *

from .views import *

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

PAGE_TITLE = "A PACT WITH THE MACHINES: The Moral Price Paid for AI"
PAGE_TITLE_CSS = '<div class="brand">A PACT WITH THE MACHINES:<br><span>The Moral Price Paid for AI</span></div>'
PERSONA_STR = "<div style='font-size: 16px;'> <strong>Persona:</strong> C-suite of data center operators</div>"
TQ_STR = """
As AI becomes increasingly central to our everyday decision-making, who bears the costs of moral erosion?
"""
GQ_STR = """
<div style="background-color: #171415; padding: 10px 15px; display: inline-block;">
    <span style="color: #ffffff; font-size: 0.9rem; line-height: 1.5;">
        <strong>Group Question: </strong>Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?
    </span>
</div>
"""

BG = "#404e51"
PANEL = "rgba(24, 34, 46, 0.72)"
LINE = "rgba(150, 180, 210, 0.4)"
TEXT = "#d9e4ef"
MUTED = "#7d8fa3"
ACCENT = "#4fc3e8"
ALARM = "#ff4d5a"


def moral_degradation_tab():
    st.markdown(
        f"""
        <style>
        header[data-testid="stHeader"] {{ background: transparent; }}
        .block-container {{ padding-top: 1.5rem; max-width: 1600px; }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {PANEL}; border: 1px solid {LINE}; border-radius: 16px;
            backdrop-filter: blur(8px);
        }}
        div[data-testid="stMetric"] label {{ color: {MUTED}; }}
        .brand {{ font-size: 1.4rem; font-weight: 700; letter-spacing: .02em; }}
        .brand span {{ font-weight: 300; }}
        .muted {{ color: {MUTED}; font-size: .85rem; }}
        .custom-tab-bar {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #3e444d; /* The long bottom line */
            margin-bottom: 20px;
            padding-bottom: 0;
        }}
    </style>


    """,
        unsafe_allow_html=True,
    )

    st.markdown(PAGE_TITLE_CSS, text_alignment="center", unsafe_allow_html=True)
    st.space()
    st.markdown(
        f"**Question**: {TQ_STR}", text_alignment="center", unsafe_allow_html=True
    )
    st.markdown(GQ_STR, text_alignment="center", unsafe_allow_html=True)

    st.space()
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
