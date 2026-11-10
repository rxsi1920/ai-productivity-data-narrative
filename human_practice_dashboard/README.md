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

## The story, section by section
| Section | Claim | Chart (Visual Vocabulary family) | Source |
|---|---|---|---|
| Opening | The answer, and four figures that span the datasets | Key figures | all |
| 1. Today | AI use is spreading | Line of US firms using AI (change over time) | Census BTOS; OWID |
| 1. Today | Output rises; first skill warnings | Paired dot panels, one labelled dot per finding (Karan's design) | 5 papers, `evidence.csv` |
| 2. People | Fewer early-career seats in AI-exposed work | Diverging bars around zero (deviation) | Brynjolfsson, Chandar and Chen 2026 |
| 3. Knowledge | Human writing is a falling share of web text | Stacked area (part-to-whole) | WildAI |
| 3. Knowledge | Where the trend points | Line with forecast band (change over time) | WildAI |
| 3. Knowledge | Which human formats are crowded out | Dumbbell, sorted by gap (ranking) | WildAI |
| 4. Models | AI text is a poor substitute for human text | Loss change vs amount added (correlation) | WildAI |
| 4. Models | The compute bill | Curve with labelled scenarios | WildAI (fitted law) |
| 5. Decision | Where to lean human, where to lean AI; what the data cannot show; sources | Tables | all |

Walking the user story: section 2 is "staff training", sections 3 and 4 are "model training", section 5 is the decision.

## Run
    pip install -r requirements.txt
    python -m src.data              # rebuild data/processed/ from the source copies and validate
    streamlit run app.py
    pip install pytest==9.1.1 && python -m pytest     # 19 tests

Tested on 10 Nov 2026 with Python 3.13, Streamlit 1.63.0, pandas 3.0.5, Altair 6.3.0.

## Use inside the group app
    from src.page import render_page
    render_page()          # call from a page of the group's multipage app
`app.py` only sets the page config and calls `render_page()`. Copy `src/`, `data/` and `.streamlit/config.toml`
into the group repo (rename `src` if the group repo already has one). All controls are in the page body, so nothing
is added to the shared sidebar. Karan's original used Plotly; this page uses Altair only.

## Structure
- `src/data.py` builds and validates ten tables. `src/views_people.py` has the workforce charts, the web-composition
  chart and the answer, decision, limits and sources blocks. `src/views.py` has the WildAI charts. `src/page.py` is the page.
- `data/workforce/` and `data/wildai/` hold unmodified source copies (see each `SOURCE.md`), `data/processed/` what the
  app reads, `DATA_DICTIONARY.md` every dataset.

## What changed from the two originals
- Dropped from this page: the AI-phrase-rate chart. Karan's multi-country OWID line chart became a world-versus-one-country
  comparison, and his "What it means" options table became the section 5 decision table. The eight definitions of
  model collapse are kept as a collapsed reference in section 5.
- Karan's adoption chart picked the last numeric column of the OWID file, which is GDP per capita (the recording shows
  "Afghanistan ... went from 1964.5 to 1964.5"). This page reads the share column; a test checks it.
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
  changed during the series. The licence lines for BTOS and OWID in `DATA_DICTIONARY.md` are from general knowledge.
- Peer-review status of Russell et al. (arXiv v1 only was checked, on 2 Nov 2026).
- The Federal Reserve Bank of New York's recent-graduate unemployment series and Stack Overflow question counts would
  both strengthen sections 2 and 3. They could not be downloaded in this build, so they are not used.

## Draft row for the AI provenance matrix
| Artefact | Who | Tool | What was asked | What came back | How it was verified | Outcome |
|---|---|---|---|---|---|---|
| This merged page (code, data pipeline, on-screen text) | Dominique | Claude | Merge the model-collapse dashboard with Karan's dashboard into one narrative for the user story | A Streamlit page, ten processed tables, tests, this README and the data dictionary | `python -m pytest`: 19 tests that would fail if a headline number stopped matching its source (for example 27.5% AI share in June 2026, 17.3% to 24.6% of firms, the 19% shortfall recomputed from -11% and +10%). The Canaries figures still need a human read of the PDF | To be completed by Dominique |

## Licence
WildAI data are CC BY-NC-SA 4.0 (non-commercial, ShareAlike; see `data/wildai/SOURCE.md`). Other sources: `data/workforce/SOURCE.md`.
