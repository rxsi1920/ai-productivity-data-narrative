"""Build data/dictionary.yml, the machine-readable data dictionary, in the Assignment 2 Part C standard.

The `sources` and `datasets` blocks follow the A2 Part C manifest schema (schemas/dashboard.schema.json, schema_version 2):
- each source: id, publisher, title, url, licence, retrieved, cadence, status, notes
- each dataset: id, source_ids, sample, processed_output, format, date_column, primary_key, minimum_rows,
  latest_observation, columns (type, role, nullable, unit, minimum/maximum, date_minimum/date_maximum, allowed_values)

What is written by hand below: sources, which raw file and source each dataset comes from, primary keys, units and the
transform. What is computed from the files: column types, nullability, ranges, allowed values, row counts, date ranges
and the latest observation. The script stops if a primary key is not unique or a measure has no unit.

Dates follow the A2 checker: CSV values are read as text and the date column is parsed with pandas.to_datetime, so a
year "2025" is read as 2025-01-01 and a quarter "2026-Q3" as 2026-07-01.

Run from the repository root:  python scripts/build_dictionary.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW, PROC = Path("data/raw"), Path("data/processed")
OUT = ROOT / "data" / "dictionary.yml"

warnings.filterwarnings("ignore")  # pandas date-format inference notices

# --------------------------------------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------------------------------------
PROFIT, FEEDBACK, MORAL = "2026-10-22", "2026-11-11", "2026-11-16"  # date each part's raw files were downloaded
OWID = "Our World in Data"
EUROSTAT_LICENCE = "CC BY 4.0 (Eurostat copyright notice)"


def owid(slug: str) -> str:
    return f"https://ourworldindata.org/grapher/{slug}"


def eurostat(code: str) -> str:
    return f"https://ec.europa.eu/eurostat/databrowser/view/{code}/default/table"


SOURCES = [
    # Profitability -------------------------------------------------------------------------------------------------
    dict(id="owid_ai_adoption", publisher=OWID, title="Share of companies using artificial intelligence",
         url=owid("share-companies-using-artificial-intelligence"), licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Annual", status="snapshot",
         notes="Original source: McKinsey Global Survey on AI, via the Stanford AI Index."),
    dict(id="owid_genai_use", publisher=OWID, title="Estimated share of working-age adults who use generative AI",
         url=owid("estimated-share-people-generative-ai"), licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Irregular, about every 6 months", status="snapshot",
         notes="Original source: Microsoft AI Economy Institute. GDP per capita column from the World Bank via OWID."),
    dict(id="eurostat_isoc_eb_ai", publisher="Eurostat",
         title="Artificial intelligence by size class of enterprise (isoc_eb_ai)", url=eurostat("isoc_eb_ai"),
         licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual survey (AI module in 2021, 2023, 2024, 2025)",
         status="snapshot", notes="Used for AI adoption by country, by firm size and barriers to adoption."),
    dict(id="eurostat_isoc_eb_ain2", publisher="Eurostat",
         title="Artificial intelligence by NACE Rev.2 activity (isoc_eb_ain2)", url=eurostat("isoc_eb_ain2"),
         licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual survey (AI module in 2021, 2023, 2024, 2025)",
         status="snapshot"),
    dict(id="owid_private_ai_investment", publisher=OWID,
         title="Private investment in artificial intelligence (CSET)",
         url=owid("private-investment-in-artificial-intelligence-cset"), licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Annual", status="snapshot",
         notes="Original source: Center for Security and Emerging Technology (CSET). Extract: 2022-2025."),
    dict(id="owid_genai_investment", publisher=OWID, title="Global investment in generative AI",
         url=owid("global-investment-in-generative-ai"), licence="CC BY 4.0", retrieved=PROFIT, cadence="Annual",
         status="snapshot", notes="Original source: Quid, via the Stanford AI Index 2026."),
    dict(id="owid_nvidia_revenue", publisher=OWID, title="NVIDIA quarterly revenue by segment",
         url=owid("nvidia-quarterly-revenue-segment"), licence="CC BY 4.0", retrieved=PROFIT, cadence="Quarterly",
         status="snapshot", notes="Original source: NVIDIA quarterly filings. Quarters are fiscal, as labelled by OWID."),
    dict(id="owid_datacentre_electricity", publisher=OWID,
         title="Share of total electricity demand coming from data centers",
         url=owid("data-centers-share-electricity-demand"), licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Annual", status="snapshot", notes="Original sources: IEA Energy and AI (numerator), Ember (denominator)."),
    dict(id="owid_gdp_pc_growth", publisher=OWID, title="GDP per capita growth (annual %)",
         url=owid("gdp-per-capita-growth"), licence="CC BY 4.0", retrieved=PROFIT, cadence="Annual",
         status="snapshot", notes="Original source: World Bank WDI NY.GDP.PCAP.KD.ZG. Extract: 7 regions."),
    dict(id="ilo_output_per_hour", publisher="International Labour Organization (ILO)",
         title="Output per hour worked, GDP constant 2021 international $ at PPP (DF_GDP_2HRW_NOC_NB)",
         url="https://sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB", licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Annual, with projections", status="snapshot",
         notes="ILO modelled estimates. Values after 2025 are projections and are not used."),
    dict(id="ilo_labour_income_share", publisher="International Labour Organization (ILO)",
         title="Labour income share as a percent of GDP (DF_LAP_2GDP_NOC_RT)",
         url="https://sdmx.ilo.org/rest/data/ILO,DF_LAP_2GDP_NOC_RT", licence="CC BY 4.0", retrieved=PROFIT,
         cadence="Annual, with projections", status="snapshot"),
    dict(id="fred_cp", publisher="US Bureau of Economic Analysis via FRED",
         title="Corporate profits after tax (CP)", url="https://fred.stlouisfed.org/series/CP",
         licence="Public domain (US government work)", retrieved=PROFIT, cadence="Quarterly, with revisions",
         status="snapshot"),
    dict(id="fred_gdp", publisher="US Bureau of Economic Analysis via FRED", title="Gross domestic product (GDP)",
         url="https://fred.stlouisfed.org/series/GDP", licence="Public domain (US government work)", retrieved=PROFIT,
         cadence="Quarterly, with revisions", status="snapshot"),
    dict(id="fred_coe", publisher="US Bureau of Economic Analysis via FRED",
         title="Compensation of employees, paid (COE)", url="https://fred.stlouisfed.org/series/COE",
         licence="Public domain (US government work)", retrieved=PROFIT, cadence="Quarterly, with revisions",
         status="snapshot"),
    dict(id="fred_ophnfb", publisher="US Bureau of Labor Statistics via FRED",
         title="Nonfarm business sector: labor productivity (output per hour) (OPHNFB)",
         url="https://fred.stlouisfed.org/series/OPHNFB", licence="Public domain (US government work)",
         retrieved=PROFIT, cadence="Quarterly, with revisions", status="snapshot"),
    dict(id="fred_ulcnfb", publisher="US Bureau of Labor Statistics via FRED",
         title="Nonfarm business sector: unit labor costs (ULCNFB)", url="https://fred.stlouisfed.org/series/ULCNFB",
         licence="Public domain (US government work)", retrieved=PROFIT, cadence="Quarterly, with revisions",
         status="snapshot"),
    dict(id="eurostat_nasa_10_ki", publisher="Eurostat", title="Key indicators, sectors (nasa_10_ki)",
         url=eurostat("nasa_10_ki"), licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual, with revisions",
         status="snapshot", notes="Indicators B2G_B3G_RAT_S11 (profit share) and P4_R_HAB_GR (consumption growth)."),
    dict(id="eurostat_nama_10_lp_ulc", publisher="Eurostat",
         title="Labour productivity and unit labour costs (nama_10_lp_ulc)", url=eurostat("nama_10_lp_ulc"),
         licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual, with revisions", status="snapshot"),
    dict(id="eurostat_nama_10_a10", publisher="Eurostat",
         title="Gross value added and income by A*10 industry breakdowns (nama_10_a10)", url=eurostat("nama_10_a10"),
         licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual, with revisions", status="snapshot"),
    dict(id="eurostat_nama_10_a10_e", publisher="Eurostat",
         title="Employment by A*10 industry breakdowns (nama_10_a10_e)", url=eurostat("nama_10_a10_e"),
         licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual, with revisions", status="snapshot"),
    dict(id="eurostat_une_rt_a", publisher="Eurostat", title="Unemployment by sex and age, annual data (une_rt_a)",
         url=eurostat("une_rt_a"), licence=EUROSTAT_LICENCE, retrieved=PROFIT, cadence="Annual", status="snapshot"),
    # Feedback loop and cognition -----------------------------------------------------------------------------------
    dict(id="census_btos", publisher="US Census Bureau",
         title="Business Trends and Outlook Survey (BTOS), AI use question",
         url="https://www.census.gov/hfp/btos", licence="Public domain (US government work)", retrieved=FEEDBACK,
         cadence="Every two weeks", status="snapshot",
         notes="Copied from karanmakhijauts/at-3-dvn at commit b33f3b25b7cce24833c857d242c90152c3b41571."),
    dict(id="workforce_evidence", publisher="Karan Makhija (group member), from five published studies",
         title="Evidence table: AI and output or skill (one finding per row)",
         url="https://github.com/karanmakhijauts/at-3-dvn", licence="Cited facts; each row links to its paper",
         retrieved=FEEDBACK, cadence="One-off compilation", status="archive",
         notes="Commit b33f3b25b7cce24833c857d242c90152c3b41571. The source_url column gives each finding's paper."),
    dict(id="canaries_2026", publisher="Stanford Digital Economy Lab",
         title="Brynjolfsson, Chandar and Chen (Aug 2026), Canaries in the Coal Mine, update",
         url="https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf",
         licence="Cited facts; the underlying ADP payroll microdata are proprietary", retrieved=FEEDBACK,
         cadence="One-off paper", status="archive"),
    dict(id="wildai", publisher="Pangram Labs (Russell et al., 2026)",
         title="WildAI: AI-written share of web text and training-cost results (arXiv:2609.40295 v1)",
         url="https://github.com/pangramlabs/WildAI", licence="CC BY-NC-SA 4.0", retrieved=FEEDBACK,
         cadence="One-off release", status="archive",
         notes="Commit 795a71852d569173fcdaca1db2a466109cd80814. Used non-commercially, with credit."),
    dict(id="schaeffer_2025", publisher="Schaeffer et al. (2025)",
         title="Position: Model collapse does not mean what you think (arXiv:2503.03150 v2), Appendix A Table 1",
         url="https://arxiv.org/abs/2503.03150", licence="Cited facts", retrieved=FEEDBACK, cadence="One-off paper",
         status="archive"),
    # Moral degradation ---------------------------------------------------------------------------------------------
    dict(id="aiid_snapshot", publisher="Responsible AI Collaborative",
         title="AI Incident Database (AIID), full database snapshot",
         url="https://incidentdatabase.ai/research/snapshots/", licence="CC BY-SA 4.0", retrieved=MORAL,
         cadence="Continuously updated; weekly snapshots", status="snapshot",
         notes="Report text is excluded from AIID's CC BY-SA grant; only report ids and dates are used. "
               "ai_reports.csv latest observation: 2026-11-15 (date_submitted)."),
    dict(id="aiid_gmf", publisher="Responsible AI Collaborative",
         title="AI Incident Database, Goals-Methods-Failures (GMF) taxonomy classifications",
         url="https://incidentdatabase.ai/taxonomies/gmf/", licence="CC BY-SA 4.0", retrieved=MORAL,
         cadence="Continuously updated", status="snapshot"),
    dict(id="llm_ethics_benchmark", publisher="universe-szw (GitHub)",
         title="Scientometric LLM Ethics Benchmark: human validation and AI-judge scores (scoring_results/)",
         url="https://github.com/universe-szw/scientometric-llm-ethics-benchmark", licence="MIT", retrieved=MORAL,
         cadence="One-off release", status="archive", notes="2026 release, GPT-5.5 as one of three judges."),
    dict(id="girai", publisher="Global Center on AI Governance",
         title="Global Index on Responsible AI (GIRAI), 2nd edition: Global Survey dataset",
         url="https://www.global-index.ai/", licence="CC BY 4.0", retrieved=MORAL,
         cadence="About every two years", status="archive",
         notes="Evidence cut-off September 2025, published 2026. No observation date per row."),
    dict(id="ipsos_ai_monitor_2025", publisher="Ipsos", title="Ipsos AI Monitor 2025",
         url="https://www.ipsos.com/sites/default/files/ct/publication/documents/2025-06/Ipsos-AI-Monitor-2025.pdf",
         licence="Copyright Ipsos; published figures, cited", retrieved=MORAL, cadence="Annual", status="archive",
         notes="Page 23 (trust in government to regulate AI). Fieldwork ended 2025-04-04."),
    dict(id="ipsos_ai_monitor_2026", publisher="Ipsos", title="Ipsos AI Monitor 2026",
         url="https://www.ipsos.com/sites/default/files/ct/news/documents/2026-06/Ipsos-AI-Monitor-2026.pdf",
         licence="Copyright Ipsos; published figures, cited", retrieved=MORAL, cadence="Annual", status="archive",
         notes="Pages 17, 21 and 26. Fieldwork ended 2026-04-03."),
    dict(id="kaggle_ai_workforce", publisher="Kaggle (M. K. Suraj)",
         title="Global AI Adoption & Workforce Impact Survey 24-26",
         url="https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26",
         licence="Apache 2.0", retrieved=MORAL, cadence="One-off (last updated 2026-04-07)", status="snapshot",
         notes="Survey responses 2024-2026; no observation date per row."),
    dict(id="cheng_sycophancy", publisher="Cheng et al. (Science, 2026), OSF project smvw7",
         title="Sycophantic AI and moral judgement: Study 2 and Study 3 response data",
         url="https://osf.io/smvw7/", licence="CC BY 4.0", retrieved=MORAL, cadence="One-off release",
         status="archive", notes="Released 2026-03-26. No observation date per row."),
]

# --------------------------------------------------------------------------------------------------------------------
# Datasets: id, processed file, raw sample, sources, primary key, date column, units, transform
# --------------------------------------------------------------------------------------------------------------------
EU_FLAG = "Eurostat observation flag"
PROFIT_BUILD = "python src/narrative/tabs/profitability/build_processed.py"
FEEDBACK_BUILD = "python -m narrative.human_practice_data"
MORAL_BUILD = "python scripts/data.py"
WINDOW = "rows from the analysis start year onward; exact duplicates dropped; sorted by key"


def same(name: str, sources, pk, date=None, units=None, transform=WINDOW, sample=None):
    """Profitability files: the processed file has the same name as its raw file."""
    return dict(id=Path(name).stem.replace("-", "_").lower(), processed=name, sample=sample or name,
                source_ids=sources, primary_key=pk, date_column=date, units=units or {},
                transform=f"{PROFIT_BUILD}: {transform}")


DATASETS = [
    # Profitability --------------------------------------------------------------------------------------------------
    same("owid_share-companies-using-artificial-intelligence.csv", ["owid_ai_adoption"], ["Entity", "Year"], "Year",
         {"Organizations reporting having adopted AI": "% of organisations using AI in at least one business function"}),
    same("owid_estimated-share-people-generative-ai.csv", ["owid_genai_use"], ["Code", "Day"], "Day",
         {"Estimated share of working-age adults who use generative AI": "% of adults aged 15-64",
          "GDP per capita": "international $ (2021 prices, PPP)"}, transform="exact duplicates dropped; sorted by key"),
    same("eurostat_isoc_eb_ai.csv", ["eurostat_isoc_eb_ai"], ["indic_is", "geo", "year"], "year",
         {"value": "% of enterprises with 10+ employees"}),
    same("eurostat_isoc_eb_ain2_industry.csv", ["eurostat_isoc_eb_ain2"], ["nace_r2", "year"], "year",
         {"value": "% of enterprises with 10+ employees"}),
    same("eurostat_isoc_eb_ai_size.csv", ["eurostat_isoc_eb_ai"], ["size_emp", "year"], "year",
         {"value": "% of enterprises in the size class"}),
    same("eurostat_isoc_eb_ai_barriers.csv", ["eurostat_isoc_eb_ai"], ["indic_is", "year"], "year",
         {"value": "% of all enterprises with 10+ employees"}),
    same("owid_private-investment-in-artificial-intelligence-cset.csv", ["owid_private_ai_investment"],
         ["Code", "Year"], "Year", {"Estimated funding raised by privately held AI companies - Field: All": "US$ (constant 2021)"}),
    same("owid_global-investment-in-generative-ai.csv", ["owid_genai_investment"], ["Year"], "Year",
         {"Global investment in generative AI": "US$ (constant 2021)"}),
    same("owid_nvidia-quarterly-revenue-segment.csv", ["owid_nvidia_revenue"], ["Entity", "Quarter"], "Quarter",
         {"NVIDIA’s quarterly revenue": "US$ (nominal)"}, transform="exact duplicates dropped; sorted by key"),
    same("owid_data-centers-share-electricity-demand.csv", ["owid_datacentre_electricity"], ["Entity", "Year"], "Year",
         {"Share of total electricity demand coming from data centers": "% of electricity demand"}),
    same("owid_gdp-per-capita-growth.csv", ["owid_gdp_pc_growth"], ["Entity", "Year"], "Year",
         {"GDP per capita growth (annual %)": "% change in real GDP per person on previous year"}),
    same("ilo_output_per_hour.csv", ["ilo_output_per_hour"], ["ref_area", "year"], "year",
         {"value": "GDP per hour worked, international $ (2021 prices, PPP)"},
         transform=WINDOW + ". Values for 2026 and 2027 are ILO projections (not used by the app); the last "
                   "estimated year is 2025."),
    same("ilo_output_per_hour_countries.csv", ["ilo_output_per_hour"], ["ref_area", "year"], "year",
         {"value": "GDP per hour worked, international $ (2021 prices, PPP)"}),
    same("ilo_labour_income_share.csv", ["ilo_labour_income_share"], ["ref_area", "year"], "year",
         {"value": "% of GDP"},
         transform=WINDOW + ". The 2026 value is an ILO projection (not used by the app); the last estimated year is 2025."),
    same("fred_CP.csv", ["fred_cp"], ["observation_date"], "observation_date",
         {"CP": "US$ billion, seasonally adjusted annual rate"}, transform="exact duplicates dropped; sorted by date"),
    same("fred_GDP.csv", ["fred_gdp"], ["observation_date"], "observation_date",
         {"GDP": "US$ billion, seasonally adjusted annual rate"}, transform="exact duplicates dropped; sorted by date"),
    same("fred_COE.csv", ["fred_coe"], ["observation_date"], "observation_date",
         {"COE": "US$ billion, seasonally adjusted annual rate"}, transform="exact duplicates dropped; sorted by date"),
    same("fred_OPHNFB.csv", ["fred_ophnfb"], ["observation_date"], "observation_date",
         {"OPHNFB": "index, 2017 = 100"}, transform="exact duplicates dropped; sorted by date"),
    same("fred_ULCNFB.csv", ["fred_ulcnfb"], ["observation_date"], "observation_date",
         {"ULCNFB": "index, 2017 = 100"}, transform="exact duplicates dropped; sorted by date"),
    same("eurostat_nasa_10_ki_profit_share.csv", ["eurostat_nasa_10_ki"], ["geo", "year"], "year",
         {"value": "% (gross operating surplus share of non-financial corporations' value added)"}),
    same("eurostat_nasa_10_ki_consumption_growth.csv", ["eurostat_nasa_10_ki"], ["geo", "year"], "year",
         {"value": "% change on previous year (real household consumption per person)"}),
    same("eurostat_nama_10_lp_ulc.csv", ["eurostat_nama_10_lp_ulc"], ["na_item", "geo", "year"], "year",
         {"value": "index, 2015 = 100"}),
    same("eurostat_nama_10_a10_industry.csv", ["eurostat_nama_10_a10"], ["unit", "nace_r2", "na_item", "year"], "year",
         {"value": "€ million (unit column: CLV20_MEUR = 2020 prices, CP_MEUR = current prices)"}),
    same("eurostat_nama_10_a10_e_hours.csv", ["eurostat_nama_10_a10_e"], ["nace_r2", "year"], "year",
         {"value": "thousand hours worked"}),
    same("eurostat_une_rt_a.csv", ["eurostat_une_rt_a"], ["age", "geo", "year"], "year",
         {"value": "% of labour force"}),
    # Feedback loop and cognition -----------------------------------------------------------------------------------
    dict(id="hp_adoption", processed="human_practice/adoption.csv", sample="human_practice/workforce/btos_ai.csv",
         source_ids=["census_btos"], primary_key=["period_code", "answer"],
         units={"share_pct": "% of US firms", "period_order": "rank (1 = first two-week period)"},
         transform=f"{FEEDBACK_BUILD} (build_adoption): rename value_pct to share_pct, add period_order, "
                   "drop answer_id and raw_value. Coverage 2025-P24 to 2026-P21 (24 two-week periods); "
                   "periods are not calendar dates, so no date column is declared."),
    dict(id="hp_evidence", processed="human_practice/evidence.csv", sample="human_practice/workforce/evidence.csv",
         source_ids=["workforce_evidence"], primary_key=["id"], date_column="year",
         units={"sample_size": "people (see sample_unit)"},
         transform=f"{FEEDBACK_BUILD} (build_evidence): add panel_title."),
    dict(id="hp_entry_level", processed="human_practice/entry_level.csv",
         sample="human_practice/workforce/entry_level_employment.csv", source_ids=["canaries_2026"],
         primary_key=["id"], date_column="period_end",
         units={"change_pct": "% change in employment since November 2022"},
         transform=f"{FEEDBACK_BUILD} (build_entry_level): copy."),
    dict(id="hp_web_composition", processed="human_practice/web_composition.csv",
         sample="human_practice/wildai/monthly_topic_format.csv", source_ids=["wildai"],
         primary_key=["month", "label"], date_column="month",
         units={"documents": "documents in the month's sample", "tokens": "tokens in the month's sample",
                "token_share": "fraction of the month's sampled tokens (0-1)",
                "document_share": "fraction of the month's sampled documents (0-1)"},
         transform=f"{FEEDBACK_BUILD} (build_web_composition): sum monthly_topic_format.csv by month and label, "
                   "divide by the month total; checked against monthly_ai_share.csv."),
    dict(id="hp_ai_share", processed="human_practice/ai_share.csv", sample="human_practice/wildai/monthly_ai_share.csv",
         source_ids=["wildai"], primary_key=["month", "kind"], date_column="month",
         units={"share": "fraction of tokens labelled AI (0-1)", "lo80": "fraction (0-1), 80% interval lower bound",
                "hi80": "fraction (0-1), 80% interval upper bound", "lo95": "fraction (0-1), 95% interval lower bound",
                "hi95": "fraction (0-1), 95% interval upper bound", "documents": "documents", "tokens": "tokens",
                "ai_tokens": "tokens labelled AI"},
         transform=f"{FEEDBACK_BUILD} (build_ai_share): stack observed rows and forecast rows. Observed data end "
                   "2026-08; rows after that (kind = forecast, to 2030-12) are the paper's forecast, so "
                   "latest_observation is the last forecast month."),
    dict(id="hp_fig3_points", processed="human_practice/fig3_points.csv", sample="human_practice/wildai/losses.csv",
         source_ids=["wildai"], primary_key=["name"],
         units={"budget": "human tokens per parameter",
                "x": "AI tokens added per human token", "bpb": "bits per byte on C4",
                "ctrl_bpb": "bits per byte on C4 (human-only control)", "change_pct": "% vs human-only control"},
         transform=f"{FEEDBACK_BUILD} (build_fig3_points): join models.csv and losses.csv, compare each run with "
                   "its group's human-only control."),
    dict(id="hp_cost", processed="human_practice/cost.csv", sample="human_practice/wildai/cost_of_not_filtering.csv",
         source_ids=["wildai"], primary_key=["target", "model_size", "ai_share"],
         units={"n_params": "parameters", "human_tpp": "human tokens per parameter",
                "ai_share": "fraction of training tokens written by AI (0-1)",
                "cost": "compute multiplier (1 = human-only); prediction from a fitted law"},
         transform=f"{FEEDBACK_BUILD} (build_cost): label model size and scenario."),
    dict(id="hp_definitions", processed="human_practice/definitions.csv",
         sample="human_practice/schaeffer/section_a_schaeffer_table.csv", source_ids=["schaeffer_2025"],
         primary_key=["id"], units={},
         transform=f"{FEEDBACK_BUILD} (build_definitions): add short_name, families, collapse_accumulate, "
                   "collapse_replace (from the paper) and covered_in, coverage_note (group judgement)."),
    # Moral degradation ---------------------------------------------------------------------------------------------
    dict(id="ai_incidents", processed="ai_incidents.csv", sample="ai_incidents/mongodump_full_snapshot/incidents.csv",
         source_ids=["aiid_snapshot"], primary_key=["_id"], date_column="date", units={},
         transform=f"{MORAL_BUILD} (transform1): keep _id and date."),
    dict(id="ai_reports", processed="ai_reports.csv", sample="ai_incidents/mongodump_full_snapshot/reports.csv",
         source_ids=["aiid_snapshot"], primary_key=["_id"], units={},
         transform=f"{MORAL_BUILD} (transform1): keep _id, date_published and date_submitted. Some dates are "
                   "malformed in the source (e.g. {'$numberLong': ...}), so they are kept as text and no date "
                   "column is declared; the app parses them and drops the malformed ones. Latest: 2026-11-15."),
    dict(id="classifications_gmf", processed="classifications_GMF.csv",
         sample="ai_incidents/mongodump_full_snapshot/classifications_GMF.csv", source_ids=["aiid_gmf"],
         primary_key=["Incident ID"], units={},
         transform=f"{MORAL_BUILD} (transform1): copied unchanged."),
    dict(id="human_validation_scores", processed="human_validation_scores_merged.csv",
         sample="human_validation_scores_merged.csv", source_ids=["llm_ethics_benchmark"],
         primary_key=["validation_id"],
         units={c: "score (0-10)" for c in ["gpt55_score", "human_score_E1", "human_score_E2", "human_score_E3",
                                           "human_mean_score"]},
         transform=f"{MORAL_BUILD} (acquire2): downloaded and copied unchanged."),
    dict(id="ai_validation_scores", processed="ai_validation_scores_merged.csv", sample="gpt55_scores.csv",
         source_ids=["llm_ethics_benchmark"], primary_key=["judge_model_id", "evaluated_model_id", "run_id", "item_id"],
         units={"score": "score (0-10)"},
         transform=f"{MORAL_BUILD} (transform2): stack gpt55_scores.csv, deepseek_v4_pro_scores.csv and "
                   "qwen3_6_plus_scores.csv."),
    dict(id="girai_frameworks", processed="GIRAI_Frameworks.csv", sample="GIRAI_Global_Survey_dataset.xlsx",
         source_ids=["girai"], primary_key=["ISO3", "indicator"],
         units={"fr_counts": "number of frameworks", "Unnamed: 0": "row number added by pandas"},
         transform=f"{MORAL_BUILD} (transform3): sheet 'frameworks' to CSV (adds the row-number column Unnamed: 0)."),
    dict(id="girai_classifications", processed="GIRAI_Classifications.csv", sample="GIRAI_Global_Survey_dataset.xlsx",
         source_ids=["girai"], primary_key=["ISO3"],
         units={"GDP_per_capita_PPP": "international $ (PPP)", "Unnamed: 0": "row number added by pandas"},
         transform=f"{MORAL_BUILD} (transform3): sheet 'country_classifications' to CSV."),
    *[dict(id=f"ipsos_{key}", processed=f"Ipsos_{key}_trust.csv", sample=pdf, source_ids=[src],
           primary_key=["Country"], units={c: "% of respondents" for c in ["Agree", "Unsure", "Disagree"]},
           transform=f"{MORAL_BUILD} (transform4): pdfplumber text extraction of {page} of the PDF.")
      for key, pdf, src, page in [
          ("gov", "Ipsos-AI-Monitor-2025.pdf", "ipsos_ai_monitor_2025", "page 23"),
          ("comp", "Ipsos-AI-Monitor-2026.pdf", "ipsos_ai_monitor_2026", "page 17"),
          ("ai_env", "Ipsos-AI-Monitor-2026.pdf", "ipsos_ai_monitor_2026", "page 21"),
          ("job_sec", "Ipsos-AI-Monitor-2026.pdf", "ipsos_ai_monitor_2026", "page 26")]],
    dict(id="ai_policy_and_ethics", processed="ai_policy_and_ethics.csv", sample="ai_policy_and_ethics.csv",
         source_ids=["kaggle_ai_workforce"], primary_key=["respondent_id"],
         units={"ai_bias_concern_level": "rating (1-5)", "data_privacy_concern_level": "rating (1-5)"},
         transform=f"{MORAL_BUILD} (acquire5, transform5): copied."),
    dict(id="salary_and_satisfaction", processed="salary_and_satisfaction.csv", sample="salary_and_satisfaction.csv",
         source_ids=["kaggle_ai_workforce"], primary_key=["respondent_id"],
         units={"annual_salary_usd": "US$ per year", "salary_change_yoy_pct": "% change on previous year",
                "job_satisfaction_score": "rating (1-5)", "work_life_balance_score": "rating (1-5)"},
         transform=f"{MORAL_BUILD} (transform5): copied."),
    *[dict(id=f"sycophancy_study{n}", processed=proc, sample=proc, source_ids=["cheng_sycophancy"],
           primary_key=["response_id"],
           units={"rightorwrong": "rating (1-7)", "return_likelihood": "rating (1-7)", "response_quality": "rating (1-7)",
                  "repair_score": "scale score (1-7)", "trust_score": "scale score (1-7)",
                  "performance_trust_score": "scale score (1-7)", "moral_trust_score": "scale score (1-7)"},
           transform=f"{MORAL_BUILD} (transform6): keep 9 columns and add response_id (row number in the raw file).")
      for n, proc in [(2, "study2_responses.csv"), (3, "study3_responses.redacted.csv")]],
]

# Columns that are numeric but are codes or ranks, not measures.
DIMENSION_NUMBERS = {"question_id", "run_id", "scenarioNum", "period_code", "Incident ID", "id", "response_id",
                     "Unnamed: 0", "size_order"}
# Roles that the name rules below would get wrong.
ROLE_OVERRIDES = {("owid_nvidia_quarterly_revenue_segment", "Entity"): "dimension"}  # a revenue segment, not a place
TIME_NAMES = {"year", "Year", "Day", "Quarter", "observation_date", "month", "date", "date_published",
              "date_submitted", "period_code", "period_label", "period_order", "period_start", "period_end"}
GEO_NAMES = {"geo", "ref_area", "Entity", "Code", "ISO3", "country", "Country", "region", "subregion",
             "World region according to OWID"}
MAX_ALLOWED = 12  # list allowed values for categorical columns with at most this many distinct values


def read(path: Path) -> pd.DataFrame:
    # Exactly how the A2 checker reads a CSV: every value as text, only empty fields missing.
    return pd.read_csv(path, dtype=object, keep_default_na=False, na_values=[""])


def infer_type(s: pd.Series, is_date: bool) -> str:
    v = s.dropna()
    if is_date:
        return "date"
    if len(v) and v.str.lower().isin({"true", "false"}).all():
        return "boolean"
    num = pd.to_numeric(v, errors="coerce")
    if len(v) and num.notna().all():
        leading_zero = v.str.match(r"^0\d").any()
        if leading_zero:
            return "string"
        return "integer" if (num == num.round()).all() and not v.str.contains(r"[.eE]").any() else "number"
    return "string"


def column_spec(name: str, s: pd.Series, spec: dict) -> dict:
    is_date = name == spec.get("date_column")
    kind = infer_type(s, is_date)
    if (spec["id"], name) in ROLE_OVERRIDES:
        role = ROLE_OVERRIDES[(spec["id"], name)]
    elif name in GEO_NAMES:
        role = "geography"
    elif is_date or name in TIME_NAMES:
        role = "time"
    elif name in spec["primary_key"] or name in DIMENSION_NUMBERS or name.endswith("_id"):
        role = "identifier"
    elif kind in {"integer", "number"} and name not in DIMENSION_NUMBERS:
        role = "measure"
    else:
        role = "dimension"
    out = {"type": kind, "role": role, "nullable": bool(s.isna().any())}
    v = s.dropna()
    if role == "measure":
        unit = spec["units"].get(name)
        if not unit:
            raise SystemExit(f"{spec['id']}: measure column {name!r} has no unit")
        num = pd.to_numeric(v)
        out.update(unit=unit, minimum=float(num.min()), maximum=float(num.max()))
        if kind == "integer":
            out.update(minimum=int(num.min()), maximum=int(num.max()))
    elif name in spec["units"]:
        out["unit"] = spec["units"][name]
    if kind == "date":
        d = pd.to_datetime(v, utc=True)
        out.update(date_minimum=d.min().date().isoformat(), date_maximum=d.max().date().isoformat())
    if kind in {"string", "boolean"} and role in {"dimension", "geography"} and 0 < v.nunique() <= MAX_ALLOWED:
        vals = sorted(v.unique().tolist())
        out["allowed_values"] = [x.lower() == "true" for x in vals] if kind == "boolean" else vals
    return out


def build() -> dict:
    source_ids = {s["id"] for s in SOURCES}
    datasets, transforms = [], {}
    for spec in DATASETS:
        proc, sample = PROC / spec["processed"], RAW / spec["sample"]
        for p in (proc, sample):
            if not (ROOT / p).exists():
                raise SystemExit(f"{spec['id']}: missing file {p}")
        missing = set(spec["source_ids"]) - source_ids
        if missing:
            raise SystemExit(f"{spec['id']}: unknown sources {missing}")
        frame = read(ROOT / proc)
        key = spec["primary_key"]
        if frame[key].isna().any().any() or frame.duplicated(key).any():
            raise SystemExit(f"{spec['id']}: primary key {key} is not unique and non-null")
        entry = {
            "id": spec["id"],
            "source_ids": spec["source_ids"],
            "sample": sample.as_posix(),
            "processed_output": proc.as_posix(),
            "format": "csv",
        }
        if spec.get("date_column"):
            dates = pd.to_datetime(frame[spec["date_column"]], utc=True)
            entry["date_column"] = spec["date_column"]
            entry["latest_observation"] = dates.max().date().isoformat()
        entry["primary_key"] = key
        entry["minimum_rows"] = len(frame)
        entry["columns"] = {c: column_spec(c, frame[c], spec) for c in frame.columns}
        datasets.append(entry)
        transforms[spec["id"]] = spec["transform"]
    return {
        "schema_version": 2,
        "title": "AI: Gains vs Hidden Costs - data dictionary",
        "description": (
            "Machine-readable data dictionary in the Assignment 2 Part C standard. `sources` and `datasets` follow "
            "the A2 manifest schema; `transforms` gives the step that produced each processed file. Built by "
            "scripts/build_dictionary.py from the files in data/. Dates are read as the A2 checker reads them: "
            "a year such as 2025 is 2025-01-01 and a quarter such as 2026-Q3 is 2026-07-01."
        ),
        "pipelines": [
            {"part": "Profitability", "acquisition_method": "manual download",
             "acquisition_path": "data/raw", "transform_command": PROFIT_BUILD.split()},
            {"part": "Feedback loop and cognition", "acquisition_method": "copy from cited repositories and papers",
             "acquisition_path": "src/narrative/human_practice_data.py", "transform_command": FEEDBACK_BUILD.split()},
            {"part": "Moral degradation", "acquisition_method": "script",
             "acquisition_path": "scripts/data.py", "transform_command": MORAL_BUILD.split()},
        ],
        "sources": SOURCES,
        "datasets": datasets,
        "transforms": transforms,
    }


if __name__ == "__main__":
    manifest = build()
    text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120)
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(manifest['sources'])} sources, {len(manifest['datasets'])} datasets")
