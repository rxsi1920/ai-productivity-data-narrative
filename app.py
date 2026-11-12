"""
Did AI lift profitability through productivity?
A Streamlit dashboard built only from public, citable source files in ./data.

Every number on screen is computed in this file from one of those raw files.
The Appendix lists each figure with its source file and the exact
transformation applied; each chart has a "Data behind this chart" expander.

Run:  streamlit run app.py
"""
from pathlib import Path

import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="AI, Productivity & Profitability", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# --------------------------------------------------------------------------------------
# 1. Source registry — where every file came from
# --------------------------------------------------------------------------------------
SOURCES = {
    "companies": dict(
        file="owid_share-companies-using-artificial-intelligence.csv",
        title="Organisations using AI, by region",
        publisher="McKinsey & Company survey via Stanford AI Index; Our World in Data",
        url="https://ourworldindata.org/grapher/share-companies-using-artificial-intelligence",
        notes="Share of organisations using AI in at least one business function, 2021–2025.",
    ),
    "workers": dict(
        file="owid_share-working-adults-united-states-ai-work.csv",
        title="US employees using AI at work",
        publisher="Gallup via Our World in Data",
        url="https://ourworldindata.org/grapher/share-working-adults-united-states-ai-work",
        notes="Share of US employees using AI daily / a few times a week+ / a few times a year+, by quarter.",
    ),
    "devs": dict(
        file="owid_share-of-professional-software-developers-using-ai-tools.csv",
        title="Developers using AI tools",
        publisher="Stack Overflow Developer Survey via Our World in Data",
        url="https://ourworldindata.org/grapher/share-of-professional-software-developers-using-ai-tools",
        notes="Share of professional developers worldwide using AI tools, 2023–2026.",
    ),
    "genai": dict(
        file="owid_global-investment-in-generative-ai.csv",
        title="Private investment in generative AI",
        publisher="Quid via Stanford AI Index 2026; Our World in Data",
        url="https://ourworldindata.org/grapher/global-investment-in-generative-ai",
        notes="Constant 2021 US$. Privately held gen-AI companies only.",
    ),
    "corp": dict(
        file="owid_corporate-investment-in-artificial-intelligence-by-type.csv",
        title="Corporate investment in AI by deal type",
        publisher="Quid via Stanford AI Index 2026; Our World in Data",
        url="https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type",
        notes="Constant 2021 US$. Excludes Big Tech internal R&D and capex.",
    ),
    "ophnfb": dict(
        file="fred_OPHNFB.csv",
        title="US labour productivity (output per hour)",
        publisher="U.S. Bureau of Labor Statistics via FRED, series OPHNFB",
        url="https://fred.stlouisfed.org/series/OPHNFB",
        notes="Nonfarm business sector, all workers, index 2017 = 100, quarterly, seasonally adjusted.",
    ),
    "ulcnfb": dict(
        file="fred_ULCNFB.csv",
        title="US unit labour cost",
        publisher="U.S. Bureau of Labor Statistics via FRED, series ULCNFB",
        url="https://fred.stlouisfed.org/series/ULCNFB",
        notes="Nonfarm business sector, index 2017 = 100, quarterly, seasonally adjusted.",
    ),
    "cp": dict(
        file="fred_CP.csv",
        title="US corporate profits after tax",
        publisher="U.S. Bureau of Economic Analysis via FRED, series CP",
        url="https://fred.stlouisfed.org/series/CP",
        notes="Without IVA and CCAdj, billions of US$, seasonally adjusted annual rate.",
    ),
    "gdp": dict(
        file="fred_GDP.csv",
        title="US nominal GDP",
        publisher="U.S. Bureau of Economic Analysis via FRED, series GDP",
        url="https://fred.stlouisfed.org/series/GDP",
        notes="Billions of US$, seasonally adjusted annual rate.",
    ),
    "evidence": dict(
        file="aiindex2026_ch4_extract.csv",
        title="Firm and study evidence",
        publisher="Stanford HAI AI Index Report 2026, Chapter 4 (Economy)",
        url="https://hai.stanford.edu/assets/files/ai_index_report_2026_chapter_4_economy.pdf",
        notes="Transcribed by hand from the PDF; each row keeps its figure and page number.",
    ),
}

EUROSTAT = "https://ec.europa.eu/eurostat/databrowser/view/{}/default/table"
SOURCES.update({
    "eu_ai": dict(
        file="eurostat_isoc_eb_ai.csv",
        title="Enterprises using AI, by country",
        publisher="Eurostat, ICT usage in enterprises survey (isoc_eb_ai)",
        url=EUROSTAT.format("isoc_eb_ai"),
        notes="Enterprises with 10+ employees, all activities except agriculture, mining and finance (C10-S951_X_K), % of enterprises. "
              "E_AI_TANY = uses at least one AI technology; E_AI_BCST = doesn't use AI because costs seem too high. Constant columns "
              "(freq, size_emp, nace_r2, unit) dropped on download; flags kept (b = break in series, u = unreliable).",
    ),
    "eu_lp": dict(
        file="eurostat_nama_10_lp_ulc.csv",
        title="Labour productivity and unit labour cost, by country",
        publisher="Eurostat national accounts (nama_10_lp_ulc)",
        url=EUROSTAT.format("nama_10_lp_ulc"),
        notes="RLPR_HW = real labour productivity per hour worked; NULC_HW = nominal unit labour cost per hour; both index 2015 = 100. "
              "2019 onward. Flag p = provisional.",
    ),
    "eu_profit": dict(
        file="eurostat_nasa_10_ki_profit_share.csv",
        title="Profit share of non-financial corporations, by country",
        publisher="Eurostat sector accounts (nasa_10_ki, B2G_B3G_RAT_S11)",
        url=EUROSTAT.format("nasa_10_ki"),
        notes="Gross operating surplus and mixed income ÷ gross value added × 100, non-financial corporations. 2019 onward.",
    ),
    "eu_cons": dict(
        file="eurostat_nasa_10_ki_consumption_growth.csv",
        title="Real consumption per person, by country",
        publisher="Eurostat sector accounts (nasa_10_ki, P4_R_HAB_GR)",
        url=EUROSTAT.format("nasa_10_ki"),
        notes="Households' actual final consumption per capita in real terms, % change on previous year. A proxy for consumer demand ('sales').",
    ),
    "eu_unemp": dict(
        file="eurostat_une_rt_a.csv",
        title="Unemployment rate, by country",
        publisher="Eurostat Labour Force Survey (une_rt_a)",
        url=EUROSTAT.format("une_rt_a"),
        notes="% of labour force, total and aged 15–24. Flags: b = break, d = definition differs, u = unreliable.",
    ),
    "ind_ai": dict(
        file="eurostat_isoc_eb_ain2_industry.csv",
        title="Enterprises using AI, by industry (EU27)",
        publisher="Eurostat (isoc_eb_ain2)",
        url=EUROSTAT.format("isoc_eb_ain2"),
        notes="EU27, enterprises with 10+ employees, % using at least one AI technology, by NACE section.",
    ),
    "ind_gva": dict(
        file="eurostat_nama_10_a10_industry.csv",
        title="Value added and pay, by industry (EU27)",
        publisher="Eurostat national accounts (nama_10_a10)",
        url=EUROSTAT.format("nama_10_a10"),
        notes="B1G = gross value added (CLV20_MEUR real; CP_MEUR nominal); D1 = compensation of employees (CP_MEUR). EU27, 2019 onward.",
    ),
    "ind_hours": dict(
        file="eurostat_nama_10_a10_e_hours.csv",
        title="Hours worked, by industry (EU27)",
        publisher="Eurostat national accounts (nama_10_a10_e)",
        url=EUROSTAT.format("nama_10_a10_e"),
        notes="Total employment, thousand hours worked (THS_HW, EMP_DC). EU27, 2019 onward.",
    ),
    "labshare": dict(
        file="fred_PRS85006173.csv",
        title="US labour share",
        publisher="U.S. Bureau of Labor Statistics via FRED, series PRS85006173",
        url="https://fred.stlouisfed.org/series/PRS85006173",
        notes="Nonfarm business sector labour share, index 2017 = 100, quarterly.",
    ),
    "nvidia": dict(
        file="owid_nvidia-quarterly-revenue-segment.csv",
        title="NVIDIA revenue by segment",
        publisher="NVIDIA Corporation via Our World in Data",
        url="https://ourworldindata.org/grapher/nvidia-quarterly-revenue-segment",
        notes="Quarterly revenue, nominal US$. Filtered to 2019 onward on download. Quarters as labelled by OWID (NVIDIA's fiscal year ends in late January).",
    ),
    "evidence2": dict(
        file="evidence_for_and_against.csv",
        title="Evidence for and against",
        publisher="Compiled from AI Index 2026 Ch.4, BMO Economics (Jun 2026), MIT NANDA coverage, NBER/BFI/arXiv papers",
        url="https://hai.stanford.edu/assets/files/ai_index_report_2026_chapter_4_economy.pdf",
        notes="Hand-compiled; each row names its source URL and where the number was checked. Rows marked 'verify' come from paper abstracts or press coverage.",
    ),
})

SOURCES.update({
    "ilo_oph": dict(
        file="ilo_output_per_hour.csv",
        title="Output per hour worked, world and regions",
        publisher="ILO modelled estimates (Nov 2025), ILOSTAT SDMX DF_GDP_2HRW_NOC_NB",
        url="https://sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB/X01+X34+X92+X45+X56+X26+X13+X88..?startPeriod=2015&format=csv",
        notes="GDP per hour worked, constant 2021 international $ at PPP. Columns kept: ref_area, year, value, obs_status. "
              "X01 World, X34 Northern America, X92 EU-27, X88 G7, X45 Eastern Asia, X56 Southern Asia, X26 Latin America & Caribbean, X13 Sub-Saharan Africa. "
              "Release includes projections to 2027; the app uses ≤ 2025.",
    ),
    "ilo_lis": dict(
        file="ilo_labour_income_share.csv",
        title="Labour income share of GDP, world and regions",
        publisher="ILO modelled estimates (Nov 2025), ILOSTAT SDMX DF_LAP_2GDP_NOC_RT",
        url="https://sdmx.ilo.org/rest/data/ILO,DF_LAP_2GDP_NOC_RT/X01+X34+X92+X45+X56+X26+X13+X88..?startPeriod=2015&format=csv",
        notes="Labour income (employees + self-employed) as % of GDP; same regions as above. Non-labour share = 100 − value.",
    ),
})

GEO_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "CH": "Switzerland", "CY": "Cyprus", "CZ": "Czechia", "DE": "Germany",
    "DK": "Denmark", "EE": "Estonia", "EL": "Greece", "ES": "Spain", "FI": "Finland", "FR": "France", "HR": "Croatia",
    "HU": "Hungary", "IE": "Ireland", "IS": "Iceland", "IT": "Italy", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "MT": "Malta", "NL": "Netherlands", "NO": "Norway", "PL": "Poland", "PT": "Portugal", "RO": "Romania", "RS": "Serbia",
    "SE": "Sweden", "SI": "Slovenia", "SK": "Slovakia", "TR": "Türkiye", "AL": "Albania", "BA": "Bosnia & Herz.",
    "ME": "Montenegro", "MK": "North Macedonia", "EU27_2020": "EU-27", "EA": "Euro area",
}
AGGREGATES = {"EU27_2020", "EA"}
INDUSTRY_MAP = {  # GVA/hours code (NACE A10) -> AI survey codes averaged, display name
    "C": (["C"], "Manufacturing"),
    "F": (["F"], "Construction"),
    "G-I": (["G", "H", "I"], "Trade, transport & hospitality"),
    "J": (["J"], "Information & communication"),
    "L": (["L"], "Real estate"),
    "M_N": (["M", "N"], "Professional & admin services"),
}


COLORS = {"accent": "#2563EB", "second": "#F59E0B", "third": "#10B981", "fourth": "#EF4444",
          "fifth": "#8B5CF6", "sixth": "#64748B", "muted": "#94A3B8", "ref": "#64748B"}
# >>> Edit these two lines to match your group's wording <<<
GROUP_QUESTION = "Do AI’s measured productivity gains outweigh the hidden costs to how people think, learn, and work?"
QUESTION = "Has AI improved company profitability by enhancing productivity?"  # my sub-question (the measured-gains side)
PERSONA = "CEO / CFO deciding whether to invest in adopting AI"   # edit to match your group's persona

AI_ERA_START = "2022-10-01"  # ChatGPT launched 30 Nov 2022 → first full quarter of the gen-AI era is 2022Q4


# --------------------------------------------------------------------------------------
# 2. Loading (raw files, untouched)
# --------------------------------------------------------------------------------------
@st.cache_data
def load(key: str) -> pd.DataFrame:
    return pd.read_csv(DATA / SOURCES[key]["file"])


@st.cache_data
def fred(key: str) -> pd.Series:
    df = load(key)
    col = df.columns[1]
    s = pd.Series(df[col].astype(float).values, index=pd.to_datetime(df["observation_date"]), name=col)
    return s


def qlabel(ts: pd.Timestamp) -> str:
    return f"{ts.year}Q{(ts.month - 1) // 3 + 1}"


# --------------------------------------------------------------------------------------
# 3. Transformations — every derived number comes from one of these
# --------------------------------------------------------------------------------------
def annualised_growth(s: pd.Series, start: str, end: str) -> float:
    """(end ÷ start)^(4 ÷ number of quarters) − 1, in %."""
    a, b = pd.Timestamp(start), pd.Timestamp(end)
    n = s.index.get_loc(b) - s.index.get_loc(a)
    return ((s[b] / s[a]) ** (4 / n) - 1) * 100


def quarterly_frame(base: str) -> pd.DataFrame:
    """Join the four FRED files by quarter and derive YoY, profit share and indices (base quarter = 100)."""
    P, U, CP, G = fred("ophnfb"), fred("ulcnfb"), fred("cp"), fred("gdp")
    b = pd.Timestamp(base)
    q = pd.DataFrame({"output_per_hour": P, "unit_labour_cost": U, "corporate_profits_bn": CP, "gdp_bn": G})
    q["quarter"] = [qlabel(t) for t in q.index]
    q["productivity_yoy_pct"] = (P / P.shift(4) - 1) * 100
    q["profit_share_pct"] = CP / G * 100
    q["productivity_idx"] = P / P[b] * 100
    q["ulc_idx"] = U / U[b] * 100
    q["profits_idx"] = CP / CP[b] * 100
    q["gdp_idx"] = G / G[b] * 100
    return q


def period_table(ai_start: str) -> pd.DataFrame:
    P, U = fred("ophnfb"), fred("ulcnfb")
    last = P.index[-1].strftime("%Y-%m-%d")
    periods = [
        ("Pre-pandemic", "2015-01-01", "2019-10-01"),
        ("Pandemic & recovery", "2019-10-01", ai_start),
        ("Gen-AI era", ai_start, last),
    ]
    rows = []
    for name, a, b in periods:
        label = f"{name}\n{qlabel(pd.Timestamp(a))}–{qlabel(pd.Timestamp(b))}"
        rows.append({"period": label, "start": qlabel(pd.Timestamp(a)), "end": qlabel(pd.Timestamp(b)),
                     "output_per_hour_pct_yr": annualised_growth(P, a, b),
                     "unit_labour_cost_pct_yr": annualised_growth(U, a, b)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# 4. Lineage registry — filled as figures are computed, shown in the Method tab
# --------------------------------------------------------------------------------------
LINEAGE: list[dict] = []


def record(label: str, value: str, source_keys: list[str], how: str) -> str:
    files = " + ".join(SOURCES[k]["file"] for k in source_keys)
    LINEAGE.append({"Figure": label, "Value": value, "Source file(s)": files, "How it was computed": how})
    return f"**Source:** {files}  \n**How:** {how}"


def data_expander(df: pd.DataFrame, source_keys: list[str], how: str, key: str):
    with st.expander("Data behind this chart"):
        st.caption(" · ".join(f"[{SOURCES[k]['publisher']}]({SOURCES[k]['url']}) — `{SOURCES[k]['file']}`" for k in source_keys))
        st.markdown(f"**Transformation:** {how}")
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button("Download as CSV", df.to_csv(index=False).encode(), file_name=f"{key}.csv", mime="text/csv", key=f"dl_{key}")


def style(fig: go.Figure, y_title: str = "", height: int = 380, y_suffix: str = "", y_prefix: str = "") -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                      yaxis=dict(title=y_title, ticksuffix=y_suffix, tickprefix=y_prefix, gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                      xaxis=dict(showgrid=False), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


# --------------------------------------------------------------------------------------
# 5. Gen-AI era start (fixed)
# --------------------------------------------------------------------------------------
P_all = fred("ophnfb")
quarters = [t.strftime("%Y-%m-%d") for t in P_all.index]
ai_start = AI_ERA_START  # fixed: 2022Q4, the first full quarter after ChatGPT's launch (30 Nov 2022)

# --------------------------------------------------------------------------------------
# 6. Compute headline figures
# --------------------------------------------------------------------------------------
comp = load("companies")
allg = comp[comp["Entity"] == "All geographies"].set_index("Year")["Organizations reporting having adopted AI"]
gi = load("genai").set_index("Year")["Global investment in generative AI"]
q = quarterly_frame(ai_start)
per = period_table(ai_start)
last_q = q.index[-1]
pre_share = q.loc["2015":"2019", "profit_share_pct"].mean()

k_adopt = allg[2025]; k_adopt_chg = allg[2025] - allg[2022]
k_gi = gi[2025] / 1e9; k_gi_mult = gi[2025] / gi[2022]
k_prod_ai, k_prod_pre = per.loc[2, "output_per_hour_pct_yr"], per.loc[0, "output_per_hour_pct_yr"]
k_ulc_ai, k_ulc_mid = per.loc[2, "unit_labour_cost_pct_yr"], per.loc[1, "unit_labour_cost_pct_yr"]
k_share = q["profit_share_pct"].iloc[-1]
k_profit_growth = (q["corporate_profits_bn"].iloc[-1] / q.loc[pd.Timestamp(ai_start), "corporate_profits_bn"] - 1) * 100
k_gdp_growth = (q["gdp_bn"].iloc[-1] / q.loc[pd.Timestamp(ai_start), "gdp_bn"] - 1) * 100
ai_q, end_q = qlabel(pd.Timestamp(ai_start)), qlabel(last_q)

h_adopt = record("Organisations using AI, 2025", f"{k_adopt:.0f}%", ["companies"], "Row Entity = 'All geographies', Year = 2025, as published.")
h_adopt_chg = record("Change in organisational adoption 2022→2025", f"{k_adopt_chg:+.0f} pp", ["companies"], "2025 value − 2022 value (All geographies).")
h_gi = record("Gen-AI private investment, 2025", f"${k_gi:.1f}bn", ["genai"], "Year = 2025 value ÷ 1e9 (constant 2021 US$).")
h_gi_mult = record("Gen-AI investment, 2025 vs 2022", f"{k_gi_mult:.0f}×", ["genai"], "2025 value ÷ 2022 value.")
h_prod = record(f"Productivity growth, {ai_q}–{end_q}", f"{k_prod_ai:.2f}%/yr", ["ophnfb"], f"(OPHNFB[{end_q}] ÷ OPHNFB[{ai_q}])^(4 ÷ quarters) − 1.")
h_prod_pre = record("Productivity growth, 2015Q1–2019Q4", f"{k_prod_pre:.2f}%/yr", ["ophnfb"], "(OPHNFB[2019Q4] ÷ OPHNFB[2015Q1])^(4 ÷ 19) − 1.")
h_ulc = record(f"Unit labour cost growth, {ai_q}–{end_q}", f"{k_ulc_ai:.2f}%/yr", ["ulcnfb"], "Same annualisation applied to ULCNFB.")
h_ulc_mid = record(f"Unit labour cost growth, 2019Q4–{ai_q}", f"{k_ulc_mid:.2f}%/yr", ["ulcnfb"], "Same annualisation applied to ULCNFB.")
h_share = record(f"Corporate profits as % of GDP, {end_q}", f"{k_share:.2f}%", ["cp", "gdp"], "CP ÷ GDP × 100 for the latest quarter.")
h_share_pre = record("Corporate profits as % of GDP, 2015–2019 average", f"{pre_share:.2f}%", ["cp", "gdp"], "Mean of quarterly CP ÷ GDP × 100 over 2015Q1–2019Q4 (20 quarters).")
h_pg = record(f"Corporate profit growth, {ai_q}→{end_q}", f"{k_profit_growth:+.1f}%", ["cp"], f"CP[{end_q}] ÷ CP[{ai_q}] − 1.")
h_gg = record(f"Nominal GDP growth, {ai_q}→{end_q}", f"{k_gdp_growth:+.1f}%", ["gdp"], f"GDP[{end_q}] ÷ GDP[{ai_q}] − 1.")


# --------------------------------------------------------------------------------------
# 6b. Country, industry and gains-capture data (Eurostat, FRED, OWID)
# --------------------------------------------------------------------------------------
@st.cache_data
def eu_long(key: str, col: str | None = None, val: str | None = None) -> pd.DataFrame:
    """Raw Eurostat file → (geo, year, value) with the requested slice. Blank values (confidential/missing) become NaN."""
    df = load(key)
    if col:
        df = df[df[col] == val]
    out = df[["geo", "year", "value"]].copy()
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["value"])


def growth_since(df: pd.DataFrame, base_year: int) -> pd.DataFrame:
    """Index series → cumulative % change since base_year, per geo."""
    base = df[df["year"] == base_year].set_index("geo")["value"]
    out = df[df["geo"].isin(base.index)].copy()
    out["value"] = (out["value"] / out["geo"].map(base) - 1) * 100
    return out


OUTCOMES = {
    "AI adoption (% of enterprises)": dict(
        get=lambda: eu_long("eu_ai", "indic_is", "E_AI_TANY"), higher=True, unit="%", keys=["eu_ai"],
        how="E_AI_TANY value as published.",
        change=lambda w: (w.get(2025) - w.get(2021)), change_label="Change 2021→2025 (pp)"),
    "Productivity growth since 2019 (%)": dict(
        get=lambda: growth_since(eu_long("eu_lp", "na_item", "RLPR_HW"), 2019), higher=True, unit="%", keys=["eu_lp"],
        how="RLPR_HW index ÷ its 2019 value − 1.",
        change=lambda w: None, change_label="Productivity growth 2021→2025 (%)"),
    "Profit share of companies (%)": dict(
        get=lambda: eu_long("eu_profit"), higher=True, unit="%", keys=["eu_profit"],
        how="B2G_B3G_RAT_S11 as published.",
        change=lambda w: (w.get(2024) - w.get(2021)), change_label="Change in profit share 2021→2024 (pp)"),
    "Unit labour cost growth since 2019 (%)": dict(
        get=lambda: growth_since(eu_long("eu_lp", "na_item", "NULC_HW"), 2019), higher=False, unit="%", keys=["eu_lp"],
        how="NULC_HW index ÷ its 2019 value − 1. Lower ranks better (cheaper output).",
        change=lambda w: None, change_label="Unit labour cost growth 2021→2025 (%)"),
    "Unemployment rate (%)": dict(
        get=lambda: eu_long("eu_unemp", "age", "Y15-74"), higher=False, unit="%", keys=["eu_unemp"],
        how="Age 15–74, as published. Lower ranks better.",
        change=lambda w: (w.get(2025) - w.get(2021)), change_label="Change in unemployment 2021→2025 (pp)"),
    "Youth unemployment rate (%)": dict(
        get=lambda: eu_long("eu_unemp", "age", "Y15-24"), higher=False, unit="%", keys=["eu_unemp"],
        how="Age 15–24, as published. Lower ranks better.",
        change=lambda w: (w.get(2025) - w.get(2021)), change_label="Change in youth unemployment 2021→2025 (pp)"),
    "Real consumption growth per person (%)": dict(
        get=lambda: eu_long("eu_cons"), higher=True, unit="%", keys=["eu_cons"],
        how="P4_R_HAB_GR (% change on previous year), as published.",
        change=lambda w: pd.concat([w.get(2022), w.get(2023), w.get(2024)], axis=1).mean(axis=1, skipna=False),
        change_label="Average real consumption growth 2022–2024 (%)"),
}


def change_table(name: str) -> pd.Series:
    """Per-country change in an outcome over the AI-adoption period (definitions in OUTCOMES)."""
    if name.startswith("Productivity"):
        w = eu_long("eu_lp", "na_item", "RLPR_HW").pivot(index="geo", columns="year", values="value")
        return (w.get(2025) / w.get(2021) - 1) * 100
    if name.startswith("Unit labour"):
        w = eu_long("eu_lp", "na_item", "NULC_HW").pivot(index="geo", columns="year", values="value")
        return (w.get(2025) / w.get(2021) - 1) * 100
    w = OUTCOMES[name]["get"]().pivot(index="geo", columns="year", values="value")
    return OUTCOMES[name]["change"](w)


ai_cty = eu_long("eu_ai", "indic_is", "E_AI_TANY")
ai_wide = ai_cty.pivot(index="geo", columns="year", values="value")
countries_ranked = ai_wide[~ai_wide.index.isin(AGGREGATES)][2025].dropna().sort_values(ascending=False)


def corr(x: pd.Series, y: pd.Series):
    from scipy import stats
    d = pd.concat([x, y], axis=1).dropna()
    if len(d) < 4:
        return None
    r, p = stats.pearsonr(d.iloc[:, 0], d.iloc[:, 1])
    return dict(r=r, p=p, n=len(d))


cty_x = (ai_wide[2025] - ai_wide[2021]).drop(index=list(AGGREGATES), errors="ignore")
c_prod = corr(cty_x, change_table("Productivity growth since 2019 (%)"))
c_profit = corr(cty_x, change_table("Profit share of companies (%)"))


# Industry frame
@st.cache_data
def industry_frame() -> pd.DataFrame:
    ai = load("ind_ai").assign(value=lambda d: pd.to_numeric(d["value"], errors="coerce"))
    g = load("ind_gva"); h = load("ind_hours")
    real = g[(g["unit"] == "CLV20_MEUR") & (g["na_item"] == "B1G")].pivot(index="nace_r2", columns="year", values="value")
    nom = g[(g["unit"] == "CP_MEUR") & (g["na_item"] == "B1G")].pivot(index="nace_r2", columns="year", values="value")
    pay = g[(g["unit"] == "CP_MEUR") & (g["na_item"] == "D1")].pivot(index="nace_r2", columns="year", values="value")
    hrs = h.pivot(index="nace_r2", columns="year", values="value")
    prod = real / hrs
    rows = []
    for code, (ai_codes, name) in INDUSTRY_MAP.items():
        for yr in range(2019, 2026):
            a = ai[(ai["nace_r2"].isin(ai_codes)) & (ai["year"] == yr)]["value"]
            rows.append(dict(code=code, industry=name, year=yr,
                             ai_adoption_pct=a.mean() if len(a) == len(ai_codes) else None,
                             productivity_growth_since_2019_pct=(prod.loc[code, yr] / prod.loc[code, 2019] - 1) * 100,
                             non_wage_share_pct=(1 - pay.loc[code, yr] / nom.loc[code, yr]) * 100,
                             real_gva_meur=real.loc[code, yr], hours_ths=hrs.loc[code, yr]))
    return pd.DataFrame(rows)


ind = industry_frame()
ind_w = ind.pivot(index="industry", columns="year")
ind_summary = pd.DataFrame({
    "AI adoption 2021 (%)": ind_w["ai_adoption_pct"][2021], "AI adoption 2025 (%)": ind_w["ai_adoption_pct"][2025],
    "Productivity growth 2021→2025 (%)": ((1 + ind_w["productivity_growth_since_2019_pct"][2025] / 100) /
                                          (1 + ind_w["productivity_growth_since_2019_pct"][2021] / 100) - 1) * 100,
    "Non-wage share change 2021→2025 (pp)": ind_w["non_wage_share_pct"][2025] - ind_w["non_wage_share_pct"][2021],
}).reset_index()
c_ind = corr(ind_summary["AI adoption 2025 (%)"], ind_summary["Productivity growth 2021→2025 (%)"])

h_cprod = record("Country correlation: AI adoption change vs productivity growth", f"r = {c_prod['r']:.2f} (n = {c_prod['n']})",
                 ["eu_ai", "eu_lp"], "Pearson r across European countries between (AI 2025 − AI 2021) and (RLPR_HW 2025 ÷ 2021 − 1); aggregates excluded.")
h_cprofit = record("Country correlation: AI adoption change vs profit-share change", f"r = {c_profit['r']:.2f} (n = {c_profit['n']})",
                   ["eu_ai", "eu_profit"], "Pearson r between (AI 2025 − AI 2021) and (profit share 2024 − 2021).")
h_cind = record("Industry correlation: AI adoption 2025 vs productivity growth", f"r = {c_ind['r']:.2f} (n = {c_ind['n']})",
                ["ind_ai", "ind_gva", "ind_hours"], "Pearson r across 6 EU27 industries; productivity = real GVA ÷ hours worked, 2025 ÷ 2021 − 1.")

# --------------------------------------------------------------------------------------
# Shared chart helpers (bump chart, scatter with fit, correlation text)
# --------------------------------------------------------------------------------------
PALETTE10 = ["#2563EB", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#0EA5E9", "#EC4899", "#84CC16", "#F97316", "#64748B"]


def bump_chart(long: pd.DataFrame, entity: str, period: str, value: str, higher_is_better: bool,
               value_fmt=lambda v: f"{v:.1f}", height: int = 430, colors: dict | None = None) -> tuple[go.Figure, pd.DataFrame]:
    """Rank entities within each period (1 = best) and draw a bump chart. Returns the figure and the ranked table."""
    d = long.dropna(subset=[value]).copy()
    d["rank"] = d.groupby(period)[value].rank(ascending=not higher_is_better, method="min").astype(int)
    ents = list(d.sort_values([period, "rank"]).groupby(entity).tail(1).sort_values("rank")[entity])
    fig = go.Figure()
    for i, e in enumerate(ents):
        s = d[d[entity] == e].sort_values(period)
        colr = (colors or {}).get(e, PALETTE10[i % len(PALETTE10)])
        fig.add_scatter(x=s[period], y=s["rank"], mode="lines+markers", name=e, line=dict(color=colr, width=3, shape="linear"),
                        marker=dict(size=13, color=colr, line=dict(color="white", width=2)),
                        customdata=s[[value]].values, hovertemplate=f"<b>{e}</b><br>%{{x}}: rank %{{y}}<br>value %{{customdata[0]:.2f}}<extra></extra>")
        last, first = s.iloc[-1], s.iloc[0]
        fig.add_annotation(x=last[period], y=last["rank"], text=f"{e} ({value_fmt(last[value])})", showarrow=False, xanchor="left", xshift=12,
                           font=dict(size=12, color=colr))
        fig.add_annotation(x=first[period], y=first["rank"], text=f"{int(first['rank'])}. {e}", showarrow=False, xanchor="right", xshift=-12, font=dict(size=11, color=colr))
    n = int(d["rank"].max()) if len(d) else 1
    periods = sorted(d[period].unique())
    fig.update_layout(height=height, showlegend=False, margin=dict(l=120, r=190, t=10, b=30), hovermode="closest",
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      yaxis=dict(autorange="reversed", tickmode="array", tickvals=list(range(1, n + 1)), showticklabels=False, title=None, gridcolor="rgba(128,128,128,0.12)", zeroline=False),
                      xaxis=dict(tickmode="array", tickvals=periods, showgrid=False, range=[min(periods) - 0.25, max(periods) + 0.25] if periods else None))
    return fig, d.sort_values([period, "rank"])


def scatter_fit(df: pd.DataFrame, x: str, y: str, label: str, highlight: set, xtitle: str, ytitle: str, height: int = 430) -> go.Figure:
    d = df.dropna(subset=[x, y])
    fig = go.Figure()
    other, top = d[~d[label].isin(highlight)], d[d[label].isin(highlight)]
    fig.add_scatter(x=other[x], y=other[y], mode="markers+text", text=other[label], textposition="top center", name="Other countries",
                    marker=dict(size=9, color=COLORS["muted"]), textfont=dict(size=10, color=COLORS["sixth"]),
                    hovertemplate="%{text}<br>x %{x:.1f}<br>y %{y:.2f}<extra></extra>")
    fig.add_scatter(x=top[x], y=top[y], mode="markers+text", text=top[label], textposition="top center", name="Selected top adopters",
                    marker=dict(size=12, color=COLORS["accent"]), textfont=dict(size=11, color=COLORS["accent"]),
                    hovertemplate="%{text}<br>x %{x:.1f}<br>y %{y:.2f}<extra></extra>")
    if len(d) >= 3:
        import numpy as np
        b, a = np.polyfit(d[x], d[y], 1)
        xs = np.linspace(d[x].min(), d[x].max(), 20)
        fig.add_scatter(x=xs, y=a + b * xs, mode="lines", name="Linear fit", line=dict(color=COLORS["fourth"], dash="dash", width=2), hoverinfo="skip")
    fig.add_hline(y=0, line_color=COLORS["muted"], line_width=1)
    style(fig, ytitle, height=height).update_layout(hovermode="closest").update_xaxes(title=xtitle, showgrid=True, gridcolor="rgba(128,128,128,0.12)")
    return fig


def corr_text(c: dict | None) -> str:
    if not c:
        return "Too few observations for a correlation."
    sig = "statistically significant at 5%" if c["p"] < 0.05 else "not statistically significant"
    return f"r = **{c['r']:+.2f}**, n = {c['n']}, p = {c['p']:.2f} ({sig})"

# ======================================================================================
# 8. NEW SOURCES (recommended sources: OWID AI pages, Microsoft via OWID, IEA via OWID, Census via OWID, Eurostat, FRED)
# ======================================================================================
SOURCES.update({
    "cset": dict(
        file="owid_private-investment-in-artificial-intelligence-cset.csv",
        title="Funding raised by privately held AI companies, by country",
        publisher="Center for Security and Emerging Technology (CSET) via Our World in Data (AI pages)",
        url="https://ourworldindata.org/grapher/private-investment-in-artificial-intelligence-cset",
        notes="Venture capital, private equity and M&A money raised by private AI companies, by the company's country; constant 2021 US$ "
              "(US CPI). Includes CSET estimates for undisclosed deals; excludes Big Tech's own spending. Extract: years 2022–2025, all entities.",
    ),
    "ilo_oph_c": dict(
        file="ilo_output_per_hour_countries.csv",
        title="Output per hour worked, by country",
        publisher="ILO modelled estimates via ILOSTAT SDMX (DF_GDP_2HRW_NOC_NB)",
        url="https://sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB/all?startPeriod=2015&endPeriod=2025&format=csv",
        notes="GDP per hour worked, constant 2021 int-$ PPP. Extract: country rows (regional 'X' codes dropped), years 2015, 2019, 2022, 2025 only; 2025 is a nowcast.",
    ),
    "gdppc_growth": dict(
        file="owid_gdp-per-capita-growth.csv",
        title="GDP per person, annual growth (inflation-adjusted)",
        publisher="World Bank, World Development Indicators via Our World in Data",
        url="https://ourworldindata.org/grapher/gdp-per-capita-growth",
        notes="NY.GDP.PCAP.KD.ZG, annual %, constant prices; World Bank regional aggregates, EU-27 and World. Filtered to 2015 onward and 7 regions.",
    ),
    "genai_use": dict(
        file="owid_estimated-share-people-generative-ai.csv",
        title="Working-age adults using generative AI, by country",
        publisher="Microsoft AI Economy Institute via Our World in Data (AI pages)",
        url="https://ourworldindata.org/grapher/estimated-share-people-generative-ai",
        notes="% of people aged 15–64 who used a gen-AI website or app in the period; Jun 2025, Dec 2025, Mar 2026. Includes GDP per capita "
              "(World Bank/IMF/OECD/Eurostat, 2021 int-$) and OWID region.",
    ),
    "dc_build": dict(
        file="owid_monthly-spending-data-center-us.csv",
        title="US data-centre construction spending",
        publisher="US Census Bureau (construction spending) via Our World in Data",
        url="https://ourworldindata.org/grapher/monthly-spending-data-center-us",
        notes="Monthly private spending on building data centres, constant 2021 US$; excludes servers and IT hardware. Filtered to 2019 onward.",
    ),
    "dc_power": dict(
        file="owid_data-centers-share-electricity-demand.csv",
        title="Data centres' share of electricity demand",
        publisher="International Energy Agency (Energy and AI) via Our World in Data",
        url="https://ourworldindata.org/grapher/data-centers-share-electricity-demand",
        notes="% of total electricity demand used by data centres; 2020, 2023–2025. Covers all data-centre uses, not only AI.",
    ),
    "coe": dict(
        file="fred_COE.csv",
        title="US compensation of employees",
        publisher="US Bureau of Economic Analysis via FRED, series COE",
        url="https://fred.stlouisfed.org/series/COE",
        notes="Total pay (wages, salaries and benefits) paid to employees, US$bn SAAR, quarterly.",
    ),
    "eu_barriers": dict(
        file="eurostat_isoc_eb_ai_barriers.csv",
        title="Why EU firms do not use AI",
        publisher="Eurostat, ICT usage in enterprises survey (isoc_eb_ai)",
        url="https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table",
        notes="EU-27, enterprises with 10+ employees, % of all enterprises. E_AI_EC = considered using AI but don't; barrier codes B* are asked of that group.",
    ),
    "eu_size": dict(
        file="eurostat_isoc_eb_ai_size.csv",
        title="EU firms using AI, by size",
        publisher="Eurostat, ICT usage in enterprises survey (isoc_eb_ai)",
        url="https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table",
        notes="EU-27, % of enterprises using at least one AI technology, by number of employees.",
    ),
})

# ======================================================================================
# 9. THEME — professional dark "tech" style
# ======================================================================================
BLUE, TEAL, AMBER, RED, VIOLET, GREEN, SLATE, MUTED = "#3B82F6", "#14B8A6", "#F59E0B", "#EF4444", "#A78BFA", "#22C55E", "#94A3B8", "#475569"
PAL = [BLUE, TEAL, AMBER, VIOLET, "#F472B6", "#38BDF8", RED, GREEN]
BG, PANEL, EDGE, GRID, TEXT, SUB = "#0B1220", "#0F172A", "#1E293B", "#1E293B", "#E2E8F0", "#94A3B8"
H = 400

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {{font-family: 'Inter', sans-serif;}}
.stApp {{background-color: {BG};
  background-image: linear-gradient(rgba(148,163,184,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.045) 1px, transparent 1px);
  background-size: 32px 32px;}}
.block-container {{padding-top: 2.6rem; padding-bottom: 1.2rem; max-width: 1640px;}}
div[data-testid="stVerticalBlock"] {{gap: 0.6rem;}}
div[data-testid="stVerticalBlockBorderWrapper"] {{background: {PANEL}; border: 1px solid {EDGE} !important; border-radius: 8px;}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{padding: 0.5rem 0.75rem 0.3rem 0.75rem;}}
.banner {{background: linear-gradient(90deg, #0F172A 0%, #111C33 100%); border: 1px solid {EDGE}; border-left: 4px solid {BLUE};
          border-radius: 8px; padding: 14px 20px; margin-bottom: 8px;}}
.banner .eyebrow {{color: {BLUE}; font-size: .72rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase;}}
.banner .bt {{color: {TEXT}; font-size: 1.6rem; font-weight: 700; line-height: 1.25; margin-top: 2px;}}
.banner p {{color: {SUB}; margin: 4px 0 0 0; font-size: .88rem;}}
.banner b {{color: {TEXT};}}
.sec {{margin: 18px 0 4px 0; display: flex; align-items: baseline; gap: 12px;}}
.sec .q {{color: {TEXT}; font-size: 1.2rem; font-weight: 700;}}
.sec .tag {{color: {BLUE}; font-size: .72rem; font-weight: 600; letter-spacing: .14em; text-transform: uppercase;}}
.sec-line {{height: 1px; background: linear-gradient(90deg, {BLUE} 0%, rgba(59,130,246,0) 70%); margin-bottom: 6px;}}
.ct {{font-weight: 600; font-size: 1rem; color: {TEXT}; line-height: 1.3;}}
.cs {{font-size: .78rem; color: {SUB}; line-height: 1.3; margin-top: 1px;}}
.kpi {{background: {PANEL}; border: 1px solid {EDGE}; border-radius: 8px; padding: 10px 14px; height: 100%;}}
.kpi .kh {{color: {SUB}; font-size: .7rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;}}
.kpi .kv {{color: {TEXT}; font-size: 1.9rem; font-weight: 700; line-height: 1.2; margin-top: 4px;}}
.kpi .kd {{font-size: .76rem; color: {SUB}; margin-top: 2px;}}
.kpi .up {{color: {GREEN}; font-weight: 600;}} .kpi .dn {{color: {RED}; font-weight: 600;}} .kpi .nt {{color: {AMBER}; font-weight: 600;}}
.imp {{background: {PANEL}; border: 1px solid {EDGE}; border-top: 3px solid {TEAL}; border-radius: 8px; padding: 12px 16px; height: 100%;}}
.imp .ih {{color: {TEXT}; font-weight: 700; font-size: 1rem;}}
.imp .ib {{color: {SUB}; font-size: .84rem; margin-top: 4px; line-height: 1.4;}}
div[data-testid="stPopover"] button {{padding: 0 8px; min-height: 1.5rem; font-size: .75rem; border-color: {EDGE}; background: transparent;}}
</style>
""", unsafe_allow_html=True)


def mini(fig: go.Figure, h: int = H, ysuf: str = "", ypre: str = "", legend: bool = True, ytitle: str = "", xtitle: str = "") -> go.Figure:
    fig.update_layout(height=h, margin=dict(l=4, r=8, t=8, b=4), font=dict(family="Inter, sans-serif", size=12, color="#CBD5E1"),
                      hovermode="x unified", hoverlabel=dict(bgcolor="#1E293B", bordercolor="#334155", font=dict(color=TEXT)),
                      showlegend=legend, legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      yaxis=dict(ticksuffix=ysuf, tickprefix=ypre, gridcolor=GRID, zeroline=False, linecolor=GRID, title=dict(text=ytitle, font=dict(size=11))),
                      xaxis=dict(showgrid=False, linecolor="#334155", title=dict(text=xtitle, font=dict(size=11))))
    return fig


def card(title: str, sub: str, fig: go.Figure | None, df: pd.DataFrame, keys: list[str], how: str, key: str, before=None):
    """A panel: action title (the takeaway) + source line, a small ⓘ popover with file / transformation / table, then the chart."""
    with st.container(border=True):
        t, p = st.columns([9, 1])
        t.markdown(f"<div class='ct'>{title}</div><div class='cs'>{sub}</div>", unsafe_allow_html=True)
        with p.popover("ⓘ", help="Source file, transformation and the exact table plotted"):
            st.caption(" · ".join(f"[{SOURCES[k]['publisher']}]({SOURCES[k]['url']}) — `{SOURCES[k]['file']}`" for k in keys))
            st.markdown(f"**Transformation:** {how}")
            st.dataframe(df, hide_index=True, height=280)
            st.download_button("CSV", df.to_csv(index=False).encode(), f"{key}.csv", "text/csv", key=f"dl_{key}")
        if before:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            before()
        if fig is not None:
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=f"ch_{key}")


def plain(label: str) -> str:
    t = label.replace(" (%)", "").replace(" (pp)", "")
    return t[0].lower() + t[1:]


def kpi(col, head: str, value: str, delta: str, cls: str = ""):
    col.markdown(f"<div class='kpi'><div class='kh'>{head}</div><div class='kv'>{value}</div><div class='kd'><span class='{cls}'>{delta}</span></div></div>",
                 unsafe_allow_html=True)


def section(question: str, tag: str, anchor: str):
    st.markdown(f"<div class='sec' id='{anchor}'><span class='tag'>{tag}</span><span class='q'>{question}</span></div><div class='sec-line'></div>",
                unsafe_allow_html=True)


# ======================================================================================
# 10. NUMBERS (all derived from the files; each headline figure is recorded in the lineage table)
# ======================================================================================
ILO_AREAS = {"X01": "World", "X34": "North America", "X92": "EU-27", "X88": "G7", "X45": "East Asia",
             "X56": "South Asia", "X26": "Latin America", "X13": "Sub-Saharan Africa"}
LAST_ILO = 2025  # ILO Nov-2025 release: 2025 is a nowcast; later projections are not used


def ilo(key: str) -> pd.DataFrame:  # not cached: cheap, and avoids a stale region map after edits
    d = load(key)
    d = d[d["year"] <= LAST_ILO].copy()
    d["region"] = d["ref_area"].map(ILO_AREAS)
    return d


oph = ilo("ilo_oph").pivot(index="region", columns="year", values="value")
lis = ilo("ilo_lis").pivot(index="region", columns="year", values="value")
prod_reg = pd.DataFrame({"2015–19": ((oph[2019] / oph[2015]) ** (1 / 4) - 1) * 100,
                         "2022–25": ((oph[2025] / oph[2022]) ** (1 / 3) - 1) * 100}).round(2)
w_pre, w_post = prod_reg.loc["World", "2015–19"], prod_reg.loc["World", "2022–25"]
ls_chg = (lis[2025] - lis[2019]).round(2)
record("World output per hour, annual growth 2022–25 vs 2015–19", f"{w_post:.2f}% vs {w_pre:.2f}%", ["ilo_oph"],
       "Region X01: (2025 ÷ 2022)^(1/3) − 1 and (2019 ÷ 2015)^(1/4) − 1.")

# adoption
gu = load("genai_use").rename(columns={"Estimated share of working-age adults who use generative AI": "share", "GDP per capita": "gdppc",
                                       "World region according to OWID": "region"})
gu_last_day = gu["Day"].max()
gu_now = gu[(gu["Day"] == gu_last_day) & (gu["Code"].str.len() == 3)].copy()
gu_world = gu[gu["Entity"] == "World"].set_index("Day")["share"]
top3 = gu_now.sort_values("share", ascending=False).head(3)["Entity"].tolist()
record(f"Working-age adults using gen AI worldwide, {gu_last_day}", f"{gu_world[gu_last_day]:.1f}% (Jun 2025: {gu_world['2025-06-30']:.1f}%)",
       ["genai_use"], "Row Entity = World, as published (Microsoft's population-weighted figure).")

# capital
dcm = load("dc_build").copy()
dcm["date"] = pd.to_datetime(dcm["Month"] + "-01")
dcm["bn"] = dcm["Data center construction"] / 1e9
dc_year = dcm.assign(year=dcm["date"].dt.year).groupby("year")["bn"].sum()
dc_mult = dc_year[2025] / dc_year[2022]
record("US data-centre construction spending, 2025 (vs 2022)", f"${dc_year[2025]:.1f}bn ({dc_mult:.1f}× 2022)", ["dc_build"],
       "Sum of the 12 monthly values for each calendar year ÷ 1e9 (constant 2021 US$).")
_cs = load("cset").set_index(["Entity", "Year"]).iloc[:, -1] / 1e9
cset_world = _cs.loc["World"]
cset_us_share25 = _cs.loc[("United States", 2025)] / cset_world[2025] * 100
record("Private AI funding worldwide, 2025 (vs 2022)", f"${cset_world[2025]:.0f}bn ({cset_world[2025] / cset_world[2022]:.1f}× 2022)", ["cset"],
       "World row ÷ 1e9 (constant 2021 US$).")
nv = load("nvidia")
dcrev = nv[nv["Entity"] == "Data centers and AI"].set_index("Quarter")["NVIDIA’s quarterly revenue"] / 1e9
nv_mult = dcrev.iloc[-1] / dcrev["2022-Q4"]
record("NVIDIA data-centre revenue, latest quarter vs 2022-Q4", f"{nv_mult:.1f}×", ["nvidia"], f"{dcrev.index[-1]} ÷ 2022-Q4.")
pw = load("dc_power").rename(columns={"Share of total electricity demand coming from data centers": "share"})

# payoff
eu_ps = eu_long("eu_profit")
eu27 = eu_ps[eu_ps["geo"] == "EU27_2020"].set_index("year")["value"]
us_ps_year = q.assign(year=q.index.year).groupby("year")["profit_share_pct"].mean()

# who gains
COE = fred("coe")
CPs = fred("cp")
base = pd.Timestamp(AI_ERA_START)
pg = (CPs.iloc[-1] / CPs[base] - 1) * 100
wg = (COE.iloc[-1] / COE[base] - 1) * 100
record("US corporate profits vs employee pay, growth since 2022Q4", f"profits {pg:+.1f}% · pay {wg:+.1f}%", ["cp", "coe"],
       f"CP[{qlabel(CPs.index[-1])}] ÷ CP[2022Q4] − 1 and COE[{qlabel(COE.index[-1])}] ÷ COE[2022Q4] − 1 (both nominal US$bn SAAR).")

# barriers & size
bar = load("eu_barriers").pivot(index="indic_is", columns="year", values="value")
considered = bar.loc["E_AI_EC", 2025]
BARRIER_NAMES = {"E_AI_BLE": "Lack of expertise", "E_AI_BLEG": "Unclear legal consequences", "E_AI_BCDP": "Data-protection & privacy concerns",
                 "E_AI_BDDT": "Data availability or quality", "E_AI_BINC": "Incompatible with existing systems", "E_AI_BCST": "Costs seem too high",
                 "E_AI_BEC": "Ethical concerns", "E_AI_BNU": "Not useful for the business"}
barriers = pd.DataFrame({"barrier": [BARRIER_NAMES[k] for k in BARRIER_NAMES], "pct_of_all_firms": [bar.loc[k, 2025] for k in BARRIER_NAMES]})
barriers["pct_of_firms_that_considered_AI"] = (barriers["pct_of_all_firms"] / considered * 100).round(1)
barriers = barriers.sort_values("pct_of_firms_that_considered_AI")
top_bar = barriers.iloc[-1]
cost_bar = barriers[barriers["barrier"] == "Costs seem too high"].iloc[0]
record("Top barrier among EU firms that considered AI, 2025", f"{top_bar['barrier']}: {top_bar['pct_of_firms_that_considered_AI']:.0f}%", ["eu_barriers"],
       f"E_AI_BLE ÷ E_AI_EC × 100 = {bar.loc['E_AI_BLE', 2025]} ÷ {considered} × 100.")
sz = load("eu_size").pivot(index="size_emp", columns="year", values="value")
large_small = sz.loc["GE250", 2025] / sz.loc["10-49", 2025]

# industries & countries
SHORT_IND = {"Information & communication": "ICT", "Professional & admin services": "Professional & admin", "Trade, transport & hospitality": "Trade & transport",
             "Manufacturing": "Manufacturing", "Real estate": "Real estate", "Construction": "Construction"}
gva25 = load("ind_gva")
gva25 = gva25[(gva25["unit"] == "CP_MEUR") & (gva25["na_item"] == "B1G") & (gva25["year"] == 2025)].set_index("nace_r2")["value"]
ind_b = ind_summary.copy()
ind_b["code"] = ind_b["industry"].map({v[1]: k for k, v in INDUSTRY_MAP.items()})
ind_b["gva_2025_bn_eur"] = (ind_b["code"].map(gva25) / 1000).round(0)
ind_b["label"] = ind_b["industry"].map(SHORT_IND)
ind_top = ind_b.sort_values("AI adoption 2025 (%)").iloc[-1]
ind_low = ind_b.sort_values("AI adoption 2025 (%)").iloc[0]

# ======================================================================================
# 11. THE PAGE
# ======================================================================================
st.markdown(f"<div class='banner'><div class='eyebrow'>Investment brief · AI adoption</div>"
            f"<div class='bt'>Will investing in AI lift our productivity and profits?</div>"
            f"<p><b>Group question:</b> {GROUP_QUESTION}<br><b>My part:</b> {QUESTION} &nbsp;·&nbsp; <b>Audience:</b> {PERSONA}</p></div>", unsafe_allow_html=True)

k = st.columns(5)
kpi(k[0], "Firms using AI · 2025", f"{k_adopt:.0f}%", f"▲ {k_adopt_chg:+.0f} pp vs 2022", "up")
kpi(k[1], f"Adults using gen AI · world", f"{gu_world[gu_last_day]:.1f}%", f"▲ from {gu_world['2025-06-30']:.1f}% in Jun 2025", "up")
kpi(k[2], "Private AI funding · 2025", f"${cset_world[2025]:.0f}bn", f"▲ {cset_world[2025] / cset_world[2022]:.1f}× 2022 · US {cset_us_share25:.0f}%", "nt")
kpi(k[3], "World productivity growth", f"{w_post:.1f}%/yr", f"▼ 2022–25 vs {w_pre:.1f}% in 2015–19", "dn")
kpi(k[4], "US profits vs pay · since 2022", f"{pg:+.0f}%", f"vs employee pay {wg:+.0f}%", "nt")

# --------------------------------------------------------------------------------------
section("Is AI becoming standard practice?", "Adoption", "adoption")
c1, c2 = st.columns(2)
with c1:
    REG_COL = {"Europe": BLUE, "North America": TEAL, "Asia": AMBER, "Oceania": VIOLET, "South America": "#F472B6", "Africa": SLATE}
    sc = gu_now.dropna(subset=["gdppc"])
    fig = go.Figure()
    for reg, cl in REG_COL.items():
        d = sc[sc["region"] == reg]
        fig.add_scatter(x=d["gdppc"], y=d["share"], mode="markers", name=reg, marker=dict(size=9, color=cl, opacity=0.8, line=dict(color="#0B1220", width=0.6)),
                        text=d["Entity"], hovertemplate="<b>%{text}</b><br>%{y:.1f}% use gen AI · GDP/person $%{x:,.0f}<extra></extra>")
    lab = sc[sc["Entity"].isin(top3 + ["United States", "China", "India", "Australia", "Germany", "Japan"])]
    fig.add_scatter(x=lab["gdppc"], y=lab["share"], mode="text", text=lab["Entity"], textposition=["bottom center" if e in ("Germany", "China") else ("middle right" if e == "United States" else "top center") for e in lab["Entity"]], textfont=dict(size=10, color=TEXT),
                    showlegend=False, hoverinfo="skip")
    fig.add_hline(y=gu_world[gu_last_day], line_dash="dot", line_color=SLATE,
                  annotation_text=f"World {gu_world[gu_last_day]:.1f}%", annotation_position="top left", annotation_font=dict(size=11, color=SUB))
    card(f"Gen-AI use is global and rising with income — {gu_world[gu_last_day]:.0f}% of adults worldwide, up to {gu_now['share'].max():.0f}% in {top3[0]}",
         f"each dot = a country · % of working-age adults using gen AI ({pd.Timestamp(gu_last_day):%b %Y}) vs GDP per person · Microsoft, World Bank via OWID",
         mini(fig, ysuf="%", xtitle="GDP per person (2021 int-$, log scale)").update_layout(hovermode="closest")
         .update_xaxes(type="log", showgrid=True, gridcolor=GRID, tickprefix="$"),
         gu_now[["Entity", "Code", "Day", "share", "gdppc", "region"]].sort_values("share", ascending=False), ["genai_use"],
         f"Rows with Day = {gu_last_day} and a 3-letter country code; values as published; countries without GDP per capita are omitted from the chart.", "genai_gdp")
with c2:
    fig = go.Figure()
    regs = ["All geographies", "North America", "Europe", "Asia-Pacific", "Greater China", "Developing markets"]
    for i, r in enumerate(regs):
        d = comp[comp["Entity"] == r]
        fig.add_scatter(x=d["Year"], y=d["Organizations reporting having adopted AI"], mode="lines+markers",
                        name={"All geographies": "All regions", "Developing markets": "Developing", "Greater China": "China", "North America": "N. America"}.get(r, r),
                        line=dict(width=4 if i == 0 else 1.6, color=BLUE if i == 0 else [SLATE, TEAL, AMBER, VIOLET, "#F472B6"][i - 1]),
                        marker=dict(size=7 if i == 0 else 4), opacity=1 if i == 0 else 0.75, hovertemplate="%{y:.0f}%")
    card(f"{k_adopt:.0f}% of companies now use AI — up from {allg[2023]:.0f}% in 2023",
         "% of organisations using AI in ≥1 business function · McKinsey survey via AI Index / OWID",
         mini(fig, ysuf="%").update_xaxes(dtick=1), comp[comp["Entity"].isin(regs)], ["companies"], "None — values as published.", "adopt")
c3, c4 = st.columns(2)
with c3:
    hm = ind.dropna(subset=["ai_adoption_pct"]).pivot(index="industry", columns="year", values="ai_adoption_pct")
    hm = hm.loc[hm[2025].sort_values().index]
    hm.index = [SHORT_IND[i] for i in hm.index]
    fig = go.Figure(go.Heatmap(z=hm.values, x=[str(c) for c in hm.columns], y=hm.index, text=hm.round(0).values, texttemplate="%{text:.0f}%",
                               colorscale=[[0, "#0F2A4A"], [0.5, "#1D4ED8"], [1, "#60A5FA"]], showscale=False, xgap=3, ygap=3,
                               hovertemplate="%{y} · %{x}: %{z:.1f}%<extra></extra>"))
    card(f"Adoption depends on the industry — {ind_top['label']} {ind_top['AI adoption 2025 (%)']:.0f}% vs {ind_low['label'].lower()} {ind_low['AI adoption 2025 (%)']:.0f}%",
         "% of EU firms (10+ staff) using AI · Eurostat (no 2022 survey)",
         mini(fig, legend=False).update_layout(hovermode="closest").update_xaxes(side="top", type="category"), hm.round(2).rename(columns=str).reset_index(names="industry"),
         ["ind_ai"], "Mean of the survey sections mapped to each industry (Trade & transport = mean of G, H, I; Professional & admin = mean of M, N).", "heat")
with c4:
    s = sz.loc[["10-49", "50-249", "GE250"]]
    fig = go.Figure()
    for i, (lab, row) in enumerate(zip(["Small (10–49)", "Medium (50–249)", "Large (250+)"], s.itertuples(index=False))):
        fig.add_bar(x=[str(c) for c in s.columns], y=list(row), name=lab, marker_color=[MUTED, TEAL, BLUE][i],
                    text=[f"{v:.0f}%" for v in row], textposition="outside", cliponaxis=False, hovertemplate="%{y:.1f}%")
    card(f"Large firms are {large_small:.1f}× more likely to use AI than small ones",
         "% of EU firms using AI, by number of employees · Eurostat",
         mini(fig, ysuf="%").update_layout(barmode="group", bargap=0.25).update_xaxes(type="category"), s.rename(columns=str).reset_index(), ["eu_size"], "Values as published.", "size")

# --------------------------------------------------------------------------------------
section("How much capital is flowing into AI?", "Investment", "capital")
c1, c2 = st.columns(2)
with c1:
    cs = load("cset").rename(columns={"Estimated funding raised by privately held AI companies - Field: All": "usd"})
    cs_c = cs[cs["Code"].str.len() == 3]
    tot = (cs_c.groupby("Entity")["usd"].sum() / 1e9).sort_values(ascending=False)
    world_tot = cs[cs["Entity"] == "World"]["usd"].sum() / 1e9
    top = tot.head(12)[::-1]
    us_share = tot["United States"] / world_tot * 100
    record("Private AI funding 2022–25, US share of world", f"{us_share:.0f}% (${tot['United States']:.0f}bn of ${world_tot:.0f}bn)", ["cset"],
           "Sum of 2022–2025 values per country ÷ 1e9; US ÷ World row.")
    fig = go.Figure(go.Bar(x=top.values, y=top.index, orientation="h",
                           marker_color=[BLUE if c == "United States" else (TEAL if c == "China" else MUTED) for c in top.index],
                           text=[f"${v:,.0f}bn" for v in top.values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: $%{x:,.1f}bn<extra></extra>"))
    card(f"AI capital is concentrated: US AI companies raised {us_share:.0f}% of the world's ${world_tot:,.0f}bn since 2022",
         "funding raised by private AI companies, 2022–2025 total, constant 2021 US$bn · top 12 countries · CSET via OWID",
         mini(fig, legend=False).update_xaxes(tickprefix="$", ticksuffix="bn", showgrid=True, gridcolor=GRID, range=[0, top.max() * 1.18]),
         tot.round(3).rename("US$bn 2022–25").reset_index().rename(columns={"Entity": "country"}), ["cset"],
         "Country rows (3-letter code), summed over 2022–2025, ÷ 1e9.", "cset")
with c2:
    fig = go.Figure()
    for seg, cl in [("Data centers and AI", BLUE), ("Gaming, devices, automotive", MUTED)]:
        d = nv[nv["Entity"] == seg]
        fig.add_bar(x=d["Quarter"], y=d["NVIDIA’s quarterly revenue"] / 1e9, name={"Data centers and AI": "Data centre & AI chips", "Gaming, devices, automotive": "Other"}[seg],
                    marker_color=cl, hovertemplate="$%{y:.1f}bn")
    card(f"Spending on AI hardware: NVIDIA's data-centre sales are up {nv_mult:.0f}× since late 2022",
         "quarterly revenue, US$bn · company filings via OWID",
         mini(fig, ypre="$").update_layout(barmode="stack").update_xaxes(tickangle=-45, nticks=10), nv, ["nvidia"], "Revenue ÷ 1e9; 'Total' rows not drawn.", "nvidia")
c3, c4 = st.columns(2)
with c3:
    fig = go.Figure()
    for i, r in enumerate(["United States", "Europe (IEA)", "China", "World"]):
        d = pw[pw["Entity"] == r]
        fig.add_scatter(x=d["Year"], y=d["share"], name=r.replace(" (IEA)", ""), mode="lines+markers", marker=dict(size=7),
                        line=dict(width=3.5 if r == "World" else 2, color=[BLUE, TEAL, AMBER, TEXT][i], dash="dot" if r == "World" else None),
                        hovertemplate="%{y:.2f}%")
    us_pw = pw[(pw["Entity"] == "United States")].set_index("Year")["share"]
    card(f"The build-out shows in power use: data centres take {us_pw[2025]:.1f}% of US electricity",
         "% of electricity demand used by data centres (all uses, incl. AI) · IEA via OWID",
         mini(fig, ysuf="%").update_xaxes(dtick=1), pw.rename(columns={"share": "share_pct"}), ["dc_power"], "Values as published.", "power")
with c4:
    gdf = load("genai").copy(); gdf["US$bn"] = (gdf["Global investment in generative AI"] / 1e9).round(2)
    fig = go.Figure(go.Bar(x=gdf["Year"], y=gdf["US$bn"], marker_color=[MUTED] * (len(gdf) - 3) + [BLUE] * 3,
                           text=gdf["US$bn"].map(lambda v: f"${v:,.0f}bn"), textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: $%{y:,.1f}bn<extra></extra>"))
    card(f"Capital to build AI: ${k_gi:.0f}bn of private investment in gen-AI developers in 2025",
         "US$bn, constant 2021 prices · Quid via Stanford AI Index 2026 / OWID",
         mini(fig, ypre="$", legend=False).update_xaxes(dtick=1), gdf, ["genai"], "Value ÷ 1e9.", "genai")

# --------------------------------------------------------------------------------------
section("Has it paid off in productivity and profits?", "Payoff", "payoff")
gg = load("gdppc_growth").rename(columns={"GDP per capita growth (annual %)": "growth"})
gg["region"] = gg["Entity"].str.replace(" (WB)", "", regex=False).replace({"European Union (27)": "EU-27", "Latin America and Caribbean": "Latin America",
                                                                             "East Asia and Pacific": "East Asia & Pacific"})
gw = gg.pivot(index="Year", columns="region", values="growth")
eu_low_yr = int(gw.loc[2022:, "EU-27"].idxmin()); eu_low = gw.loc[eu_low_yr, "EU-27"]
record(f"EU-27 GDP per person growth, {eu_low_yr}", f"{eu_low:.2f}%", ["gdppc_growth"], "Value as published (NY.GDP.PCAP.KD.ZG), EU-27 row.")
fig = go.Figure()
for x0, x1, lab in [(2019.5, 2020.5, "COVID-19"), (2021.6, 2023.4, "War in Ukraine · energy shock · rate hikes")]:
    fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(239,68,68,.08)", line_width=0, layer="below",
                  annotation_text=lab, annotation_position="top left", annotation_font=dict(size=11, color="#FCA5A5"))
style = {"World": (TEXT, 3, "dot"), "North America": (BLUE, 2.5, None), "EU-27": (TEAL, 2.5, None), "East Asia & Pacific": (AMBER, 2, None)}
for reg in ["South Asia", "Latin America", "Sub-Saharan Africa", "East Asia & Pacific", "North America", "EU-27", "World"]:
    col, wid, dash = style.get(reg, (MUTED, 1.4, None))
    fig.add_scatter(x=gw.index, y=gw[reg], name=reg, mode="lines+markers", line=dict(color=col, width=wid, dash=dash), marker=dict(size=5 if reg in style else 3),
                    hovertemplate="%{y:.1f}%")
fig.add_hline(y=0, line_color="#334155")
card(f"The economy itself was shocked — COVID, then the 2022 war and energy shock; EU growth per person fell to {eu_low:.1f}% in {eu_low_yr}",
     "GDP per person, real annual growth · productivity = output ÷ hours, so it moves with these swings · World Bank WDI via OWID",
     mini(fig, h=340, ysuf="%").update_xaxes(dtick=1, range=[2014.6, 2025.4]),
     gw.round(2).reset_index(), ["gdppc_growth"], "Values as published (annual % change in real GDP per person); pivoted to year × region.", "gdppc")
c1, c2 = st.columns(2)
with c1:
    pr = prod_reg.drop(index=["G7"]).sort_values("2022–25")
    fig = go.Figure()
    for reg, row in pr.iterrows():
        up = row["2022–25"] > row["2015–19"]
        fig.add_scatter(x=[row["2015–19"], row["2022–25"]], y=[reg, reg], mode="lines", line=dict(color=GREEN if up else RED, width=3),
                        showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=pr["2015–19"], y=pr.index, mode="markers", name="2015–19 (before)", marker=dict(size=11, color=MUTED),
                    hovertemplate="%{y}: %{x:.2f}%/yr before<extra></extra>")
    fig.add_scatter(x=pr["2022–25"], y=pr.index, mode="markers", name="2022–25 (gen-AI era)", marker=dict(size=13, color=BLUE),
                    hovertemplate="%{y}: %{x:.2f}%/yr since 2022<extra></extra>")
    faster = [r for r in pr.index if pr.loc[r, "2022–25"] > pr.loc[r, "2015–19"] + 0.3]
    slower = [r for r in ["World", "EU-27", "East Asia"] if r in pr.index and pr.loc[r, "2022–25"] < pr.loc[r, "2015–19"]]
    card(f"Since 2022, productivity growth slowed for the {' and '.join([s_.replace('World', 'world') for s_ in slower[:2]])} — North America is the big-economy exception",
         "output per hour worked, average annual growth · green = faster, red = slower · ILO modelled estimates (2025 nowcast)",
         mini(fig).update_layout(hovermode="closest").update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#334155"),
         prod_reg.reset_index(), ["ilo_oph"], "(2019 ÷ 2015)^(1/4) − 1 and (2025 ÷ 2022)^(1/3) − 1.", "dumbbell")
with c2:
    cap = 100 - lis
    idx = pd.DataFrame({
        "US — corporate profits ÷ GDP": us_ps_year.reindex(range(2019, 2026)) / us_ps_year[2019] * 100,
        "EU — company profit share": eu27.reindex(range(2019, 2026)) / eu27[2019] * 100,
        "World — capital share of GDP": cap.loc["World"].reindex(range(2019, 2026)) / cap.loc["World", 2019] * 100,
    }).round(2)
    fig = go.Figure()
    for i, c_ in enumerate(idx.columns):
        fig.add_scatter(x=idx.index, y=idx[c_], name=c_, mode="lines+markers", line=dict(color=[BLUE, TEAL, AMBER][i], width=3 if i == 0 else 2),
                        marker=dict(size=6), hovertemplate="%{y:.1f}")
        last = idx[c_].dropna()
        fig.add_annotation(x=last.index[-1], y=last.iloc[-1], text=f"{last.iloc[-1] - 100:+.0f}%", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=[BLUE, TEAL, AMBER][i], size=12))
    fig.add_hline(y=100, line_color="#334155", line_dash="dot")
    card("Profit margins rose in the US — not in the EU or worldwide",
         "profit share indexed to 2019 = 100 · BEA via FRED, Eurostat, ILO",
         mini(fig, ytitle="index, 2019 = 100").update_xaxes(dtick=1, range=[2018.7, 2025.7]), idx.reset_index(names="year"), ["cp", "gdp", "eu_profit", "ilo_lis"],
         "US: annual mean of quarterly CP ÷ GDP; EU: B2G_B3G_RAT_S11 (EU27); World: 100 − ILO labour income share. Each ÷ its 2019 value × 100.", "profitidx")

# --------------------------------------------------------------------------------------
section("Where does AI actually pay off?", "Evidence", "where")
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Scatter(x=ind_b["AI adoption 2025 (%)"], y=ind_b["Productivity growth 2021→2025 (%)"], mode="markers+text", text=ind_b["label"],
                               textposition=["middle left" if v > 50 else "top center" for v in ind_b["AI adoption 2025 (%)"]],
                               marker=dict(size=ind_b["gva_2025_bn_eur"], sizemode="area", sizeref=2.0 * ind_b["gva_2025_bn_eur"].max() / (70 ** 2), sizemin=6,
                                           color=[BLUE if l == "ICT" else TEAL for l in ind_b["label"]], opacity=0.85, line=dict(color="#0B1220", width=1)),
                               customdata=ind_b[["gva_2025_bn_eur"]], textfont=dict(size=12, color=TEXT),
                               hovertemplate="<b>%{text}</b><br>AI use %{x:.0f}% · productivity %{y:+.1f}%<br>value added €%{customdata[0]:,.0f}bn<extra></extra>"))
    fig.add_hline(y=0, line_color="#334155")
    card(f"Industries that use AI most grew productivity fastest — led by {ind_top['label']}",
         f"EU-27 · x: % firms using AI (2025) · y: productivity growth 2021–25 · bubble = value added · r = {c_ind['r']:+.2f}, 6 industries · Eurostat",
         mini(fig, ysuf="%", legend=False, xtitle="% of firms using AI, 2025", ytitle="productivity growth 2021–25").update_layout(hovermode="closest")
         .update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID), ind_b.round(2), ["ind_ai", "ind_gva", "ind_hours"],
         "Productivity = real value added ÷ hours worked, 2025 ÷ 2021 − 1; bubble = 2025 nominal value added (€bn); Pearson r.", "indbubble")
with c2:
    scope = st.session_state.get("ev_scope", "World")
    if scope == "World":
        # world: adults using gen AI (Microsoft) vs ILO output per hour, 142+ countries
        gx = gu[(gu["Day"] == gu_last_day) & (gu["Code"].str.len() == 3)].set_index("Code")
        il = load("ilo_oph_c").pivot(index="ref_area", columns="year", values="value")
        g_post = ((il[2025] / il[2022]) ** (1 / 3) - 1) * 100
        g_pre = ((il[2019] / il[2015]) ** (1 / 4) - 1) * 100
        WORLD_OUT = {"Productivity growth 2022–25 (%/yr)": g_post,
                     "Productivity growth: 2022–25 minus 2015–19 (pp)": g_post - g_pre}
        wm = st.session_state.get("w_metric", list(WORLD_OUT)[0])
        if wm not in WORLD_OUT:
            wm = list(WORLD_OUT)[0]
        qd = pd.DataFrame({"geo": gx.index, "country": gx["Entity"], "region": gx["region"], "ai": gx["share"]})
        qd["outcome"] = qd["geo"].map(WORLD_OUT[wm])
        qd = qd.dropna().reset_index(drop=True)
        x_lab, y_lab, keys = f"% of adults using gen AI ({pd.Timestamp(gu_last_day):%b %Y})", wm, ["genai_use", "ilo_oph_c"]
        how = ("x = Microsoft gen-AI user share (latest date); y = ILO output per hour: (2025 ÷ 2022)^(1/3) − 1"
               + (" minus (2019 ÷ 2015)^(1/4) − 1" if "minus" in wm else "") + "; joined on ISO3 code; lines = medians; Pearson r.")
        higher = True
        label_set = {"USA", "CHN", "IND", "ARE", "SGP", "NOR", "IRL", "DEU", "JPN", "GBR", "BRA", "AUS", "KOR", "FRA"}
        sub_lead = f"{len(qd)} countries · ILO, Microsoft via OWID"
    else:
        metric = st.session_state.get("cty_metric", "Productivity growth since 2019 (%)")
        o = OUTCOMES[metric]
        x_now = ai_wide[2025].drop(index=list(AGGREGATES), errors="ignore")
        qd = pd.DataFrame({"geo": x_now.index, "ai": x_now.values})
        qd["outcome"] = qd["geo"].map(change_table(metric))
        qd = qd.dropna().reset_index(drop=True)
        qd["country"] = qd["geo"].map(lambda g: GEO_NAMES.get(g, g)); qd["region"] = "Europe"
        x_lab, y_lab, keys = "% of firms using AI, 2025", o["change_label"], ["eu_ai"] + o["keys"]
        how = f"x = E_AI_TANY 2025; y = {o['change_label']}; dotted lines = medians; Pearson r."
        higher = o["higher"]
        label_set = set(qd["geo"])
        sub_lead = f"{len(qd)} European countries · Eurostat firm survey"
    cq = corr(qd.set_index("geo")["ai"], qd.set_index("geo")["outcome"])
    mx, my = qd["ai"].median(), qd["outcome"].median()
    good = (qd["outcome"] > my) if higher else (qd["outcome"] < my)
    lead = qd["ai"] > mx
    n_lead_good = int((lead & good).sum()); n_lead = int(lead.sum())
    fig = go.Figure()
    fig.add_shape(type="rect", xref="x", yref="paper", x0=mx, x1=qd["ai"].max() * 1.05, y0=0, y1=1, fillcolor="rgba(59,130,246,.07)", line_width=0, layer="below")
    fig.add_vline(x=mx, line_color="#334155", line_dash="dot")
    fig.add_hline(y=my, line_color="#334155", line_dash="dot")
    show = qd["geo"].isin(label_set)
    fig.add_scatter(x=qd["ai"], y=qd["outcome"], mode="markers+text", text=[g if sh else "" for g, sh in zip(qd["geo"], show)],
                    textposition="top center", textfont=dict(size=9, color=SUB),
                    marker=dict(size=9, color=[BLUE if l else MUTED for l in lead], opacity=0.85, line=dict(color="#0B1220", width=1)),
                    customdata=qd[["country"]], hovertemplate="<b>%{customdata[0]}</b><br>AI use %{x:.0f}% · %{y:+.2f}<extra></extra>", showlegend=False)
    ylo, yhi = qd["outcome"].quantile([0.01, 0.99])
    pad = (yhi - ylo) * 0.12
    share_good = n_lead_good / n_lead
    verdict = "have out-performed" if share_good > 0.6 else ("have not out-performed" if share_good <= 0.4 else "have done no better than")
    scope_word = "Worldwide" if scope == "World" else "In Europe"

    def _controls():
        a, b_ = st.columns([1, 1.5])
        a.selectbox("Scope", ["World", "Europe"], key="ev_scope", label_visibility="collapsed",
                    format_func=lambda v: {"World": "World · 142 countries", "Europe": "Europe · 30 countries"}[v])
        if st.session_state.get("ev_scope", "World") == "World":
            b_.selectbox("Outcome", ["Productivity growth 2022–25 (%/yr)", "Productivity growth: 2022–25 minus 2015–19 (pp)"],
                         key="w_metric", label_visibility="collapsed")
        else:
            b_.selectbox("Outcome", [m for m in OUTCOMES if not m.startswith("AI") and "consumption" not in m and "Youth" not in m],
                         key="cty_metric", label_visibility="collapsed", format_func=lambda m: OUTCOMES[m]["change_label"])

    card(f"{scope_word}, the heaviest AI users {verdict} the rest — {n_lead_good} of {n_lead} beat the median",
         f"{sub_lead} · shaded = above-median AI use · r = {cq['r']:+.2f}",
         mini(fig, legend=False, xtitle=x_lab, ytitle=plain(y_lab)[:34]).update_layout(hovermode="closest")
         .update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID).update_yaxes(range=[ylo - pad, yhi + pad]),
         qd[["country", "geo", "region", "ai", "outcome"]].round(3), keys, how + " Y-axis clipped to the 1st–99th percentile; hover or the table shows all.", "quadrant",
         before=_controls)

# --------------------------------------------------------------------------------------
section("Who captures the gains?", "Distribution", "gains")
c1, c2 = st.columns(2)
with c1:
    b = pd.Timestamp(AI_ERA_START)
    G = fred("gdp")
    ix = pd.DataFrame({"Corporate profits": CPs / CPs[b] * 100, "Nominal GDP": G / G[b] * 100, "Employee pay": COE / COE[b] * 100}).loc["2019":]
    fig = go.Figure()
    for i, c_ in enumerate(ix.columns):
        fig.add_scatter(x=ix.index, y=ix[c_], name=c_, mode="lines", line=dict(color=[BLUE, SLATE, AMBER][i], width=3 if i != 1 else 1.8,
                        dash="dot" if i == 1 else None), hovertemplate="%{y:.0f}")
        fig.add_annotation(x=ix.index[-1], y=ix[c_].iloc[-1], text=f"{ix[c_].iloc[-1] - 100:+.0f}%", showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=[BLUE, SLATE, AMBER][i], size=12))
    fig.add_vline(x=b, line_color="#334155", line_dash="dot")
    fig.add_hline(y=100, line_color="#334155")
    card(f"Since 2022, US profits grew {pg:.0f}% — employee pay only {wg:.0f}%",
         "indexed, 2022Q4 = 100 · BEA via FRED (CP, COE, GDP)",
         mini(fig, ytitle="index, 2022Q4 = 100").update_xaxes(range=[ix.index[0], ix.index[-1] + pd.Timedelta(days=200)]),
         ix.round(2).join(pd.DataFrame({"Profits $bn (CP)": CPs, "Employee pay $bn (COE)": COE, "GDP $bn": G}).round(3)).reset_index(names="date").iloc[::-1],
         ["cp", "coe", "gdp"], "Each series ÷ its 2022Q4 value × 100 (raw US$bn columns shown; newest first).", "profitpay")
with c2:
    lc = ls_chg.drop(index=["G7"]).sort_values()
    fig = go.Figure(go.Bar(x=lc.values, y=lc.index, orientation="h", marker_color=[RED if v < 0 else GREEN for v in lc.values],
                           text=[f"{v:+.1f} pp" for v in lc.values], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:+.2f} pp<extra></extra>"))
    fig.add_vline(x=0, line_color="#334155")
    n_fell = int((lc < 0).sum())
    card(f"Workers' share of income fell in {n_fell} of {len(lc)} regions since 2019",
         "change in labour income share of GDP, 2019→2025, percentage points · ILO modelled estimates",
         mini(fig, legend=False).update_layout(hovermode="closest").update_xaxes(ticksuffix=" pp", showgrid=True, gridcolor=GRID,
                                                                                 range=[lc.min() - 1, lc.max() + 1]),
         lis[[2019, 2025]].rename(columns=str).assign(change_pp=ls_chg).reset_index(), ["ilo_lis"], "Labour income share 2025 − 2019 (percentage points).", "labshare")

# --------------------------------------------------------------------------------------
section("What does it take to capture the value?", "Execution", "execution")
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Bar(x=barriers["pct_of_firms_that_considered_AI"], y=barriers["barrier"], orientation="h",
                           marker_color=[BLUE if b_ == top_bar["barrier"] else (AMBER if b_ == "Costs seem too high" else MUTED) for b_ in barriers["barrier"]],
                           text=[f"{v:.0f}%" for v in barriers["pct_of_firms_that_considered_AI"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.0f}%<extra></extra>"))
    card(f"Skills, not cost, hold firms back: {top_bar['pct_of_firms_that_considered_AI']:.0f}% lack expertise vs {cost_bar['pct_of_firms_that_considered_AI']:.0f}% citing cost",
         "reasons given by EU firms that considered AI but don't use it, 2025 · Eurostat",
         mini(fig, legend=False).update_layout(hovermode="closest").update_xaxes(ticksuffix="%", range=[0, 85], showgrid=True, gridcolor=GRID),
         barriers.round(2), ["eu_barriers"], f"Each barrier ÷ E_AI_EC ({considered}% of all firms considered AI but don't use it) × 100.", "barriers")
with c2:
    yu = OUTCOMES["Youth unemployment rate (%)"]["get"]()
    yu = yu[~yu["geo"].isin(AGGREGATES)]
    top8 = list(countries_ranked.index[:8])
    yu["group"] = yu["geo"].isin(top8).map({True: "8 highest AI-adopting countries", False: "Other European countries"})
    g = yu.groupby(["group", "year"])["value"].mean().reset_index()
    g_ix = g.pivot(index="year", columns="group", values="value")
    fig = go.Figure()
    for grp, cl in [("8 highest AI-adopting countries", BLUE), ("Other European countries", MUTED)]:
        fig.add_scatter(x=g_ix.index, y=g_ix[grp], name=grp, mode="lines+markers", line=dict(color=cl, width=3), marker=dict(size=7), hovertemplate="%{y:.1f}%")
    d_top = g_ix.loc[2025, "8 highest AI-adopting countries"] - g_ix.loc[2022, "8 highest AI-adopting countries"]
    d_oth = g_ix.loc[2025, "Other European countries"] - g_ix.loc[2022, "Other European countries"]
    card(f"Watch the talent pipeline: youth unemployment is rising in AI-leading countries ({d_top:+.1f} pp since 2022)",
         f"unemployment rate, ages 15–24, unweighted average · others {d_oth:+.1f} pp · Eurostat",
         mini(fig, ysuf="%").update_xaxes(dtick=1), g.round(3), ["eu_unemp", "eu_ai"],
         "Y15-24 unemployment; unweighted mean of the 8 countries with the highest 2025 AI adoption (E_AI_TANY) vs all others.", "youth")

# --------------------------------------------------------------------------------------
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
with st.expander("Appendix · data & method — every figure, source file and raw data", expanded=False):
    st.markdown("<div id='appendix'></div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["Figures & calculations", "Source files", "Inspect a raw file", "Limits"])
    with t1:
        st.dataframe(pd.DataFrame(LINEAGE).drop_duplicates(subset=["Figure"]), width="stretch", hide_index=True)
    with t2:
        src = pd.DataFrame([{"Key": k_, "File": v["file"], "Dataset": v["title"], "Publisher": v["publisher"], "Link": v["url"], "Notes": v["notes"]}
                            for k_, v in SOURCES.items()])
        st.dataframe(src, width="stretch", hide_index=True, column_config={"Link": st.column_config.LinkColumn()})
    with t3:
        pick = st.selectbox("File", list(SOURCES), format_func=lambda k_: SOURCES[k_]["file"])
        raw = load(pick)
        st.caption(f"{len(raw)} rows · unmodified as downloaded")
        st.dataframe(raw, width="stretch", hide_index=True, height=320)
        st.download_button("Download this raw file", (DATA / SOURCES[pick]["file"]).read_bytes(), SOURCES[pick]["file"], "text/csv", key="dl_raw")
    with t4:
        st.markdown(
            "- Time-series charts show **correlation in time, not causation**; other forces (post-pandemic recovery, pricing power, tax) also move profits.\n"
            "- ILO figures are modelled estimates; 2025 is a nowcast. Capital share = 100 − labour share (includes net production taxes).\n"
            "- Profit measures differ by source: US after-tax corporate profits ÷ GDP; EU gross operating surplus ÷ value added.\n"
            "- Industry, firm-size, barrier and country data are official only for Europe (Eurostat); the country chart's correlation is confounded by catch-up growth.\n"
            "- Gen-AI use is estimated by Microsoft from its own platform data, scaled to each country's working-age population.\n"
            "- Data-centre construction excludes IT hardware; data-centre electricity covers all uses, not only AI."
        )
