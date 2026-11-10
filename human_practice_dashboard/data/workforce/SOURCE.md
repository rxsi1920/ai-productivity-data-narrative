# Source and licence of the files in this folder

| File | What it is | Source | Licence | Changes |
|---|---|---|---|---|
| `btos_ai.csv` | Share of US firms answering Yes / No / Do not know to the AI-use question (question_id 7), by two-week collection period, 2025-P24 to 2026-P21 | US Census Bureau, Business Trends and Outlook Survey, https://www.census.gov/hfp/btos. Copied unmodified from Karan Makhija's repo `karanmakhijauts/at-3-dvn`, `dashboard/data/raw/btos_ai.csv`, commit `b33f3b2` (26 Oct 2026) | US government work, public domain (not confirmed on the Census page in this build) | none |
| `owid_genai.csv` | Estimated share of working-age adults (15 to 64) who use generative AI, by country, 3 dates | Our World in Data, processing Microsoft AI Diffusion Report data, https://ourworldindata.org/grapher/estimated-share-people-generative-ai. Copied unmodified from the same repo and commit | OWID charts and data are CC BY 4.0; the underlying Microsoft data may carry its own terms (not confirmed in this build) | none |
| `evidence.csv` | Six findings hand-built by Karan Makhija from five papers, each with source URL, location in source, an evidence-strength judgement and a `check_status` | Papers listed in the `source_url` column. Copied unmodified from the same repo and commit | Facts quoted from papers, with citation | none |
| `entry_level_employment.csv` | Four employment changes, November 2022 to June 2026, quoted from Brynjolfsson, Chandar and Chen (August 2026), "Canaries in the Coal Mine? Six Facts about the Recent Employment Effects of Artificial Intelligence" | https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf | Facts quoted from a paper, with citation. The underlying ADP microdata are proprietary and not public | hand-built on 10 Nov 2026 |

SHA-256 of each file is recorded in `data/processed/MANIFEST.json`.

## Checks still to do by a person
- `evidence.csv` rows E3 and E4 (Dell'Acqua et al.) are marked by Karan as read from a summary only.
- `entry_level_employment.csv` was filled from an automated summary of the PDF, not from a person reading it.
  The quoted sentences and page numbers are in `location_in_source`; open the PDF and confirm them.
- The calendar dates of the BTOS collection periods (Karan's reading: 2025-P24 is 17 to 30 Nov 2025 and
  2026-P21 is 5 to 18 Oct 2026) and the exact wording of question 7 were not re-checked against census.gov.
