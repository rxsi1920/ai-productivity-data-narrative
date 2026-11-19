 # AI: Gains vs Hidden Costs

**Question:** Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?

The question is arguable. Firm and industry data show real gains in output and profit. Other data shows early costs: fewer entry-level jobs, a shrinking share of human-written text for future models to learn from, and weaker moral judgement after talking to a flattering AI. Reasonable readers can weigh the same numbers either way, and the app shows both sides.

## Persona and decision

**Persona:** a company's C-suite (CEO, CFO or COO) at a mid-to-large firm.

**Decision:** whether to invest in adopting AI, and if so, how to roll it out. The choices are:
- where to expect a return first,
- how much entry-level and human work to keep,
- what safeguards to require.

## Our answer

**Not yet proven either way, and the gains are narrower than the hype suggests.**
- **Gains:**
  - AI-intensive industries grew productivity fastest.
  - US corporate profits rose faster than pay.
  - Controlled studies show 12–37% output gains on specific tasks.
  - But economy-wide productivity growth slowed, and countries that use AI most did not grow faster.
- **Costs:** these are early indicators, not proven harms.
  - Early-career employment in AI-exposed jobs fell 11% while less-exposed peers grew 10%.
  - The human-written share of new web text fell from 87% to 64% in two years.
  - Flattering AI made people feel more in the right and less willing to repair a conflict.

The gains are measured; the costs are early signals. A firm adopting AI should therefore expect a narrow return and protect training pathways and human judgement as it scales.

## User stories

**1. Profitability.** "As a C-suite executive deciding on AI investment (i.e., CEO or CFO), I want to see whether AI adoption has raised productivity and profits, so that I can judge the expected return."
- Open **Profitability**. Read the KPI row and the answer box.
- Go to **Evidence**. In the country chart, switch the **scope** (World / Europe) and **outcome** dropdowns. The "X of Y beat the median" count and r update.
- Read **Who captures the gains?**: profits +49% vs employee pay +19%.

**2. Feedback loop and cognition.** As a C-suite executive deciding on AI policy (i.e., COO or CTO), I want to see how AI use is affecting staff training and model training, so that I can decide where to prioritise human skilled input vs. AI-efficient output for business continuity.
- Open **Feedback loop and cognition** and read the answer box.
- In section 1, untick levels in **Evidence strength**. The headline count updates; unticking all shows a message instead of an empty chart.
- In section 3, switch **Measure the share by** between Tokens and Documents. The human-labelled share changes.
- In section 4, pick **Model sizes**, and tick **Compare with adding fresh human text** or **Mark today's web**.
- In Part C, choose **What should the model be good at?** and enter a training budget. The compute multiplier and extra cost update.

**3. Moral degradation.** As a C-suite executive deciding on AI governance (i.e., CEO or CFO), I want to see how AI-related incidents and ethical risks are changing, so that I can price risk and guardrails into the business case.
- Open **Moral degradation**.
- In section 1, change **Forecast from year** to see the incident-report trend.
- In section 3, pick a **Responsible AI dimension** and **country group** to see how many countries have binding rules.
- In section 4, change **Select study** to compare the sycophancy experiments.

Then open **Overall conclusion**, which puts the three parts side by side.

## Run it

```bash
python -m pip install uv
uv sync --all-extras --all-groups
uv run streamlit run app.py
```

Without uv:

```bash
pip install -r requirements.txt   # includes "-e ." so the narrative package is importable
streamlit run app.py
```

**Deployed app:** <ADD STREAMLIT URL> · **Submitted commit:** <ADD TAG OR HASH>

## Rebuild the processed data from raw

```bash
uv run python src/narrative/tabs/profitability/build_processed.py   # profitability (25 files)
uv run python -m narrative.human_practice_data                      # feedback loop (8 files + MANIFEST.json)
uv run python scripts/data.py                                       # moral degradation (downloads only if raw files are missing)
```

## Repository layout

```
app.py                                   entry point (multipage Streamlit app)
src/narrative/main.py                    page navigation
src/narrative/story.py                   group question, shared by every page
src/narrative/tabs/landing/              Home
src/narrative/tabs/profitability/        Profitability page + build_processed.py
src/narrative/tabs/human_practice/       Feedback loop and cognition page
src/narrative/human_practice_data.py     raw → processed for the feedback-loop page
src/narrative/tabs/moral_degradation/    Moral degradation page
src/narrative/tabs/overall_conclusion/   Overall conclusion page
scripts/data.py                          acquire + transform for moral degradation
data/raw/                                source samples as downloaded
data/processed/                          the only files the app reads
data/DATA_DICTIONARY.md                  every dataset: source, URL, licence, columns, key, coverage, transform
PROVENANCE.md                            who made what, with which tool, and how it was checked
DISCLOSURE.md                            data and AI disclosure
```

## Data and limits

All datasets, their licences and transforms are listed in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md). Each page states what its data cannot show. The main limits across the app:
- **No causal claims.** Every comparison is a correlation or a before/after break.
- **Early signals only.** The cost measures are early indicators (employment shifts, text shares, single-conversation experiments), not long-run tests of skill or judgement.
- **Mixed geography.** The geographic coverage differs by dataset.

See [`PROVENANCE.md`](PROVENANCE.md) and [`DISCLOSURE.md`](DISCLOSURE.md) for who did what and how AI tools were used.
