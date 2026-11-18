"""Rebuild every file in data/processed/ from the source samples in data/raw/.

Run from this folder:   python scripts/build_processed.py

Each processed file is its raw file restricted to the analysis window (rows from the first
period listed below onward), with exact duplicate rows dropped and rows sorted by their key
columns. Column names are kept so every figure on screen can be traced back to the raw source.
All further calculations (growth rates, indices, ratios) are done in app.py and shown in each
chart's ⓘ table and in the Appendix. Re-running on unchanged raw files gives identical output.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

PROFIT_FILES = {
    # file: (time column or None, first period kept)
    "owid_share-companies-using-artificial-intelligence.csv": ("Year", 2021),
    "owid_estimated-share-people-generative-ai.csv": (None, None),
    "eurostat_isoc_eb_ai.csv": ("year", 2021),
    "eurostat_isoc_eb_ain2_industry.csv": ("year", 2021),
    "eurostat_isoc_eb_ai_size.csv": ("year", 2021),
    "eurostat_isoc_eb_ai_barriers.csv": ("year", 2023),
    "owid_private-investment-in-artificial-intelligence-cset.csv": ("Year", 2022),
    "owid_global-investment-in-generative-ai.csv": ("Year", 2019),
    "owid_nvidia-quarterly-revenue-segment.csv": (None, None),
    "owid_data-centers-share-electricity-demand.csv": ("Year", 2020),
    "owid_gdp-per-capita-growth.csv": ("Year", 2015),
    "ilo_output_per_hour.csv": ("year", 2015),
    "ilo_output_per_hour_countries.csv": ("year", 2015),
    "ilo_labour_income_share.csv": ("year", 2015),
    "fred_CP.csv": (None, None), "fred_GDP.csv": (None, None), "fred_COE.csv": (None, None),
    "fred_OPHNFB.csv": (None, None), "fred_ULCNFB.csv": (None, None),
    "eurostat_nasa_10_ki_profit_share.csv": ("year", 2019),
    "eurostat_nasa_10_ki_consumption_growth.csv": ("year", 2019),
    "eurostat_nama_10_lp_ulc.csv": ("year", 2019),
    "eurostat_nama_10_a10_industry.csv": ("year", 2019),
    "eurostat_nama_10_a10_e_hours.csv": ("year", 2019),
    "eurostat_une_rt_a.csv": ("year", 2019),
}


def build_profitability():
    """Keep rows from the first period listed in PROFIT_FILES onward, drop exact duplicate rows, sort by all key columns."""
    for name, (tcol, start) in PROFIT_FILES.items():
        d = pd.read_csv(RAW / name).drop_duplicates()
        if tcol:
            d = d[d[tcol] >= start]
        d = d.sort_values(list(d.columns[:-1])).reset_index(drop=True)
        d.to_csv(OUT / name, index=False)
        print(f"{len(d):>6} rows  data/processed/{name}")


if __name__ == "__main__":
    build_profitability()
