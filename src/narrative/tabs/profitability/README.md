# Profitability dashboard: has AI improved company profitability by enhancing productivity?

**Question:** Has AI improved company profitability by enhancing productivity?

This is the measured-gains part of the group question: *Do AI’s measured productivity gains outweigh the hidden costs to how people think, learn, and work?*

**Owner:** Nhi Nguyen · **Last data refresh:** 22 Oct 2026 (also shown on screen)

## Persona and decision

**Persona:** a CEO or CFO of a mid-to-large company.

**Decision:** whether to invest in adopting AI, and where to expect the return to show up first.

## User stories

1. **As a CEO/CFO** deciding on AI investment, **I want to** see how widely AI is used and how much capital is going into it, **so that** I know whether we are early, on pace or behind.
   - *Walk-through:* the KPI row, then the **Adoption** and **Investment** sections. In the first chart, use the **region filter** to compare regions. Clearing every region shows a message instead of a blank chart.
2. **As a CEO/CFO** deciding on AI investment, **I want to** see whether productivity and profits have risen since gen AI arrived, **so that** I can judge the return to expect.
   - *Walk-through:* the **Payoff** section, which shows GDP per person, productivity by region and profit margins, each with 2022 as the baseline.
3. **As a CEO/CFO** deciding on AI investment, **I want to** test whether heavy AI users actually did better, **so that** I target the investment where it pays off.
   - *Walk-through:* the **Evidence** section.
   - In the country chart, switch **scope** (World · 142 countries / Europe · 30 countries) and the **outcome** dropdown. The title, the "X of Y beat the median" count and the correlation update.
   - Then read **Who captures the gains?** and **What does it take?**

## The answer (stated on screen, under the KPI row)

**Only partly, so far.**
- **Where the gain shows:** productivity grew fastest in the EU industries that use AI most (r = +0.73, 6 industries). US corporate profits rose 49% from 2022Q4 to 2026Q2, while employee pay rose 19%.
- **Where it doesn't:** world productivity growth slowed, from 2.4% a year in 2015–19 to 1.9% in 2022–25. Countries that use AI most did not grow faster.
- **Conclusion:** the measured gain is narrow, and it goes more to profits than to pay.

**How the same data could support a different answer:**
- **The J-curve.** Productivity gains usually lag new technology by years, so the lead of AI-intensive industries may be the start of a wider payoff.
- **The profit rise.** It is consistent with AI raising returns, as well as with pricing power after 2022.

## What the data cannot show (also on screen)

- **Causation.** Every comparison is a before/after break or a correlation, and the 2022 energy shock, interest-rate rises and post-COVID rebound happened at the same time.
- **Firm-level AI use outside Europe.** It is measured consistently only in Europe (Eurostat). The world view uses adults’ gen-AI use (Microsoft) as a stand-in.
- **Comparable profit measures.** They differ by region:
  - US: after-tax corporate profits ÷ GDP.
  - EU: gross operating surplus ÷ value added.
  - World: 100 − the ILO labour share.
- **Final figures for the latest periods.** ILO 2025 values are nowcasts, and recent US quarters are revised.

## Run it

From this folder:

```bash
pip install -r requirements.txt          # or: uv sync (streamlit, pandas and plotly are already in the repo’s pyproject.toml)
python scripts/build_processed.py        # rebuilds data/processed/ from data/raw/
streamlit run app.py
```

Run it from inside `profitability_dashboard/` so that `.streamlit/config.toml` (the dark theme) is picked up.

```
app.py                       the dashboard (one page, read top to bottom)
scripts/build_processed.py   raw → processed transforms
data/raw/                    25 source samples, as downloaded (extracts marked in the dictionary)
data/processed/              the only files the app reads
DATA_DICTIONARY.md           source, URL, licence, columns and units, key, coverage, latest obs., transform
.streamlit/config.toml       theme
```

Every chart has an **ⓘ** button showing its source, transform and exact table, with a CSV download. The **Appendix** at the bottom lists every headline figure with its source file and calculation.

## AI provenance (my rows)

| # | Artefact | Who | Tool | What was asked | What came back | How it was verified (a check that could fail) | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | `data/raw/` | Nhi Nguyen | Claude (Anthropic) | Find public sources on AI adoption, investment, productivity and profits, and download them as CSV | 25 source files (OWID, Eurostat, ILO, FRED, CSET) with URLs | Matched each file to the live source by row count and column total; a mismatch would have meant a truncated or altered download | Kept |
| 2 | `app.py` | Nhi Nguyen | Claude | Build the Streamlit charts, with the source table behind each one | Chart code, ⓘ popovers, Appendix | Recomputed headline figures by hand from the raw files, e.g. US profits +49.2% = 4,279.937 ÷ 2,868.270 − 1; a different result would have meant a wrong transform | Kept after fixing a stale-cache error found in testing |
| 3 | `scripts/build_processed.py` | Nhi Nguyen | Claude | Move the raw → processed step into a script | One reproducible script | Deleted `data/processed/`, re-ran the script and compared checksums; any difference would have meant a non-reproducible transform | Kept (checksums identical) |

## Data and AI disclosure

**Data.** All data comes from public, citable sources listed in `DATA_DICTIONARY.md`. Files in `data/raw/` are unmodified as downloaded, except files marked *extract*. Every processed file is rebuilt from `data/raw/` by `scripts/build_processed.py`, and every number on screen is computed from those processed files.

**AI.** I used Claude (Anthropic) to:
- find and download sources,
- draft code and text.

Each use is listed above, with the check I applied. I take responsibility for the analysis, conclusions and design decisions.
