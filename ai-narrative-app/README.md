# The Rise of Artificial Intelligence: Data Narrative Studio (Team 3)

One Streamlit app, three pages, in story order:

| Page | Story beat | Status |
|---|---|---|
| 1 | Financial profitability | Placeholder (`app_pages/1_financial_profitability.py`) |
| 2 | Feedback-loop degradation and cognitive ability of employees | **Implemented**: the merge of the model-collapse and "Smarter, or slipping?" dashboards |
| 3 | Moral degradation | Placeholder (`app_pages/3_moral_degradation.py`) |

## Run
    pip install -r requirements.txt
    streamlit run app.py          # opens on page 2
    python -m pytest              # 19 tests
    python -m page2.src.data      # rebuild page 2's processed data

## Page 2 layout
- **Part A, cognitive ability of employees:** 1 Today (output gains vs skill signals; Karan's evidence.csv and strength filter),
  2 People (entry-level employment).
- **Part B, feedback-loop degradation:** 3 Knowledge (human share of web text), 4 Models (loss effect, compute cost).
- **5 The decision:** where to lean human vs AI table, *Rollout options for staff* (Karan's "What it means" table, restored
  here with counts computed from the evidence data), limits, sources.

## What the merge did
- Page 2 is the existing merged "human practice" page, moved to `page2/` unchanged except as listed here.
- Karan's `smarter_or_slipping_dashboard` evidence data (`evidence.csv`) was already identical to the copy in the page;
  nothing to reconcile. His Plotly app is not used (page 2 is Altair only).
- Added: the three-option rollout table from his "What it means" tab; Part A/Part B labels; the app shell and navigation.
- **Not carried over from Karan's app:** the OWID/BTOS/PIAAC upload-and-chart panels. They need raw files that were not in the
  zip (`data/raw/` was empty), and BTOS is already shown as a key figure. Say if you want them back.
- Group question and page text live in `story.py`.

## Unchanged caveats (from the page README)
- `entry_level_employment.csv` values came from an automated summary of the Canaries PDF; confirm against the PDF.
- `evidence.csv` rows E3 and E4 (Dell'Acqua et al.) were read from a summary only.
- BTOS collection dates and question wording, and the peer-review status of Russell et al., are unverified.
- WildAI data are CC BY-NC-SA 4.0. See `page2/data/wildai/SOURCE.md` and `page2/DATA_DICTIONARY.md`.
