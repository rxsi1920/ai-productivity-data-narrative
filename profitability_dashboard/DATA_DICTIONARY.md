# Data dictionary: profitability dashboard

`data/raw/` holds the 25 source samples, unmodified as downloaded on 21–22 Oct 2026, except the files marked **extract**, whose filter is stated. Each file was checked against its live source by row count and column total at download.

`data/processed/` holds the only files `app.py` reads. `scripts/build_processed.py` builds every one of them. Each processed file has the same name as its raw file and is the raw file:
- restricted to the analysis window (rows from the first period listed in `PROFIT_FILES` onward),
- with exact duplicate rows dropped,
- sorted by its key columns.

Column names are kept, so every figure can be traced back to the raw source. Re-running the script on unchanged raw files gives byte-identical output.

All further calculations (growth rates, indices, ratios, correlations) are done in `app.py`. They are shown in each chart’s ⓘ table and in the Appendix (“Figures & calculations”).

Units: SAAR = seasonally adjusted annual rate; int-$ PPP = international dollars at purchasing-power parity; pp = percentage points.

| Raw → processed file (same name) | Source and URL | Licence | Columns and units | Primary key | Time coverage | Latest obs. | Transform (build_processed.py → `build_profitability`, then the calculation in app.py) |
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
| `owid_data-centers-share-electricity-demand.csv` | IEA *Energy and AI* (data-centre consumption) and Ember (total demand) via OWID · ourworldindata.org/grapher/data-centers-share-electricity-demand | CC BY 4.0 (IEA *Energy and AI* report licence; Ember data) | Entity, Code, Year, % of electricity demand | Entity, Year | 2020, 2023–2025 | 2025 | None |
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
