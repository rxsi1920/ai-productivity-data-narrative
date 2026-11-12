# Data dictionary

`data/raw/` holds the source samples, unmodified as downloaded. Files marked **extract** are filtered (the filter is stated) because the full download was too large or contained data the app does not use.

`data/processed/` holds the only files the app reads. Every one is produced by `scripts/build_processed.py`. Each function in that script builds one processed file, and its docstring states the transform. Re-running the script on unchanged raw files gives byte-identical output.

Every raw file was checked against its live source by row count and column total at download.

**Download dates:**
- Profitability files and the PISA, Eurostat gen-AI use, Epoch AI and AI-incident files: 21–22 Oct 2026.
- Stack Overflow and Wikipedia files: 5 Nov 2026.

---

## A. Profitability page

For these files, processed = raw restricted to the analysis window (rows from the stated first period onward), with exact duplicates dropped and rows sorted. Column names are kept. All other calculations are done on screen and shown in each chart’s ⓘ table and in the page’s Appendix.

| Raw → processed file (same name) | Source and URL | Licence | Columns and units | Primary key | Time coverage | Latest obs. | Transform (build_processed.py → `build_profitability`, plus page calculation) |
|---|---|---|---|---|---|---|---|
| `owid_share-companies-using-artificial-intelligence.csv` | McKinsey Global Survey via Stanford AI Index / OWID · ourworldindata.org/grapher/share-companies-using-artificial-intelligence | CC BY 4.0 | Entity (region), Code, Year, % of organisations using AI in ≥1 function | Entity, Year | 2021–2025 | 2025 | Year ≥ 2021; plotted as published |
| `owid_estimated-share-people-generative-ai.csv` | Microsoft AI Economy Institute via OWID · …/estimated-share-people-generative-ai | CC BY 4.0 | Entity, Code (ISO3), Day, % of adults 15–64 using gen AI, GDP per capita (2021 int-$), OWID region | Code, Day | Jun 2025 – Mar 2026 | 2026-03-31 | None; page filters to the latest Day and 3-letter codes |
| `eurostat_isoc_eb_ai.csv` | Eurostat isoc_eb_ai · ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai | CC BY 4.0 | indic_is, geo, year, value = % of enterprises (10+ staff), flag | indic_is, geo, year | 2021–2025 | 2025 | Year ≥ 2021; page pivots E_AI_TANY to geo × year |
| `eurostat_isoc_eb_ain2_industry.csv` | Eurostat isoc_eb_ain2 | CC BY 4.0 | nace_r2, geo (EU27), year, % of enterprises using AI, flag | nace_r2, year | 2021, 2023–2025 | 2025 | Year ≥ 2021; page maps NACE codes to 6 industry names |
| `eurostat_isoc_eb_ai_size.csv` | Eurostat isoc_eb_ai | CC BY 4.0 | size_emp, geo (EU27), year, % of enterprises, flag | size_emp, year | 2021, 2023–2025 | 2025 | Year ≥ 2021; large ÷ small ratio for 2025 |
| `eurostat_isoc_eb_ai_barriers.csv` | Eurostat isoc_eb_ai | CC BY 4.0 | indic_is (barrier code), geo (EU27), year, % of all enterprises, flag | indic_is, year | 2023–2025 | 2025 | Year ≥ 2023; each barrier ÷ E_AI_EC × 100 |
| `owid_private-investment-in-artificial-intelligence-cset.csv` (**extract**: years 2022–2025) | CSET via OWID · …/private-investment-in-artificial-intelligence-cset | CC BY 4.0 | Entity, Code, Year, funding raised by private AI companies (constant 2021 US$) | Code, Year | 2022–2025 | 2025 | Sum 2022–25 per country ÷ 1e9; US share = US ÷ World |
| `owid_global-investment-in-generative-ai.csv` | Quid via AI Index 2026 / OWID | CC BY 4.0 | Entity, Code, Year, private investment in gen AI (constant 2021 US$) | Year | 2019–2025 | 2025 | ÷ 1e9 |
| `owid_nvidia-quarterly-revenue-segment.csv` | NVIDIA filings via OWID | CC BY 4.0 | Entity (segment), Quarter, revenue (US$) | Entity, Quarter | 2019-Q1 – 2026-Q3 | 2026-Q3 | ÷ 1e9; data-centre growth vs 2022-Q4 |
| `owid_data-centers-share-electricity-demand.csv` | IEA *Energy and AI* via OWID | CC BY 4.0 as published by OWID (TODO: confirm IEA terms) | Entity, Code, Year, % of electricity demand | Entity, Year | 2020, 2023–2025 | 2025 | None |
| `owid_gdp-per-capita-growth.csv` (**extract**: 7 regions, 2015+) | World Bank WDI NY.GDP.PCAP.KD.ZG via OWID | CC BY 4.0 | Entity, Code, Year, annual % growth of real GDP per person | Entity, Year | 2015–2025 | 2025 | Pivot year × region |
| `ilo_output_per_hour.csv` | ILO modelled estimates, SDMX DF_GDP_2HRW_NOC_NB · sdmx.ilo.org | CC BY 4.0 | ref_area (ILO region), year, GDP per hour worked (2021 int-$ PPP), obs_status | ref_area, year | 2015–2027 | 2025 used (later years are projections) | Annualised growth 2015–19 and 2022–25 |
| `ilo_output_per_hour_countries.csv` (**extract**: countries; 2015, 2019, 2022, 2025) | ILO, same dataflow · sdmx.ilo.org/rest/data/ILO,DF_GDP_2HRW_NOC_NB/all | CC BY 4.0 | ref_area (ISO3), year, GDP per hour worked (2021 int-$ PPP) | ref_area, year | 2015–2025 | 2025 (nowcast) | Growth 2022–25, and that minus 2015–19; joined to gen-AI use on ISO3 |
| `ilo_labour_income_share.csv` | ILO, SDMX DF_LAP_2GDP_NOC_RT | CC BY 4.0 | ref_area, year, labour income share (% of GDP), obs_status | ref_area, year | 2015–2026 | 2025 used | Change 2019→2025 (pp); capital share = 100 − value |
| `fred_CP.csv` | BEA via FRED, series CP · fred.stlouisfed.org/series/CP | Public domain (US BEA) | observation_date (quarter start), CP (US$bn, SAAR) | observation_date | 2015Q1–2026Q2 | 2026-04-01 | Index 2022Q4 = 100; profit share = CP ÷ GDP × 100 |
| `fred_GDP.csv` | BEA via FRED, series GDP | Public domain | observation_date, GDP (US$bn, SAAR) | observation_date | 2015Q1–2026Q2 | 2026-04-01 | Index 2022Q4 = 100 |
| `fred_COE.csv` | BEA via FRED, series COE | Public domain | observation_date, compensation of employees (US$bn, SAAR) | observation_date | 2015Q1–2026Q2 | 2026-04-01 | Index 2022Q4 = 100 |
| `fred_OPHNFB.csv`, `fred_ULCNFB.csv` | BLS via FRED | Public domain | observation_date, output per hour / unit labour cost (index 2017 = 100) | observation_date | 2015Q1–2026Q2 | 2026-04-01 | Annualised growth by period (Appendix table) |
| `eurostat_nasa_10_ki_profit_share.csv` | Eurostat nasa_10_ki (B2G_B3G_RAT_S11) | CC BY 4.0 | geo, year, profit share of non-financial corporations (%), flag | geo, year | 2019–2025 | 2025 | Index 2019 = 100 (EU27) |
| `eurostat_nasa_10_ki_consumption_growth.csv` | Eurostat nasa_10_ki | CC BY 4.0 | geo, year, household consumption growth (%), flag | geo, year | 2019–2025 | 2025 | Country outcome option (Europe scope) |
| `eurostat_nama_10_lp_ulc.csv` | Eurostat nama_10_lp_ulc | CC BY 4.0 | na_item, geo, year, value (index or %), flag | na_item, geo, year | 2019–2025 | 2025 | Productivity and unit-labour-cost growth 2021→2025 per country |
| `eurostat_nama_10_a10_industry.csv`, `eurostat_nama_10_a10_e_hours.csv` | Eurostat nama_10_a10, nama_10_a10_e | CC BY 4.0 | unit, nace_r2, na_item, geo (EU27), year, value added (€m) / hours worked (thousands), flag | nace_r2, (unit, na_item), year | 2019–2025 | 2025 | Real value added ÷ hours; growth 2021→2025 per industry |
| `eurostat_une_rt_a.csv` | Eurostat une_rt_a | CC BY 4.0 | age, geo, year, unemployment rate (%), flag | age, geo, year | 2019–2025 | 2025 | Unweighted mean, top-8 AI adopters vs the rest; change since 2022 (pp) |

## B. Cognitive page

| Raw file | Processed file | Source and URL | Licence | Columns and units (processed) | Primary key | Time coverage | Latest obs. | Transform (`build_processed.py`) |
|---|---|---|---|---|---|---|---|---|
| `owid_pisa-mathematics.csv` and `owid_pisa-reading_2012-2022.csv` (**extract**: 2012, 2015, 2018, 2022) | `pisa_scores.csv` | OECD PISA via OWID · ourworldindata.org/grapher/pisa-test-score-mean-performance-on-the-mathematics-scale (and …-reading-scale) | CC BY 4.0 | country, code (ISO3; "OECD" for the OECD average), year, subject (Mathematics / Reading), score (PISA points) | code, year, subject | 2012–2022 (raw maths file 2003–2022) | 2022 | `build_pisa`: stack the two files into long format; keep 2012–2022; keep the OECD average; drop the "PISA participants average"; round to 2 dp |
| `owid_share-of-young-people-in-european-countries-using-generative-ai-tools.csv` and `owid_share-europe-using-generative-ai.csv` | `eu_genai_use_2025.csv` | Eurostat (isoc_ai) via OWID · …/share-of-young-people-in-european-countries-using-generative-ai-tools, …/share-europe-using-generative-ai | CC BY 4.0 | country, code, year, pct_16_24 and pct_16_74 (% of age group using gen-AI tools in the last 3 months), youth_gap_pp (pp) | code | 2025 | 2025 | `build_eu_genai`: join on ISO3; youth gap = 16–24 minus 16–74 |
| `eurostat_isoc_eb_ai_barriers.csv` | `eu_ai_barriers.csv` | Eurostat isoc_eb_ai | CC BY 4.0 | code, barrier, group, year, pct_all_firms (% of all EU firms), pct_of_considerers (% of firms that considered AI but don’t use it) | code, year | 2023–2025 | 2025 | `build_barriers`: barrier ÷ E_AI_EC × 100; plain-English names and barrier groups (also used by the Ethical page) |

## C. Feedback-loop page

| Raw file | Processed file | Source and URL | Licence | Columns and units (processed) | Primary key | Time coverage | Latest obs. | Transform |
|---|---|---|---|---|---|---|---|---|
| `stackexchange_stackoverflow_questions_monthly.csv` | `stackoverflow_questions_monthly.csv` | Stack Exchange API v2.3 `/questions?site=stackoverflow&fromdate&todate&filter=total`, one call per calendar month · api.stackexchange.com/docs/questions | CC BY-SA 4.0 (Stack Exchange content) | month (YYYY-MM), questions (new questions created that month and still on the site), trailing_3m, index_2019_21 (2019–21 monthly mean = 100), after_chatgpt (bool) | month | 2015-01 – 2026-10 | 2026-10 | `build_stackoverflow`: index = month ÷ 2019–21 mean × 100; trailing 3-month mean; flag months from 2022-12 |
| `wikimedia_enwiki_user_pageviews_monthly.csv` | `wikipedia_pageviews_monthly.csv` | Wikimedia REST API `metrics/pageviews/aggregate/en.wikipedia/all-access/user/monthly` · wikimedia.org/api/rest_v1 | CC0 | month, views (page views by agent = user), views_bn (billions), trailing_12m_bn, index_vs_2019_21_same_month | month | 2016-01 – 2026-10 | 2026-10 | `build_wiki`: ÷ 1e9; trailing 12-month total; seasonal index vs the same month’s 2019–21 mean |
| `owid_ai-training-dataset-size_language.csv` (**extract**: Domain = Language; model names dropped) | `ai_training_data_language.csv` | Epoch AI via OWID · ourworldindata.org/grapher/artificial-intelligence-number-training-datapoints | CC BY 4.0 | model_row (surrogate key), Day (publication date), year, datapoints (training dataset size, ≈ words/tokens), log10_datapoints, year_median | model_row | 1993-06 – 2026-06 | 2026-06-29 | `build_training`: parse date; log10; yearly median; sort; add model_row |

## D. Ethical page

| Raw file | Processed file | Source and URL | Licence | Columns and units (processed) | Primary key | Time coverage | Latest obs. | Transform |
|---|---|---|---|---|---|---|---|---|
| `owid_annual-reported-ai-incidents-controversies.csv` | `ai_incidents_annual.csv` | AI Incident Database via Stanford AI Index 2025, published by OWID (chart since withdrawn; archived copy: archive.ourworldindata.org/20260304-094028/grapher/annual-reported-ai-incidents-controversies.html, indicator 1025675) | CC BY-ND 4.0 (AI Index) | year, incidents (reported per year), yoy_pct, index_2021 (2021 = 100) | year | 2012–2024 | 2024 | `build_incidents`: year-on-year %; index 2021 = 100 |
| `owid_share-companies-using-artificial-intelligence.csv` | `companies_using_ai.csv` | as in section A | CC BY 4.0 | year, pct_orgs_using_ai (%), index_2021 | year | 2021–2025 | 2025 | `build_companies`: "All geographies" rows; index 2021 = 100 |
| `eurostat_isoc_eb_ai_barriers.csv` | `eu_ai_barriers.csv` | as in section B | CC BY 4.0 | as in section B | code, year | 2023–2025 | 2025 | as in section B |

## E. Opening screen

| Processed file | Built from | Columns | Primary key | Transform |
|---|---|---|---|---|
| `ledger.csv` | the processed files above | side (Gain / Cost / Context), page, indicator, baseline_period, baseline_value, latest_period, latest_value, measure, evidence, change_pct (%) | indicator | `build_ledger`: change % = latest ÷ baseline − 1 for one headline indicator per page |
