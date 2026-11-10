"""The pipeline reproduces numbers printed in the source papers and files."""

import hashlib
import json
import math

import pandas as pd
import pytest

from src.data import BUILDERS, PROCESSED, ROOT, read_processed


@pytest.fixture(scope="module")
def t():
    return {n: read_processed(n) for n in BUILDERS}


def test_ai_share_headlines(t):
    s = t["ai_share"].set_index(["month", "kind"])["share"]
    assert round(s[("2024-06-01", "observed")], 3) == 0.101  # "10.1% two years earlier"
    assert round(s[("2026-06-01", "observed")], 3) == 0.275  # "27.5% of June 2026 tokens"
    assert round(s[("2026-08-01", "observed")], 3) == 0.311  # "31.1% by August"
    assert round(s[("2027-12-01", "forecast")], 3) == 0.423  # "42.3% by the end of 2027"
    assert round(s[("2028-12-01", "forecast")], 3) == 0.507  # "50.7% by the end of 2028"


def test_topic_format_matches_paper_figure_2(t):
    f = t["topic_format"]
    f = f[(f["month"] >= "2026-01-01") & (f["month"] <= "2026-06-01") & f["label"].isin(["AI", "Human"])]
    tokens = f.groupby(["format", "label"])["tokens"].sum().unstack()
    shares = tokens / tokens.sum() * 100
    assert round(shares.loc["Tutorial", "AI"], 1) == 18.5 and round(shares.loc["Tutorial", "Human"], 1) == 6.2
    assert round(shares.loc["Personal Blog", "AI"], 1) == 1.0 and round(shares.loc["Personal Blog", "Human"], 1) == 8.6


def test_figure_3_worked_example(t):
    f = t["fig3_points"].set_index("name")["change_pct"]
    assert round(f["268m-g075-ai-r1"], 3) == -1.031
    assert round(f["268m-g075-human-r1"], 2) == -3.34


def test_cost_curve_headlines(t):
    c = t["cost"]
    c = c[(c["target"] == "c4") & (c["model_size"] == "268M") & (c["scenario"].notna())]
    got = c.set_index("scenario")["cost"].round(2).to_dict()
    assert got == {"2026 crawl": 1.34, "August 2026": 1.58, "end of 2027": 2.12, "end of 2028": 2.98}


def test_definition_five_has_two_families(t):
    d = t["definitions"].set_index("id")
    assert len(d) == 8
    assert d.loc[5, "families"].split(" | ") == ["Distributions deforming", "Decreasing value from additional data"]
    assert bool(d.loc[1, "collapse_accumulate"]) is False and bool(d.loc[1, "collapse_replace"]) is True


def test_web_composition_reproduces_the_released_ai_share(t):
    c = t["web_composition"].set_index(["month", "label"])["token_share"]
    assert round(c[("2026-06-01", "AI")], 3) == 0.275 and round(c[("2026-08-01", "AI")], 3) == 0.311
    assert round(c[("2024-08-01", "Human")], 3) == 0.873 and round(c[("2026-08-01", "Human")], 3) == 0.635


def test_adoption_first_and_last_period(t):
    yes = t["adoption"].query("answer == 'Yes'").sort_values("period_order")
    assert len(yes) == 24
    assert (yes.iloc[0]["period_label"], yes.iloc[0]["share_pct"]) == ("2025-P24", 17.3)
    assert (yes.iloc[-1]["period_label"], yes.iloc[-1]["share_pct"]) == ("2026-P21", 24.6)


def test_genai_use_charts_the_share_not_gdp(t):
    world = t["genai_use"].query("entity == 'World'").sort_values("day")
    assert list(world["share_pct"]) == [15.1, 16.3, 17.8]


def test_evidence_counts(t):
    e = t["evidence"]
    assert (e.query("panel == 'output'")["direction"] == "gain").sum() == 3
    assert sorted(e.query("panel == 'skill'")["direction"]) == ["gain", "loss", "loss"]


def test_entry_level_relative_shortfall_matches_the_paper(t):
    e = t["entry_level"].set_index("id")["change_pct"]
    assert e["C2"] - e["C1"] == 21  # "a divergence of 21 percentage points"
    assert round(100 * (1 - (100 + e["C1"]) / (100 + e["C2"]))) == 19  # "or 19% relative"


def test_processed_files_regenerate_from_the_sources(t):
    for name, build in BUILDERS.items():
        rebuilt = build()
        assert list(rebuilt.columns) == list(t[name].columns) and len(rebuilt) == len(t[name]), name


def test_manifest_hashes_match_the_copied_sources():
    manifest = json.loads((PROCESSED / "MANIFEST.json").read_text())
    assert set(manifest["tables"]) == set(BUILDERS)
    for table in manifest["tables"].values():
        for name, digest in table["inputs"].items():
            assert hashlib.sha256((ROOT / "data" / name).read_bytes()).hexdigest() == digest
