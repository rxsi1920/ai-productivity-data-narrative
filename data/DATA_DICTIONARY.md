# Data dictionary

This file covers every dataset the app reads, page by page:
- **Source columns:** where the data comes from, its URL and licence.
- **Structure columns:** columns and units, primary key, time coverage, latest observation and row count.
- **Transform column:** how the processed file is built from the raw file.

`data/raw/` holds the source samples, and `data/processed/` holds the only files the app reads.

1. [Profitability](#1-profitability), owner Nhi Nguyen
2. [Feedback loop and cognition](#2-feedback-loop-and-cognition), files under `human_practice/`
3. [Moral degradation](#3-moral-degradation)

---

## 1. Profitability

Rebuild: `python src/narrative/tabs/profitability/build_processed.py`. Last refresh: 22 Oct 2026.

`data/raw/` holds the 25 source samples, unmodified as downloaded on 21–22 Oct 2026, except the files marked **extract**, whose filter is stated. Each file was checked against its live source by row count and column total at download.

`data/processed/` holds the only files `tab.py` reads. `build_processed.py` builds every one of them. Each processed file has the same name as its raw file and is the raw file:
- restricted to the analysis window (rows from the first period listed in `PROFIT_FILES` onward),
- with exact duplicate rows dropped,
- sorted by its key columns.

Column names are kept, so every figure can be traced back to the raw source. Re-running the script on unchanged raw files gives byte-identical output.

All further calculations (growth rates, indices, ratios, correlations) are done in `tab.py`. They are shown in each chart’s ⓘ table and in the Appendix (“Figures & calculations”).

Units: SAAR = seasonally adjusted annual rate; int-$ PPP = international dollars at purchasing-power parity; pp = percentage points.

| File (raw → processed, same name) | Source | URL | Licence | Columns (units) | Primary key | Time coverage | Latest obs. | Rows | Transform: build_processed.py → app.py |
|---|---|---|---|---|---|---|---|---|---|
| `owid_share-companies-using-artificial-intelligence.csv` | McKinsey Global Survey via Stanford AI Index / Our World in Data | https://ourworldindata.org/grapher/share-companies-using-artificial-intelligence | CC BY 4.0 | `Entity`: region; `Code`: code (blank for regions); `Year`: survey year; `Organizations reporting having adopted AI`: % of organisations using AI in ≥1 business function | Entity, Year | 2021 – 2025 (2021, 2022, 2023, 2024, 2025) | 2025 | 30 | rows with Year ≥ 2021; dedupe, sort → Plotted as published; 2025 − 2022 change (pp) |
| `owid_estimated-share-people-generative-ai.csv` | Microsoft AI Economy Institute via OWID | https://ourworldindata.org/grapher/estimated-share-people-generative-ai | CC BY 4.0 | `Entity`: country/region; `Code`: ISO3; `Day`: date of estimate; `Estimated share of working-age adults who use generative AI`: % of adults 15–64; `GDP per capita`: int-$ (2021 prices, PPP); `World region according to OWID`: region name | Code, Day | 2025-06-30 – 2026-03-31 (2025-06-30, 2025-12-31, 2026-03-31) | 2026-03-31 | 444 | dedupe, sort → Latest Day, 3-letter codes; joined to ILO productivity on ISO3 |
| `eurostat_isoc_eb_ai.csv` | Eurostat, ICT usage in enterprises (isoc_eb_ai) | https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table | CC BY 4.0 | `indic_is`: indicator code (E_AI_TANY = uses ≥1 AI technology); `geo`: country code; `year`: survey year; `value`: % of enterprises with 10+ staff; `flag`: Eurostat flag | indic_is, geo, year | 2021 – 2025 (2021, 2023, 2024, 2025) | 2025 | 235 | rows with year ≥ 2021; dedupe, sort → E_AI_TANY pivoted geo × year; change 2021→2025 (pp) |
| `eurostat_isoc_eb_ain2_industry.csv` | Eurostat isoc_eb_ain2 | https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ain2/default/table | CC BY 4.0 | `nace_r2`: industry (NACE section); `geo`: EU27_2020; `year`: survey year; `value`: % of enterprises using AI; `flag`: Eurostat flag | nace_r2, year | 2021 – 2025 (2021, 2023, 2024, 2025) | 2025 | 36 | rows with year ≥ 2021; dedupe, sort → NACE codes mapped to 6 industry names |
| `eurostat_isoc_eb_ai_size.csv` | Eurostat isoc_eb_ai | https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table | CC BY 4.0 | `size_emp`: size class (employees); `geo`: EU27_2020; `year`: survey year; `value`: % of enterprises using AI; `flag`: Eurostat flag | size_emp, year | 2021 – 2025 (2021, 2023, 2024, 2025) | 2025 | 16 | rows with year ≥ 2021; dedupe, sort → Large ÷ small, 2025 |
| `eurostat_isoc_eb_ai_barriers.csv` | Eurostat isoc_eb_ai | https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table | CC BY 4.0 | `indic_is`: barrier code (E_AI_B*) or E_AI_EC; `geo`: EU27_2020; `year`: survey year; `value`: % of all enterprises; `flag`: Eurostat flag | indic_is, year | 2023 – 2025 (2023, 2024, 2025) | 2025 | 27 | rows with year ≥ 2023; dedupe, sort → Each barrier ÷ E_AI_EC × 100 = % of firms that considered AI but don't use it |
| `owid_private-investment-in-artificial-intelligence-cset.csv` | CSET via OWID (extract: 2022–2025) | https://ourworldindata.org/grapher/private-investment-in-artificial-intelligence-cset | CC BY 4.0 | `Entity`: country/region; `Code`: ISO3 or OWID code; `Year`: year; `Estimated funding raised by privately held AI companies - Field: All`: constant 2021 US$ | Code, Year | 2022 – 2025 (2022, 2023, 2024, 2025) | 2025 | 392 | rows with Year ≥ 2022; dedupe, sort → Sum 2022–25 by country ÷ 1e9; US ÷ World |
| `owid_global-investment-in-generative-ai.csv` | Quid via Stanford AI Index 2026 / OWID | https://ourworldindata.org/grapher/global-investment-in-generative-ai | CC BY 4.0 | `Entity`: World; `Code`: OWID_WRL; `Year`: year; `Global investment in generative AI`: constant 2021 US$ | Year | 2019 – 2025 | 2025 | 7 | rows with Year ≥ 2019; dedupe, sort → ÷ 1e9 |
| `owid_nvidia-quarterly-revenue-segment.csv` | NVIDIA filings via OWID | https://ourworldindata.org/grapher/nvidia-quarterly-revenue-segment | CC BY 4.0 | `Entity`: segment; `Quarter`: fiscal quarter as labelled by OWID; `NVIDIA’s quarterly revenue`: nominal US$ | Entity, Quarter | 2019-Q1 – 2026-Q3 | 2026-Q3 | 93 | dedupe, sort → ÷ 1e9; data-centre latest ÷ 2022-Q4 |
| `owid_data-centers-share-electricity-demand.csv` | IEA Energy and AI (numerator) and Ember (denominator) via OWID | https://ourworldindata.org/grapher/data-centers-share-electricity-demand | CC BY 4.0 (IEA Energy and AI; Ember) | `Entity`: country/region; `Code`: code; `Year`: year; `Share of total electricity demand coming from data centers`: % of electricity demand | Entity, Year | 2020 – 2025 (2020, 2023, 2024, 2025) | 2025 | 40 | rows with Year ≥ 2020; dedupe, sort → Plotted as published |
| `owid_gdp-per-capita-growth.csv` | World Bank WDI NY.GDP.PCAP.KD.ZG via OWID (extract: 7 regions) | https://ourworldindata.org/grapher/gdp-per-capita-growth | CC BY 4.0 | `Entity`: region; `Code`: code; `Year`: year; `GDP per capita growth (annual %)`: % change in real GDP per person | Entity, Year | 2015 – 2025 | 2025 | 77 | rows with Year ≥ 2015; dedupe, sort → Pivot year × region |
| `ilo_output_per_hour.csv` | ILO modelled estimates, SDMX DF_GDP_2HRW_NOC_NB | https://sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB | CC BY 4.0 | `ref_area`: ILO region code (X01 = World …); `year`: year; `value`: GDP per hour worked, 2021 int-$ PPP; `obs_status`: ILO status flag | ref_area, year | 2015 – 2027 | 2027 | 104 | rows with year ≥ 2015; dedupe, sort → Annualised growth 2015–19 and 2022–25 (2026–27 projections not used) |
| `ilo_output_per_hour_countries.csv` | ILO, same dataflow (extract: countries; 2015, 2019, 2022, 2025) | https://sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB/all | CC BY 4.0 | `ref_area`: ISO3; `year`: year; `value`: GDP per hour worked, 2021 int-$ PPP | ref_area, year | 2015 – 2025 (2015, 2019, 2022, 2025) | 2025 | 750 | rows with year ≥ 2015; dedupe, sort → Growth 2022–25 and minus 2015–19; join to gen-AI use on ISO3 |
| `ilo_labour_income_share.csv` | ILO, SDMX DF_LAP_2GDP_NOC_RT | https://sdmx.ilo.org/rest/data/ILO,DF_LAP_2GDP_NOC_RT | CC BY 4.0 | `ref_area`: ILO region code; `year`: year; `value`: labour income share, % of GDP; `obs_status`: ILO status flag | ref_area, year | 2015 – 2026 | 2026 | 96 | rows with year ≥ 2015; dedupe, sort → Change 2019→2025 (pp); capital share = 100 − value |
| `fred_CP.csv` | US BEA via FRED, series CP | https://fred.stlouisfed.org/series/CP | Public domain (US BEA) | `observation_date`: quarter start date; `CP`: corporate profits after tax, US$bn SAAR | observation_date | 2015-01-01 – 2026-04-01 | 2026-04-01 | 46 | dedupe, sort → Index 2022Q4 = 100; CP ÷ GDP × 100 |
| `fred_GDP.csv` | US BEA via FRED, series GDP | https://fred.stlouisfed.org/series/GDP | Public domain (US BEA) | `observation_date`: quarter start date; `GDP`: nominal GDP, US$bn SAAR | observation_date | 2015-01-01 – 2026-04-01 | 2026-04-01 | 46 | dedupe, sort → Index 2022Q4 = 100; denominator of profit share |
| `fred_COE.csv` | US BEA via FRED, series COE | https://fred.stlouisfed.org/series/COE | Public domain (US BEA) | `observation_date`: quarter start date; `COE`: compensation of employees, US$bn SAAR | observation_date | 2015-01-01 – 2026-04-01 | 2026-04-01 | 46 | dedupe, sort → Index 2022Q4 = 100 |
| `fred_OPHNFB.csv` | US BLS via FRED, series OPHNFB | https://fred.stlouisfed.org/series/OPHNFB | Public domain (US BLS) | `observation_date`: quarter start date; `OPHNFB`: nonfarm business output per hour, index 2017 = 100 | observation_date | 2015-01-01 – 2026-04-01 | 2026-04-01 | 46 | dedupe, sort → Annualised growth by period (Appendix) |
| `fred_ULCNFB.csv` | US BLS via FRED, series ULCNFB | https://fred.stlouisfed.org/series/ULCNFB | Public domain (US BLS) | `observation_date`: quarter start date; `ULCNFB`: nonfarm business unit labour cost, index 2017 = 100 | observation_date | 2015-01-01 – 2026-04-01 | 2026-04-01 | 46 | dedupe, sort → Annualised growth by period (Appendix) |
| `eurostat_nasa_10_ki_profit_share.csv` | Eurostat nasa_10_ki (B2G_B3G_RAT_S11) | https://ec.europa.eu/eurostat/databrowser/view/nasa_10_ki/default/table | CC BY 4.0 | `geo`: country code; `year`: year; `value`: profit share of non-financial corporations, %; `flag`: Eurostat flag | geo, year | 2019 – 2025 | 2025 | 204 | rows with year ≥ 2019; dedupe, sort → EU27 index 2019 = 100; country change 2021→2024 (pp) |
| `eurostat_nasa_10_ki_consumption_growth.csv` | Eurostat nasa_10_ki (P4_R_HAB_GR) | https://ec.europa.eu/eurostat/databrowser/view/nasa_10_ki/default/table | CC BY 4.0 | `geo`: country code; `year`: year; `value`: real household consumption per person, % change on previous year; `flag`: Eurostat flag | geo, year | 2019 – 2025 | 2025 | 204 | rows with year ≥ 2019; dedupe, sort → Average 2022–2024 (Appendix) |
| `eurostat_nama_10_lp_ulc.csv` | Eurostat nama_10_lp_ulc | https://ec.europa.eu/eurostat/databrowser/view/nama_10_lp_ulc/default/table | CC BY 4.0 | `na_item`: RLPR_HW (real labour productivity per hour) or NULC_HW (nominal unit labour cost per hour); `geo`: country code; `year`: year; `value`: index, 2015 = 100; `flag`: Eurostat flag | na_item, geo, year | 2019 – 2025 | 2025 | 476 | rows with year ≥ 2019; dedupe, sort → Growth 2021→2025 per country |
| `eurostat_nama_10_a10_industry.csv` | Eurostat nama_10_a10 | https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10/default/table | CC BY 4.0 | `unit`: CLV20_MEUR (real, €m 2020 prices) or CP_MEUR (current €m); `nace_r2`: industry; `na_item`: B1G (value added) or D1 (compensation of employees); `geo`: EU27_2020; `year`: year; `value`: € million; `flag`: Eurostat flag | unit, nace_r2, na_item, year | 2019 – 2025 | 2025 | 168 | rows with year ≥ 2019; dedupe, sort → Real value added ÷ hours (with hours file); growth 2021→2025 |
| `eurostat_nama_10_a10_e_hours.csv` | Eurostat nama_10_a10_e | https://ec.europa.eu/eurostat/databrowser/view/nama_10_a10_e/default/table | CC BY 4.0 | `nace_r2`: industry; `geo`: EU27_2020; `year`: year; `value`: thousand hours worked (total employment); `flag`: Eurostat flag | nace_r2, year | 2019 – 2025 | 2025 | 56 | rows with year ≥ 2019; dedupe, sort → Denominator of productivity per hour |
| `eurostat_une_rt_a.csv` | Eurostat une_rt_a | https://ec.europa.eu/eurostat/databrowser/view/une_rt_a/default/table | CC BY 4.0 | `age`: Y15-24 or Y15-74; `geo`: country code; `year`: year; `value`: unemployment rate, % of labour force; `flag`: Eurostat flag | age, geo, year | 2019 – 2025 | 2025 | 490 | rows with year ≥ 2019; dedupe, sort → Unweighted mean, top-8 AI adopters vs rest; change since 2022 (pp) |


---

## 2. Feedback loop and cognition

Every number on the page is in, or computed from, a file in `data/processed/`. `python -m narrative.human_practice_data` rebuilds all eight
from the source copies and writes the SHA-256 of every input to `data/processed/human_practice/MANIFEST.json`. Last refresh: 11 Nov 2026.

### Source samples

| File | Source and URL | Licence | Primary key | Time coverage | Latest observation |
|---|---|---|---|---|---|
| `data/raw/human_practice/workforce/btos_ai.csv` | US Census Bureau, Business Trends and Outlook Survey, https://www.census.gov/hfp/btos (via Karan Makhija's repo, commit `b33f3b2`) | US government work (not re-checked) | `period_code`, `answer_id` | 2025-P24 to 2026-P21, 24 two-week periods | 2026-P21 |
| `data/raw/human_practice/workforce/evidence.csv` | Hand-built by Karan Makhija from five papers; URL per row in `source_url` (same repo and commit) | Cited facts | `id` | Studies published 2023 to 2025 | 2025 |
| `data/raw/human_practice/workforce/entry_level_employment.csv` | Brynjolfsson, Chandar and Chen (Aug 2026), https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf | Cited facts; ADP microdata are proprietary | `id` | November 2022 to June 2026 | June 2026 |
| `data/raw/human_practice/wildai/*.csv` (6 files) | Russell et al. (2026), arXiv:2609.40295 v1; https://github.com/pangramlabs/WildAI commit `795a718` | CC BY-NC-SA 4.0 | see processed tables | January 2021 to August 2026 observed; forecast to December 2030 | August 2026 |
| `data/raw/human_practice/schaeffer/section_a_schaeffer_table.csv` | Written from Schaeffer et al. (2025), arXiv:2503.03150 v2 | Cited facts | row order (definition 1 to 8) | not applicable | 2025 |

### Processed files

| File | Rows | Primary key | Columns (units) | Transform (`src/narrative/human_practice_data.py`) |
|---|---|---|---|---|
| `human_practice/adoption.csv` | 72 | `period_code`, `answer` | `period_order` (1 to 24), `period_code`, `period_label`, `question_id`, `answer` (Yes / No / Do not know), `share_pct` (% of US firms) | `build_adoption`: rename `value_pct`, add `period_order` by sorting `period_code`, drop `answer_id` and `raw_value` |
| `human_practice/evidence.csv` | 6 | `id` | Karan's 16 columns plus `panel_title`; `sample_size` (people), `direction` (gain / loss), `evidence_strength` (High / Medium / Low, a judgement) | `build_evidence`: add `panel_title` |
| `human_practice/entry_level.csv` | 4 | `id` | `group`, `age_group`, `exposure_group`, `change_pct` (% change in employment, baseline November 2022), `period_start`, `period_end`, `measure`, `highlight`, `source`, `source_url`, `location_in_source`, `check_status` | `build_entry_level`: copy |
| `human_practice/web_composition.csv` | 183 | `month`, `label` | `month`, `label` (AI / Human / Mixed), `documents`, `tokens`, `token_share` and `document_share` (fraction of that month's sample), `sampling_source` | `build_web_composition`: sum `monthly_topic_format.csv` by month and label, divide by the month total. Validation checks the AI share equals `monthly_ai_share.csv` |
| `human_practice/ai_share.csv` | 114 | `month`, `kind` | `kind` (observed / forecast), `share` (fraction of tokens labelled AI), `lo80`, `hi80`, `lo95`, `hi95`, `sampling_source`, `documents`, `tokens`, `ai_tokens` | `build_ai_share`: stack observed and forecast rows |
| `human_practice/fig3_points.csv` | 287 | `name` | `group`, `size`, `budget` (human tokens per parameter), `arm` (ai / human), `x` (tokens added per human token), `bpb` and `ctrl_bpb` (bits per byte on C4), `change_pct` (% vs human-only control), `in_figure` | `build_fig3_points`: join `models.csv` and `losses.csv`, compare each run with its group's control |
| `human_practice/cost.csv` | 462 | `target`, `model_size`, `ai_share` | `n_params`, `human_tpp` (tokens per parameter), `ai_share` (fraction), `scenario`, `cost` (compute multiplier, 1 = human-only; a fitted-law prediction) | `build_cost`: label model size and scenario |
| `human_practice/definitions.csv` | 8 | `id` | Schaeffer table columns plus `short_name`, `families`, `collapse_accumulate`, `collapse_replace` (paper's Appendix A Table 1), `covered_in`, `coverage_note` (our judgement) | `build_definitions` |

### Known limits of the data
- BTOS: US firms only; one question; the calendar dates of the periods were not re-checked.
- Evidence: single firms or single tasks; strength ratings are judgements.
- Entry-level: descriptive, one payroll provider, values rounded in the paper and entered from an automated summary.
- WildAI: about 5,000 sampled documents a month, labelled by one detector; shares, not volumes; model results are for
  pre-training of models up to 268M parameters; cost and forecast values are predictions.


---



## 4. Moral degradation

### Datasets

Built by `scripts/data.py` (`acquireN` downloads into `data/raw/` and skips files that already exist; `transformN` writes `data/processed/`). Licences match the Sources table on the Moral degradation page. Last data refresh: 16 Nov 2026.

| Processed file | Raw file | Source | URL | Licence | Columns (units) | Primary key | Time coverage | Latest obs. | Rows | Transform (`scripts/data.py`) |
|---|---|---|---|---|---|---|---|---|---|---|
| `ai_incidents.csv` | `ai_incidents/mongodump_full_snapshot/incidents.csv` | AI Incident Database (Responsible AI Collaborative), full snapshot | https://incidentdatabase.ai/research/snapshots/ | CC BY-SA 4.0 | `_id`: incident id; `date`: date of incident (YYYY-MM-DD) | `_id` | 1983-09-26 to 2026-11-12 | 2026-11-12 | 1,817 | `transform1`: keep `_id`, `date` |
| `ai_reports.csv` | `ai_incidents/mongodump_full_snapshot/reports.csv` | AI Incident Database, same snapshot | as above | Dates only; AIID's CC BY-SA 4.0 grant excludes report text (text not used) | `_id`: report id; `date_published`, `date_submitted`: ISO timestamps (some malformed; 809 blank/unparseable `date_submitted`) | `_id` | submitted 2019-06-01 to 2026-11-15 | 2026-11-15 | 8,143 | `transform1`: keep 3 columns. App: count per year, 2010–2025; forecast fan from the selected year |
| `classifications_GMF.csv` | `ai_incidents/mongodump_full_snapshot/classifications_GMF.csv` (AIID GMF taxonomy export, as downloaded) | AI Incident Database, Goals-Methods-Failures (GMF) taxonomy export | https://incidentdatabase.ai/taxonomies/gmf/ | CC BY-SA 4.0 | `Incident ID`; known/potential AI goal, technology and technical failure (comma-separated labels), with snippets and discussion | `Incident ID` | incidents classified to date | 2026-11-12 (same snapshot as incidents) | 326 | `transform1`: copied unchanged. App: split `Known AI Technical Failure`, count incidents per label |
| `human_validation_scores_merged.csv` | same name | Scientometric LLM Ethics Benchmark, `scoring_results/` | https://github.com/universe-szw/scientometric-llm-ethics-benchmark | MIT | `dimension` (5: content_safety, privacy, ethics_bias, robustness, values); `evaluated_model_name` (8 models); `gpt55_score` and `human_score_E1..E3`, `human_mean_score` (0–10); behaviour/unsafe flags (yes/no) | `validation_id` | one benchmark release | 2026 (GPT-5.5 judge) | 2,000 | `acquire2`: download; copied unchanged. App: mean by model and dimension |
| `ai_validation_scores_merged.csv` | `gpt55_scores.csv`, `deepseek_v4_pro_scores.csv`, `qwen3_6_plus_scores.csv` | same repo | same | MIT | `judge_model_id` (3 judges); `evaluated_model_name` (8); `dimension` (5); `item_id`; `score` (0–10); `behavior_match`, `unsafe_compliance`, `safe_alternative_present`; `status` | `judge_model_id`, `evaluated_model_id`, `run_id`, `item_id` | one benchmark release | 2026 | 59,995 | `transform2`: stack the three judge files |
| `GIRAI_Frameworks.csv` | `GIRAI_Global_Survey_dataset.xlsx`, sheet `frameworks` | Global Index on Responsible AI, Global Survey dataset | https://www.global-index.ai/ | CC BY 4.0 | `country`, `ISO3`, `dimension` (5), `pillar`, `indicator` (17 areas of responsible AI), `fr_counts` (number of frameworks), `fr1_type`… (Binding / Non-binding / Draft / No framework) | `ISO3`, `indicator` | GIRAI 2nd edition (evidence to Sep 2025, published 2026) | Sep 2025 | 2,295 | `transform3`: sheet → CSV (adds an index column `Unnamed: 0`). App: share of countries by legal status per area |
| `GIRAI_Classifications.csv` | same xlsx, sheet `country_classifications` | same | same | CC BY 4.0 | `country`, `ISO3`, `region`, `subregion`, `developing_status`, `WB_income_group`, `GDP_per_capita_PPP` (int-$) | `ISO3` | GIRAI 2nd edition | Sep 2025 | 135 | `transform3`: sheet → CSV. App: country-group filter |
| `Ipsos_gov_trust.csv` | `Ipsos-AI-Monitor-2025.pdf`, p. 23 | Ipsos AI Monitor 2025 | https://www.ipsos.com/sites/default/files/ct/publication/documents/2025-06/Ipsos-AI-Monitor-2025.pdf | © Ipsos; published figures, cited | `Country`; `Agree`, `Unsure`, `Disagree` (% of respondents) | `Country` | 2025 survey, 30 countries + average | 2025 | 31 | `transform4`: pdfplumber text extraction of the chart page |
| `Ipsos_comp_trust.csv` | `Ipsos-AI-Monitor-2026.pdf`, p. 17 | Ipsos AI Monitor 2026 | https://www.ipsos.com/sites/default/files/ct/news/documents/2026-06/Ipsos-AI-Monitor-2026.pdf | © Ipsos; cited | `Country`; `Agree`, `Disagree` (%) | `Country` | 2026, 32 countries + average | 2026 | 33 | `transform4` |
| `Ipsos_ai_env_trust.csv` | same PDF, p. 21 | same | same | same | same | `Country` | 2026 | 2026 | 33 | `transform4` |
| `Ipsos_job_sec_trust.csv` | same PDF, p. 26 | same | same | same | same | `Country` | 2026 | 2026 | 33 | `transform4` |
| `ai_policy_and_ethics.csv` | same name | Kaggle, "Global AI Adoption & Workforce Impact Survey 24–26" | https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26 | Apache 2.0 | `respondent_id`; `company_has_ai_policy`; `ai_bias_concern_level`, `data_privacy_concern_level` (1–5); `supports_ai_regulation`; `has_experienced_ai_misuse`; `trust_in_ai_decisions` (Low/Moderate/High) | `respondent_id` | 2024–2026 | 2026-04-07 (last updated) | 12,000 | `acquire5` / `transform5`: copy. App: modal trust level |
| `salary_and_satisfaction.csv` | same name | same | same | Apache 2.0 | `respondent_id`; `annual_salary_usd` (US$); `salary_change_yoy_pct` (%); `job_satisfaction_score`, `work_life_balance_score` (1–5); `ai_job_replacement_fear` (Likert); `burnout_level`; … | `respondent_id` | 2024–2026 | 2026-04-07 (last updated) | 12,000 | `transform5`: copy. App: modal `ai_job_replacement_fear` |
| `study2_responses.csv` | same name | Cheng et al. (2025), sycophancy experiments, OSF project smvw7 | https://osf.io/smvw7/ · Cheng et al., *Science* (2026) | CC BY 4.0 (paper and OSF release) | `rightorwrong`, `repair_score`, `trust_score`, `response_quality`, `return_likelihood` (1–7 scale); `scenarioNum` (1–4); `is_syco` (True/False) | row (one participant) | one experiment | 2026-03-26 | 804 | `acquire6` / `transform6`: keep 9 columns. App: sycophantic minus non-sycophantic means, 95% CI |
| `study3_responses.redacted.csv` | same name | same | same | CC BY 4.0 (paper and OSF release) | as Study 2, with `Condition` (syco / non-syco) and `scenarioNum` (text) | row | one experiment | 2026-03-26 | 800 | `transform6`: keep 9 columns |

Not used by any page (can be deleted or documented): `data/raw/ai_tool_usage.csv`, `data/raw/respondents.csv`, `data/raw/skills_and_training.csv`.
