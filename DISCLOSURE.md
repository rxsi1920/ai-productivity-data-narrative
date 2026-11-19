# Data and AI disclosure

## Data

- Every dataset is public or published with a paper. Each one is listed in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) with its source, URL, licence, coverage and transform.
- **Raw files.** `data/raw/` holds the source samples as downloaded. The exceptions are the files the dictionary marks as *extract*, and tables we typed from papers or PDFs, which are marked *cited facts*.
- **Processed files.** `data/processed/` holds the only files the app reads. They are rebuilt from `data/raw/` by:
  - `src/narrative/tabs/profitability/build_processed.py` (profitability),
  - `python -m narrative.human_practice_data` (feedback loop),
  - `scripts/data.py` (moral degradation).
- **Numbers on screen.** Every number in the app is in, or computed from, those processed files. Each chart names its source on screen.
- **Licences.** We use the data for a non-commercial university assignment. Datasets under CC BY-NC-SA 4.0 (WildAI) are used non-commercially and credited. The Ipsos and paper-derived tables reproduce published figures with citation.
- **Privacy.** No personal data is used. The sycophancy study files are the authors' redacted public release, and the survey data is anonymous.

## AI tools

We used Claude (Anthropic) and other AI assistants to:
- find sources and download data,
- draft and debug code,
- extract tables from PDFs,
- draft on-screen text and these documents.

Each use is listed in [`PROVENANCE.md`](PROVENANCE.md), with the member responsible and the check that verified the output.

AI tools did not choose our question, our answer, or what to conclude from the data. Every figure shown was recomputed or checked by a group member, as recorded in the provenance matrix. We take responsibility for the analysis, conclusions and design decisions.
