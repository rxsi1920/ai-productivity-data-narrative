# Will investing in AI lift our productivity and profits?

A one-page Streamlit dashboard, framed as an investment brief for a **CEO / CFO deciding whether to invest in adopting AI**.
It answers the group question *"Has AI improved company profitability by enhancing productivity?"* using only public, citable data.

## Layout: one page, read top to bottom

Every chart title states its takeaway, and charts sit two per row.

- **Banner and five KPI tiles:**
  - firms using AI
  - adults using gen AI worldwide
  - private AI funding 2025
  - world productivity growth
  - US profits vs pay
- **Adoption: "Is AI becoming standard practice?"**
  - gen-AI use vs GDP per person (scatter)
  - company adoption by region
  - industry × year heatmap
  - firm-size bars
- **Investment: "How much capital is flowing into AI?"**
  - private AI funding by country, 2022–25 (CSET)
  - NVIDIA revenue
  - data-centre electricity share (IEA)
  - gen-AI private investment
- **Payoff: "Has it paid off in productivity and profits?"**
  - GDP per person growth by region, 2015–2025, with the COVID and 2022 war/energy-shock periods shaded (full width)
  - ILO productivity growth by region (dumbbell)
  - profit share indexed to 2019 for the US, EU and world
- **Evidence: "Where does AI actually pay off?"**
  - EU industry bubble chart
  - country quadrant scatter: World (142 countries, gen-AI use vs ILO productivity) or Europe (30 countries, Eurostat firm adoption), with an outcome picker
- **Distribution: "Who captures the gains?"**
  - US profits vs employee pay vs GDP
  - ILO labour-share change by region
- **Execution: "What does it take to capture the value?"**
  - barriers to AI adoption (Eurostat)
  - youth unemployment in AI-leading countries
- **Recommendation:** three implication tiles.
- **Appendix** (collapsed):
  - every figure's calculation
  - source list
  - raw-file viewer
  - limits

Each chart's ⓘ button opens its source file, the transformation and the exact table plotted, with a CSV download.
To change the wording, edit `QUESTION` and `PERSONA` near the top of `app.py`.
`.streamlit/config.toml` sets the dark slate theme.

## Folder

```
app.py             the whole app (single page)
presenter_script.md  recording script (≤ 5 min) mapped to the marking checklist
data/              the raw source files, unmodified as downloaded (21–22 Oct 2026)
requirements.txt
```

## Sources (all in `data/`)

| File | Publisher | Original URL |
|---|---|---|
| owid_share-companies-using-artificial-intelligence.csv | McKinsey survey via Stanford AI Index; Our World in Data | ourworldindata.org/grapher/share-companies-using-artificial-intelligence |
| owid_estimated-share-people-generative-ai.csv | Microsoft AI Economy Institute; GDP per person from World Bank/IMF; via Our World in Data | ourworldindata.org/grapher/estimated-share-people-generative-ai |
| owid_monthly-spending-data-center-us.csv | US Census Bureau construction spending via Our World in Data | ourworldindata.org/grapher/monthly-spending-data-center-us |
| owid_data-centers-share-electricity-demand.csv | IEA, Energy and AI, via Our World in Data | ourworldindata.org/grapher/data-centers-share-electricity-demand |
| owid_gdp-per-capita-growth.csv | World Bank WDI (NY.GDP.PCAP.KD.ZG) via Our World in Data | ourworldindata.org/grapher/gdp-per-capita-growth |
| owid_private-investment-in-artificial-intelligence-cset.csv | CSET via Our World in Data (extract: 2022–2025) | ourworldindata.org/grapher/private-investment-in-artificial-intelligence-cset |
| ilo_output_per_hour_countries.csv | ILO modelled estimates, SDMX DF_GDP_2HRW_NOC_NB (extract: countries; 2015, 2019, 2022, 2025) | sdmx.ilo.org |
| fred_COE.csv | BEA via FRED (compensation of employees) | fred.stlouisfed.org/series/COE |
| owid_global-investment-in-generative-ai.csv | Quid via AI Index 2026; Our World in Data | ourworldindata.org/grapher/global-investment-in-generative-ai |
| owid_corporate-investment-in-artificial-intelligence-by-type.csv | Quid via AI Index 2026; Our World in Data | ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type |
| fred_OPHNFB.csv | BLS via FRED | fred.stlouisfed.org/series/OPHNFB |
| fred_ULCNFB.csv | BLS via FRED | fred.stlouisfed.org/series/ULCNFB |
| fred_CP.csv | BEA via FRED | fred.stlouisfed.org/series/CP |
| fred_GDP.csv | BEA via FRED | fred.stlouisfed.org/series/GDP |
| aiindex2026_ch4_extract.csv | Stanford HAI AI Index 2026, Ch. 4 | hai.stanford.edu/assets/files/ai_index_report_2026_chapter_4_economy.pdf (transcribed by hand; figure and page kept per row; verify before quoting; not displayed) |
| eurostat_isoc_eb_ai.csv | Eurostat ICT usage in enterprises | ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai |
| eurostat_isoc_eb_ain2_industry.csv | Eurostat | .../view/isoc_eb_ain2 |
| eurostat_nama_10_lp_ulc.csv | Eurostat national accounts | .../view/nama_10_lp_ulc |
| eurostat_nasa_10_ki_profit_share.csv | Eurostat sector accounts | .../view/nasa_10_ki |
| eurostat_nasa_10_ki_consumption_growth.csv | Eurostat sector accounts | .../view/nasa_10_ki |
| eurostat_isoc_eb_ai_barriers.csv | Eurostat ICT usage in enterprises: reasons for not using AI | .../view/isoc_eb_ai |
| eurostat_isoc_eb_ai_size.csv | Eurostat ICT usage in enterprises: by size class | .../view/isoc_eb_ai |
| eurostat_une_rt_a.csv | Eurostat Labour Force Survey | .../view/une_rt_a |
| eurostat_nama_10_a10_industry.csv | Eurostat national accounts | .../view/nama_10_a10 |
| eurostat_nama_10_a10_e_hours.csv | Eurostat national accounts | .../view/nama_10_a10_e |
| ilo_output_per_hour.csv | ILO modelled estimates (Nov 2025), SDMX DF_GDP_2HRW_NOC_NB | sdmx.ilo.org |
| ilo_labour_income_share.csv | ILO modelled estimates (Nov 2025), SDMX DF_LAP_2GDP_NOC_RT | sdmx.ilo.org |
| fred_PRS85006173.csv | BLS via FRED (labour share) | fred.stlouisfed.org/series/PRS85006173 |
| owid_nvidia-quarterly-revenue-segment.csv | NVIDIA via Our World in Data (2019+) | ourworldindata.org/grapher/nvidia-quarterly-revenue-segment |
| evidence_for_and_against.csv | Hand-compiled; each row lists its URL (kept for reference; not displayed) | see file |

Eurostat files were pulled from the SDMX API (`/eurostat/api/dissemination/sdmx/2.1/data/<dataset>/<key>?format=SDMX-CSV`);
columns that were constant for the query (freq, unit, size class, etc.) were dropped and are listed in the app's source notes.
Every transcribed file was checked against the live source by row count and column sum.

FRED files were downloaded with `fredgraph.csv?id=<SERIES>&cosd=2015-01-01`.

## Traceability

- Every chart's **ⓘ** popover shows its source file(s), the transformation and the exact table plotted. The profits-vs-pay table also shows the raw US$bn values.
- The **Appendix** maps every headline figure to its file and calculation, and lets you open and download each raw file.

## Transformations

- Annualised growth = (end ÷ start)^(4 ÷ quarters) − 1
- Year-on-year = quarter ÷ same quarter a year earlier − 1
- Index = series ÷ value in the gen-AI start quarter × 100 (2022Q4: the first full quarter after ChatGPT launched on 30 Nov 2022)
- Profit share = CP ÷ GDP × 100; reference = mean of 2015Q1–2019Q4
- Productivity growth by region = mean of annual % changes in ILO output per hour, 2015–19 vs 2022–25
- Barriers = % of all firms citing the barrier ÷ % of firms that considered AI but don't use it (E_AI_EC)
- Country quadrant: x = % of firms using AI (2025); y = selected outcome change; lines = medians; Pearson r
