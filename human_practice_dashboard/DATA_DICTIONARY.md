# Data dictionary

Every number on the page is in, or computed from, a file in `data/processed/`. `python -m src.data` rebuilds all ten
from the source copies and writes the SHA-256 of every input to `data/processed/MANIFEST.json`. Last refresh: 10 Nov 2026.

## Source samples

| File | Source and URL | Licence | Primary key | Time coverage | Latest observation |
|---|---|---|---|---|---|
| `data/workforce/btos_ai.csv` | US Census Bureau, Business Trends and Outlook Survey, https://www.census.gov/hfp/btos (via Karan Makhija's repo, commit `b33f3b2`) | US government work (not re-checked) | `period_code`, `answer_id` | 2025-P24 to 2026-P21, 24 two-week periods | 2026-P21 |
| `data/workforce/owid_genai.csv` | Our World in Data, from Microsoft AI Diffusion Report data, https://ourworldindata.org/grapher/estimated-share-people-generative-ai (same repo and commit) | CC BY 4.0 (OWID; not re-checked) | `Entity`, `Day` | 2025-06-30, 2025-12-31, 2026-03-31 | 2026-03-31 |
| `data/workforce/evidence.csv` | Hand-built by Karan Makhija from five papers; URL per row in `source_url` (same repo and commit) | Cited facts | `id` | Studies published 2023 to 2025 | 2025 |
| `data/workforce/entry_level_employment.csv` | Brynjolfsson, Chandar and Chen (Aug 2026), https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf | Cited facts; ADP microdata are proprietary | `id` | November 2022 to June 2026 | June 2026 |
| `data/wildai/*.csv` (7 files) | Russell et al. (2026), arXiv:2609.40295 v1; https://github.com/pangramlabs/WildAI commit `795a718` | CC BY-NC-SA 4.0 | see processed tables | January 2021 to August 2026 observed; forecast to December 2030 | August 2026 |
| `data/schaeffer/section_a_schaeffer_table.csv` | Written from Schaeffer et al. (2025), arXiv:2503.03150 v2 | Cited facts | row order (definition 1 to 8) | not applicable | 2025 |

## Processed files

| File | Rows | Primary key | Columns (units) | Transform (`src/data.py`) |
|---|---|---|---|---|
| `adoption.csv` | 72 | `period_code`, `answer` | `period_order` (1 to 24), `period_code`, `period_label`, `question_id`, `answer` (Yes / No / Do not know), `share_pct` (% of US firms) | `build_adoption`: rename `value_pct`, add `period_order` by sorting `period_code`, drop `answer_id` and `raw_value` |
| `genai_use.csv` | 444 | `entity`, `day` | `entity`, `code`, `day` (date), `share_pct` (% of people aged 15 to 64), `region` | `build_genai_use`: rename columns, drop GDP per capita |
| `evidence.csv` | 6 | `id` | Karan's 16 columns plus `panel_title`; `sample_size` (people), `direction` (gain / loss), `evidence_strength` (High / Medium / Low, a judgement) | `build_evidence`: add `panel_title` |
| `entry_level.csv` | 4 | `id` | `group`, `age_group`, `exposure_group`, `change_pct` (% change in employment, baseline November 2022), `period_start`, `period_end`, `measure`, `highlight`, `source`, `source_url`, `location_in_source`, `check_status` | `build_entry_level`: copy |
| `web_composition.csv` | 183 | `month`, `label` | `month`, `label` (AI / Human / Mixed), `documents`, `tokens`, `token_share` and `document_share` (fraction of that month's sample), `sampling_source` | `build_web_composition`: sum `monthly_topic_format.csv` by month and label, divide by the month total. Validation checks the AI share equals `monthly_ai_share.csv` |
| `ai_share.csv` | 114 | `month`, `kind` | `kind` (observed / forecast), `share` (fraction of tokens labelled AI), `lo80`, `hi80`, `lo95`, `hi95`, `sampling_source`, `documents`, `tokens`, `ai_tokens` | `build_ai_share`: stack observed and forecast rows |
| `topic_format.csv` | 35,448 | `month`, `topic`, `format`, `label` | `documents`, `tokens` (counts) | `build_topic_format`: month as a date, sort |
| `fig3_points.csv` | 287 | `name` | `group`, `size`, `budget` (human tokens per parameter), `arm` (ai / human), `x` (tokens added per human token), `bpb` and `ctrl_bpb` (bits per byte on C4), `change_pct` (% vs human-only control), `in_figure` | `build_fig3_points`: join `models.csv` and `losses.csv`, compare each run with its group's control |
| `cost.csv` | 462 | `target`, `model_size`, `ai_share` | `n_params`, `human_tpp` (tokens per parameter), `ai_share` (fraction), `scenario`, `cost` (compute multiplier, 1 = human-only; a fitted-law prediction) | `build_cost`: label model size and scenario |
| `definitions.csv` | 8 | `id` | Schaeffer table columns plus `short_name`, `families`, `collapse_accumulate`, `collapse_replace` (paper's Appendix A Table 1), `covered_in`, `coverage_note` (our judgement) | `build_definitions` |

## Known limits of the data
- BTOS: US firms only; one question; the calendar dates of the periods were not re-checked.
- OWID: modelled from one company's usage data; three dates.
- Evidence: single firms or single tasks; strength ratings are judgements.
- Entry-level: descriptive, one payroll provider, values rounded in the paper and entered from an automated summary.
- WildAI: about 5,000 sampled documents a month, labelled by one detector; shares, not volumes; model results are for
  pre-training of models up to 268M parameters; cost and forecast values are predictions.
