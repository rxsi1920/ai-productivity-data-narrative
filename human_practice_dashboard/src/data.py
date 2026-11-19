"""Build the page's chart-ready tables from the source samples.

Every number shown on screen comes from a row of ``data/processed/*.csv``.
Every processed row is derived from a verbatim copy of a source file in
``data/wildai/`` (see ``data/wildai/SOURCE.md``), ``data/workforce/`` (see
``data/workforce/SOURCE.md``) or the Schaeffer et al. table in ``data/schaeffer/``.  ``data/processed/MANIFEST.json`` records the
SHA-256 of each input and the row count of each output.

    python -m src.data              # rebuild data/processed/* and validate
    python -m src.data --validate   # validate the existing processed files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WILDAI = ROOT / "data" / "wildai"
SCHAEFFER = ROOT / "data" / "schaeffer"
WORKFORCE = ROOT / "data" / "workforce"
PROCESSED = ROOT / "data" / "processed"

WILDAI_COMMIT = "795a71852d569173fcdaca1db2a466109cd80814"  # origin/main of pangramlabs/WildAI
WORKFORCE_COMMIT = "b33f3b25b7cce24833c857d242c90152c3b41571"  # karanmakhijauts/at-3-dvn, 26 Oct 2026

# Figure 3 of Russell et al. (2026): matched human-token budgets (tokens per parameter),
# drawn model sizes (depths 4-16, i.e. 19.9M-268M) and the matching tolerance.
MATCHED_BUDGETS = (4.72, 18.88, 37.76, 54.72, 72.97, 87.5)
BUDGET_TOLERANCE = 0.015
FITTED_DEPTHS = (4, 6, 9, 12, 16)
SIZE_ORDER = ("19.9m", "35.8m", "86.2m", "135m", "268m")
BUDGET_WORDS = {4.72: 5, 18.88: 20, 37.76: 40, 54.72: 55, 72.97: 73, 87.5: 88}  # the paper's labels

CSV_READ = dict(keep_default_na=False, na_values=[""])

# Schaeffer et al. (2025), Sec. 2: "the definitions can themselves be loosely clustered into three
# families: (i) population risk degrading (Definitions 1, 2 and 3), (ii) distributions deforming from
# their original shape (Definitions 4, 5, 6, 7, and 8), and (iii) decreasing value from additional
# data (Definition 5)."  Definition 5 therefore belongs to two families.
FAMILIES = {
    1: ["Population risk degrading"],
    2: ["Population risk degrading"],
    3: ["Population risk degrading"],
    4: ["Distributions deforming"],
    5: ["Distributions deforming", "Decreasing value from additional data"],
    6: ["Distributions deforming"],
    7: ["Distributions deforming"],
    8: ["Distributions deforming"],
}
# Schaeffer et al. (2025), Appendix A, Table 1 (regression setting): does collapse occur?
# (accumulate, replace)
TABLE1 = {
    1: (False, True),
    2: (True, True),
    3: (False, True),
    4: (False, False),
    5: (True, True),
    6: (False, False),
    7: (False, False),
    8: (False, False),
}
SHORT_NAMES = {
    1: "Catastrophic increase of population risk",
    2: "Any increase of population risk",
    3: "Asymptotically diverging population risk",
    4: "Collapsing variance",
    5: "Change in scaling law",
    6: "Disappearance or entanglement of real data modes",
    7: "Disappearance of real tail data",
    8: "Appearance of hallucinated data",
}
# Wording changes made after checking the table against the paper (see README, "Fact-check edits").
DEF4_CONDITION = (
    "Replace paradigm is unrealistic. Schaeffer et al. cite about 1 quadrillion available "
    "pre-training tokens (attributed to Villalobos et al. 2024). (Sec. 3, 4.1, 4.4)"
)
DEF5_CONDITION = (
    'Not tied to a specific condition. Listed in two families: "distributions deforming" and '
    '"decreasing value from additional data". (Sec. 2)'
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _month_start(period: pd.Series) -> pd.Series:
    return pd.to_datetime(period + "-01", errors="raise").dt.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- builders
def build_ai_share() -> pd.DataFrame:
    """Monthly AI share of web tokens: observed (with 95% interval) and forecast (80%/95% bands)."""
    obs = pd.read_csv(WILDAI / "monthly_ai_share.csv", **CSV_READ)
    fc = pd.read_csv(WILDAI / "ai_share_forecast.csv", **CSV_READ)
    fc = fc[fc["kind"] == "forecast"]
    observed = pd.DataFrame(
        {
            "month": _month_start(obs["month"]),
            "kind": "observed",
            "share": obs["ai_share"],
            "lo80": pd.NA,
            "hi80": pd.NA,
            "lo95": obs["ai_share_lo95"],
            "hi95": obs["ai_share_hi95"],
            "sampling_source": obs["source"],
            "documents": obs["documents"],
            "tokens": obs["tokens"],
            "ai_tokens": obs["ai_tokens"],
        }
    )
    forecast = pd.DataFrame(
        {
            "month": _month_start(fc["month"]),
            "kind": "forecast",
            "share": fc["share"],
            "lo80": fc["lo80"],
            "hi80": fc["hi80"],
            "lo95": fc["lo95"],
            "hi95": fc["hi95"],
            "sampling_source": "random walk with drift",
            "documents": pd.NA,
            "tokens": pd.NA,
            "ai_tokens": pd.NA,
        }
    )
    return pd.concat([observed, forecast], ignore_index=True).sort_values("month").reset_index(drop=True)


def build_web_composition() -> pd.DataFrame:
    """Monthly share of sampled web tokens and documents by Pangram label (Human, Mixed, AI)."""
    frame = pd.read_csv(WILDAI / "monthly_topic_format.csv", **CSV_READ)
    obs = pd.read_csv(WILDAI / "monthly_ai_share.csv", **CSV_READ).set_index("month")
    totals = frame.groupby(["period", "label"], as_index=False)[["documents", "tokens"]].sum()
    month_tokens = totals.groupby("period")["tokens"].transform("sum")
    month_docs = totals.groupby("period")["documents"].transform("sum")
    totals["token_share"] = totals["tokens"] / month_tokens
    totals["document_share"] = totals["documents"] / month_docs
    totals["sampling_source"] = totals["period"].map(obs["source"])
    totals.insert(0, "month", _month_start(totals["period"]))
    return totals.drop(columns="period").sort_values(["month", "label"]).reset_index(drop=True)


def build_adoption() -> pd.DataFrame:
    """Share of US firms giving each answer to the BTOS AI-use question, by two-week collection period."""
    raw = pd.read_csv(WORKFORCE / "btos_ai.csv", **CSV_READ)
    codes = sorted(raw["period_code"].unique())
    out = pd.DataFrame(
        {
            "period_order": raw["period_code"].map({c: i + 1 for i, c in enumerate(codes)}),
            "period_code": raw["period_code"],
            "period_label": raw["period_label"],
            "question_id": raw["question_id"],
            "answer": raw["answer"],
            "share_pct": raw["value_pct"],
        }
    )
    return out.sort_values(["period_order", "answer"]).reset_index(drop=True)


PANEL_TITLES = {"output": "Output gains", "skill": "Skill and learning signals"}


def build_evidence() -> pd.DataFrame:
    """Karan Makhija's six hand-built findings on output and skill, with a display title per panel."""
    raw = pd.read_csv(WORKFORCE / "evidence.csv", **CSV_READ)
    raw.insert(2, "panel_title", raw["panel"].map(PANEL_TITLES))
    return raw


def build_entry_level() -> pd.DataFrame:
    """Employment change by age and AI exposure, Nov 2022 to Jun 2026 (Brynjolfsson, Chandar and Chen 2026)."""
    return pd.read_csv(WORKFORCE / "entry_level_employment.csv", **CSV_READ)


def _snap_budget(tpp: float) -> float | None:
    return next((b for b in MATCHED_BUDGETS if abs(tpp - b) <= BUDGET_TOLERANCE * b), None)


def build_fig3_points() -> pd.DataFrame:
    """Points of Figure 3 (Russell et al. 2026): change in C4 loss vs each run's human-only control."""
    models = pd.read_csv(WILDAI / "models.csv", **CSV_READ)
    losses = pd.read_csv(WILDAI / "losses.csv", **CSV_READ)
    loss = losses[losses["target"] == "c4"].set_index("name")["bpb"]
    models["bpb"] = models["name"].map(loss)
    models["tpp"] = models["human_tokens"] / models["n_params"]
    control = models[models["arm"] == "control"].set_index("group")
    runs = models[models["arm"].isin(["ai", "human"])].copy()
    for col in ("tpp", "depth", "bpb", "human_tokens"):
        runs["ctrl_" + col] = runs["group"].map(control[col])
    runs["budget"] = runs["ctrl_tpp"].map(_snap_budget)
    runs = runs[runs["budget"].notna() & runs["ctrl_depth"].isin(FITTED_DEPTHS)].copy()
    runs["x"] = runs.apply(
        lambda r: r.ai_tokens / r.human_tokens if r.arm == "ai" else r.human_tokens / r.ctrl_human_tokens - 1,
        axis=1,
    )
    runs["change_pct"] = 100 * (runs["bpb"] / runs["ctrl_bpb"] - 1)
    # AI ladders: for each size and budget use the one group with the most AI runs (ties: lowest id);
    # fresh-human points use every group.  This follows the description of the authors' figure code.
    ai = runs[runs["arm"] == "ai"]
    counts = ai.groupby(["size", "budget", "group"]).size().reset_index(name="n")
    best = counts.sort_values(["size", "budget", "n", "group"], ascending=[True, True, False, True]).drop_duplicates(
        ["size", "budget"]
    )
    chosen = set(zip(best["size"], best["budget"], best["group"]))
    runs["in_figure"] = runs.apply(
        lambda r: r.arm == "human" or (r["size"], r.budget, r.group) in chosen, axis=1
    )
    runs["size_order"] = runs["size"].map({s: i for i, s in enumerate(SIZE_ORDER)})
    out = runs[["name", "group", "size", "size_order", "budget", "arm", "x", "bpb", "ctrl_bpb", "change_pct", "in_figure"]]
    return out.sort_values(["budget", "size_order", "arm", "x", "name"]).reset_index(drop=True)


def build_cost() -> pd.DataFrame:
    """Compute multiplier needed by unfiltered web text to match its human-only subset (law output)."""
    frame = pd.read_csv(WILDAI / "cost_of_not_filtering.csv", **CSV_READ)
    frame["model_size"] = frame["n_params"].map(lambda n: "268M" if n < 1e9 else "8B")
    frame["scenario"] = frame["label"].fillna("")
    return (
        frame[["target", "model_size", "n_params", "human_tpp", "ai_share", "scenario", "cost"]]
        .sort_values(["target", "model_size", "ai_share"])
        .reset_index(drop=True)
    )


# Which charts on the page bear on which definition. This mapping is my own judgement, not from either paper.
# (label shown in the table, one-sentence reason shown in the detail panel)
COVERAGE = {
    1: ("Not covered", "No chart tests catastrophic degradation. The loss chart shows changes of a few per cent when AI text is mixed into human data, which is not recursive training."),
    2: ("Loss chart (partly)", "The loss chart compares loss with added AI text against a human-only control, so a rise is an increase in risk by this definition. Loss is measured on C4 as a proxy for the real distribution, and with mixing, not recursion."),
    3: ("Not covered", "This needs successive generations of models; the WildAI models are single-generation mixes of human and AI text."),
    4: ("Not covered", "No chart measures variance or diversity."),
    5: ("Loss and compute charts", "Both are about the scaling law: what added AI text does to loss at a fixed human-token budget, and the compute multiplier that follows."),
    6: ("Not covered", "No chart shows a model losing or merging modes. The web-composition chart describes what the web contains, not what a model has lost."),
    7: ("Not covered", "No chart measures how a model handles rare cases."),
    8: ("Not covered", "No chart checks whether model output is supported by the real data."),
}
CONTEXT_NOTE = "The web-composition chart is context for every definition: it shows how much AI text is already in web data."


def build_definitions() -> pd.DataFrame:
    """The eight definitions of model collapse (Schaeffer et al. 2025) with their families."""
    raw = pd.read_csv(SCHAEFFER / "section_a_schaeffer_table.csv", **CSV_READ)
    raw.columns = ["definition", "details", "realistic_condition", "mitigation", "rebuttal", "papers"]
    raw.insert(0, "id", range(1, len(raw) + 1))
    if len(raw) != 8:
        raise ValueError("Expected eight definitions")
    raw["short_name"] = raw["id"].map(SHORT_NAMES)
    raw["families"] = raw["id"].map(lambda i: " | ".join(FAMILIES[i]))
    raw["collapse_accumulate"] = raw["id"].map(lambda i: TABLE1[i][0])
    raw["collapse_replace"] = raw["id"].map(lambda i: TABLE1[i][1])
    raw["covered_in"] = raw["id"].map(lambda i: COVERAGE[i][0])
    raw["coverage_note"] = raw["id"].map(lambda i: COVERAGE[i][1])
    raw.loc[raw["id"] == 4, "realistic_condition"] = DEF4_CONDITION
    raw.loc[raw["id"] == 5, "realistic_condition"] = DEF5_CONDITION
    return raw


# --------------------------------------------------------------------------- validation
def validate(tables: dict[str, pd.DataFrame]) -> None:
    share = tables["ai_share"]
    if share.duplicated(["month", "kind"]).any():
        raise ValueError("ai_share: duplicate month/kind")
    for col in ("share", "lo95", "hi95"):
        if not share[col].astype(float).between(0, 1).all():
            raise ValueError(f"ai_share: {col} outside [0, 1]")
    if not ((share["lo95"].astype(float) <= share["share"] + 1e-9) & (share["share"] <= share["hi95"].astype(float) + 1e-9)).all():
        raise ValueError("ai_share: share outside its 95% interval")
    observed = share[share["kind"] == "observed"]
    forecast = share[share["kind"] == "forecast"]
    if observed["month"].max() >= forecast["month"].min():
        raise ValueError("ai_share: forecast must start after the last observation")

    fig3 = tables["fig3_points"]
    if fig3["x"].le(0).any() or fig3["change_pct"].isna().any():
        raise ValueError("fig3_points: non-positive x or missing loss")
    worked = fig3[fig3["name"] == "268m-g075-ai-r1"]
    if len(worked) != 1 or abs(float(worked["change_pct"].iloc[0]) - (-1.031081)) > 1e-3:
        raise ValueError("fig3_points: worked example 268m-g075-ai-r1 does not reproduce (-1.03%)")

    cost = tables["cost"]
    finite = cost[cost["cost"].map(math.isfinite)]
    if not (finite.loc[finite["ai_share"] == 0, "cost"].round(6) == 1.0).all():
        raise ValueError("cost: the multiplier at 0% AI share must be 1")

    definitions = tables["definitions"]
    if sorted(definitions["id"]) != list(range(1, 9)):
        raise ValueError("definitions: expected ids 1-8")

    comp = tables["web_composition"]
    if not set(comp["label"]) <= {"AI", "Human", "Mixed"} or comp.duplicated(["month", "label"]).any():
        raise ValueError("web_composition: unexpected label or duplicate month/label")
    if (comp.groupby("month")["token_share"].sum() - 1).abs().max() > 1e-9:
        raise ValueError("web_composition: token shares must sum to 1 in every month")
    ai = comp[comp["label"] == "AI"].set_index("month")["token_share"]
    ref = observed.set_index("month")["share"].astype(float)
    if (ai.reindex(ref.index).fillna(0) - ref).abs().max() > 1e-9:
        raise ValueError("web_composition: AI token share does not reproduce monthly_ai_share.csv")

    adoption = tables["adoption"]
    if adoption.duplicated(["period_code", "answer"]).any() or not adoption["share_pct"].between(0, 100).all():
        raise ValueError("adoption: duplicate period/answer or share outside 0-100")
    if (adoption.groupby("period_code")["share_pct"].sum() - 100).abs().max() > 0.5:
        raise ValueError("adoption: answers should sum to about 100% in every period")

    evidence = tables["evidence"]
    if evidence["id"].duplicated().any() or not set(evidence["panel"]) <= {"output", "skill"}:
        raise ValueError("evidence: duplicate id or unknown panel")
    if not set(evidence["direction"]) <= {"gain", "loss"} or not set(evidence["evidence_strength"]) <= {"High", "Medium", "Low"}:
        raise ValueError("evidence: unknown direction or evidence strength")
    if evidence[["source_url", "location_in_source", "check_status"]].isna().any().any():
        raise ValueError("evidence: every finding needs a source, a location and a check status")

    entry = tables["entry_level"]
    if entry["id"].duplicated().any() or entry[["change_pct", "source_url", "location_in_source"]].isna().any().any():
        raise ValueError("entry_level: duplicate id or missing value/source")


# --------------------------------------------------------------------------- IO
BUILDERS = {
    "adoption": build_adoption,
    "evidence": build_evidence,
    "entry_level": build_entry_level,
    "web_composition": build_web_composition,
    "ai_share": build_ai_share,
    "fig3_points": build_fig3_points,
    "cost": build_cost,
    "definitions": build_definitions,
}
INPUTS = {
    "adoption": [WORKFORCE / "btos_ai.csv"],
    "evidence": [WORKFORCE / "evidence.csv"],
    "entry_level": [WORKFORCE / "entry_level_employment.csv"],
    "web_composition": [WILDAI / "monthly_topic_format.csv", WILDAI / "monthly_ai_share.csv"],
    "ai_share": [WILDAI / "monthly_ai_share.csv", WILDAI / "ai_share_forecast.csv"],
    "fig3_points": [WILDAI / "models.csv", WILDAI / "losses.csv"],
    "cost": [WILDAI / "cost_of_not_filtering.csv"],
    "definitions": [SCHAEFFER / "section_a_schaeffer_table.csv"],
}


def write_tables(tables: dict[str, pd.DataFrame]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    manifest = {
        "wildai_commit": WILDAI_COMMIT,
        "workforce_commit": WORKFORCE_COMMIT,
        "licence": "WildAI results: CC BY-NC-SA 4.0. Other files: see data/workforce/SOURCE.md",
        "tables": {},
    }
    for name, frame in tables.items():
        frame.to_csv(PROCESSED / f"{name}.csv", index=False)
        manifest["tables"][name] = {
            "rows": int(len(frame)),
            "inputs": {str(p.relative_to(ROOT / "data")): _sha256(p) for p in INPUTS[name]},
        }
    (PROCESSED / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def read_processed(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED / f"{name}.csv", **CSV_READ)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--validate", action="store_true", help="validate data/processed/* and stop")
    args = parser.parse_args()
    if args.validate:
        tables = {name: read_processed(name) for name in BUILDERS}
        validate(tables)
        print("Processed data valid")
        return
    tables = {name: builder() for name, builder in BUILDERS.items()}
    validate(tables)
    write_tables(tables)
    for name, frame in tables.items():
        print(f"{name}: {len(frame)} rows")
    print(f"Validated and wrote {len(tables)} tables to {PROCESSED}")


if __name__ == "__main__":
    sys.exit(main())
