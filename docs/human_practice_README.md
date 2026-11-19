# Is AI weakening the human practice and knowledge that both people and AI learn from?

One page of the Team 3 app for 36104 Assignment 3 (Data Narrative Studio). It merges Dominique Daval Santos's
model-collapse dashboard (`../model_collapse_dashboard`, left untouched) with Karan Makhija's "Smarter, or slipping?"
dashboard (`karanmakhijauts/at-3-dvn`, commit `b33f3b2`).

- **Group question:** Do AI's measured productivity gains outweigh the hidden costs to how people think, learn, and work?
- **This page's question:** Is AI weakening the human practice and knowledge that both people and AI learn from?
- **Persona:** a C-suite executive deciding AI policy, who has to decide where to keep human skilled input and where to
  take AI-efficient output.
- **User story:** As a C-suite executive deciding on AI policy, I want to see how AI use is affecting staff training and
  model training, so that I can decide where to prioritise human skilled input vs. AI-efficient output for business continuity.
- **Out of scope here:** profitability and the moral implications (another teammate's pages).

## The story, section by section (version 2: five charts)
| Section | Claim | Chart (Visual Vocabulary family) | Data files | Whose work |
|---|---|---|---|---|
| Opening | The answer, and four key figures | Key figures | all | merged |
| 1. Today | Output rises; first skill warnings | One dot chart, two labelled groups, one dot per finding | `evidence.csv` (five papers) | Karan's data and design |
| 2. People | Fewer early-career seats in AI-exposed work | Diverging bars around zero (deviation) | `entry_level_employment.csv` (Brynjolfsson, Chandar and Chen 2026) | New in the merge |
| 3. Knowledge | Human writing is a falling share of web text | Stacked area (part-to-whole) | `monthly_topic_format.csv`, `monthly_ai_share.csv`, `ai_share_forecast.csv` (WildAI) | Dominique's data, new chart |
| 4. Models | AI text is a poor substitute for human text | Loss change vs amount added (correlation) | `models.csv`, `losses.csv` (WildAI) | Dominique's |
| 4. Models | The compute bill | Curve with labelled scenarios (change over time) | `cost_of_not_filtering.csv`, `ai_share_forecast.csv` (WildAI) | Dominique's |
| 5. Decision | Where to lean human, where to lean AI; what the data cannot show; sources | Tables | all | merged |

Walking the user story: section 2 is "staff training", sections 3 and 4 are "model training", section 5 is the decision.

### Changed in version 2 (11 Nov 2026)
- Cut from nine charts to five. Removed: the US-firms-using-AI line (its two figures stay in the opening key figures),
  the world-versus-country adoption comparison, the AI-share forecast line (its end-2027 and end-2028 figures are now a
  sentence under the web-composition chart and scenario markers on the compute chart) and the topic/format dumbbell.
- The two evidence panels are one chart with two labelled groups.
- The loss chart opens on one model size (268M) and prints the value at every point. With three or more sizes selected
  only the largest is labelled and the caption says so.
- Removed the files the app no longer reads: `data/workforce/owid_genai.csv`, `data/processed/genai_use.csv`,
  `data/processed/topic_format.csv`.

## Run
    pip install -r requirements.txt
    python -m src.data              # rebuild data/processed/ from the source copies and validate
    streamlit run app.py
    pip install pytest && python -m pytest     # 17 tests

Tested on 11 Nov 2026 with Python 3.13 on two sets of versions: Streamlit 1.63.0 / pandas 3.0.5 / Altair 6.3.0, and
Streamlit 1.67.0 / pandas 3.1.1 / Altair 6.3.0 (the group repo's `pyproject.toml` asks for streamlit>=1.66.1, pandas>=3.1.0).

## Use inside the group app
    from src.page import render_page
    render_page()          # call from a page of the group's multipage app
`app.py` only sets the page config and calls `render_page()`. Copy `src/`, `data/` and `.streamlit/config.toml`
into the group repo (rename `src` if the group repo already has one). All controls are in the page body, so nothing
is added to the shared sidebar. Karan's original used Plotly; this page uses Altair only.

## Structure
- `src/data.py` builds and validates eight tables. `src/views_people.py` has the workforce charts, the web-composition
  chart and the answer, decision, limits and sources blocks. `src/views.py` has the loss and compute charts and the definitions table. `src/page.py` is the page.
- `data/workforce/` and `data/wildai/` hold unmodified source copies (see each `SOURCE.md`), `data/processed/` what the
  app reads, `DATA_DICTIONARY.md` every dataset.

## What changed from the two originals
- Not on this page: Dominique's AI-share forecast line, topic/format dumbbell and AI-phrase-rate chart, and Karan's
  adoption charts and "What it means" options table (replaced by the section 5 decision table). The eight definitions of
  model collapse are kept as a collapsed reference in section 5.
- New data: four employment changes quoted from Brynjolfsson, Chandar and Chen (August 2026), because neither
  original had anything on entry-level work.
- Evidence strength is shown by shape and an ink ramp, direction by ▲/▼ in the label, so the blue = human,
  orange = AI rule holds everywhere else.

## Claims the page deliberately does not make
- It does not say AI caused the fall in early-career employment (the paper is descriptive), or that people are learning
  less (no dataset measures that; it is stated on screen as our inference).
- It does not say people write less. The web series is a share of a fixed-size sample.
- It does not say compute costs have risen. The multipliers are predictions from a fitted law on models up to 268M parameters.

## Not verified (check before submitting)
- `entry_level_employment.csv`: the four values and their page numbers came from an automated summary of the PDF, not
  from a person reading it. Open the PDF and confirm.
- `evidence.csv` rows E3 and E4 (Dell'Acqua et al.): Karan's own `check_status` says summary only.
- BTOS: the calendar dates of the collection periods, the wording of question 7, and whether the question wording
  changed during the series. The licence line for BTOS in `DATA_DICTIONARY.md` is from general knowledge.
- Peer-review status of Russell et al. (arXiv v1 only was checked, on 2 Nov 2026).
- The Federal Reserve Bank of New York's recent-graduate unemployment series and Stack Overflow question counts would
  both strengthen sections 2 and 3. They could not be downloaded in this build, so they are not used.

## Draft row for the AI provenance matrix
| Artefact | Who | Tool | What was asked | What came back | How it was verified | Outcome |
|---|---|---|---|---|---|---|
| This merged page (code, data pipeline, on-screen text) | Dominique | Claude | Merge the model-collapse dashboard with Karan's dashboard into one narrative for the user story | A Streamlit page, eight processed tables, tests, this README and the data dictionary | `python -m pytest`: 17 tests that would fail if a headline number stopped matching its source (for example 27.5% AI share in June 2026, 17.3% to 24.6% of firms, the 19% shortfall recomputed from -11% and +10%). The Canaries figures still need a human read of the PDF | To be completed by Dominique |

## Licence
WildAI data are CC BY-NC-SA 4.0 (non-commercial, ShareAlike; see `data/wildai/SOURCE.md`). Other sources: `data/workforce/SOURCE.md`.
