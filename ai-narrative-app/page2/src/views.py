"""Renderers for the web-data and model-training charts (WildAI and Schaeffer et al.).  Each view sits in a
keyed container and carries its own title, unit, source, latest-observation caption, controls, outputs and a
CSV download.  The workforce charts are in ``views_people.py``."""

from __future__ import annotations

import math

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from .charts import AI, HUMAN, INK, INK2, NEUTRAL, style
from .data import CONTEXT_NOTE, WILDAI_COMMIT

KPI_HEIGHT = 150  # pixels; one height so every key-figure box matches
EMPTY = "No observations match the selected filters."
WILDAI_REPO = "https://github.com/pangramlabs/WildAI"
WILDAI_CITE = (
    "Russell et al. (2026), *How Much Is an AI Token Worth? Scaling Laws for Wild AI-Generated Web Text*, "
    f"Pangram Labs / University of Maryland, arXiv:2609.40295 v1; data: [WildAI]({WILDAI_REPO}) "
    f"(commit `{WILDAI_COMMIT[:7]}`, CC BY-NC-SA 4.0)."
)
SCHAEFFER_CITE = (
    "Schaeffer, Kazdan, Arulandu and Koyejo (2025), *Position: Model Collapse Does Not Mean What You Think*, "
    "arXiv:2503.03150 v2."
)


# ----------------------------------------------------------------------------- helpers
def _pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def _csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _footer(frame: pd.DataFrame, label: str, file_name: str, key: str, source: str, note: str | None = None) -> None:
    with st.expander("Show the data table"):
        st.dataframe(frame, hide_index=True, width="stretch")
    st.caption(f"Source: {source}")
    if note:
        st.caption(note)
    st.download_button(label, data=_csv(frame), file_name=file_name, mime="text/csv", key=key)


def _heading(title: str, question: str) -> None:
    st.subheader(title)
    st.markdown(f"**Question:** {question}")


# ----------------------------------------------------------------------------- 0. definitions
def render_definitions(defs: pd.DataFrame) -> None:
    with st.container(key="risk_definitions"):
        _heading(
            'Reference: what "model collapse" means',
            'Schaeffer et al. find eight different meanings of "model collapse". Do they all describe a threat?',
        )
        st.caption("Unit: definitions (n = 8). Latest observation: not applicable (a literature review of 28 papers).")
        st.caption(
            "**Two conditions decide whether a definition counts as collapse** (the two yes/no columns in the table). "
            "**Data replacement:** each generation of model is trained only on the previous model's synthetic output, "
            "and the earlier data is discarded. "
            "**Data accumulation:** each generation's synthetic data is added to the real and earlier data, which is kept. "
            "The columns say whether each definition predicts collapse under each condition, in the paper's regression "
            "example (paraphrased from Schaeffer et al.; see the note under the table). "
            "**Charted in** shows which charts on this page bear on each definition. That mapping is our own judgement, "
            f"not from the paper; the detail panel gives the reason. {CONTEXT_NOTE}"
        )
        families = [
            "Population risk degrading",
            "Distributions deforming",
            "Decreasing value from additional data",
        ]
        chosen = st.multiselect("Filter by family", families, default=families, key="family_filter")
        mask = defs["families"].map(lambda value: any(f in value.split(" | ") for f in chosen))
        shown = defs[mask]
        if shown.empty:
            st.info(EMPTY)
        else:
            compact = pd.DataFrame(
                {
                    "#": shown["id"],
                    "Definition": shown["short_name"],
                    "Family": shown["families"].str.replace(" | ", "; ", regex=False),
                    "Collapse: accumulate?": shown["collapse_accumulate"].map({True: "yes", False: "no"}),
                    "Collapse: replace?": shown["collapse_replace"].map({True: "yes", False: "no"}),
                    "Charted in": shown["covered_in"],
                }
            )
            event = st.dataframe(
                compact,
                hide_index=True,
                width="stretch",
                column_config={
                    "#": st.column_config.NumberColumn("#", width=40),
                    "Definition": st.column_config.TextColumn("Definition", width=320),
                    "Family": st.column_config.TextColumn("Family", width=340),
                    "Collapse: accumulate?": st.column_config.TextColumn("Collapse: accumulate?", width=140),
                    "Collapse: replace?": st.column_config.TextColumn("Collapse: replace?", width=120),
                    "Charted in": st.column_config.TextColumn("Charted in", width=130),
                },
                on_select="rerun",
                selection_mode="single-row",
                key="definitions_table",
            )
            picked = event.selection.rows
            row = shown.iloc[picked[0]] if picked else shown.iloc[0]
            st.markdown(f"##### Definition {row['id']}: {row['short_name']}")
            if not picked:
                st.caption("Select a row above to read about another definition.")
            st.markdown(row["details"])
            st.markdown(f"**In this dashboard ({row['covered_in']}):** {row['coverage_note']}")
            left, right = st.columns(2)
            with left:
                st.markdown("**Realistic conditions and practice trends**")
                st.markdown(row["realistic_condition"])
                st.markdown("**Rebuttal of the concern**")
                st.markdown(row["rebuttal"])
            with right:
                st.markdown("**Key consideration or mitigation**")
                st.markdown(row["mitigation"])
                st.markdown("**Papers using this definition**")
                st.markdown(row["papers"])
        _footer(
            defs.drop(columns=["short_name"]),
            "Download definitions",
            "model_collapse_definitions.csv",
            "definitions_download",
            SCHAEFFER_CITE,
            "The yes/no columns are the paper's regression example (Appendix A, Table 1), not a general result. "
            'Definition 5 sits in two of the paper\'s families, so it appears under both filters. "Realistic '
            'conditions" and the Section 5 forecast are the authors\' judgement in a position paper.',
        )


# ----------------------------------------------------------------------------- 4. Figure 3
LABEL_ALL_UP_TO = 2  # print a value at every point while this many model sizes or fewer are selected
BUDGET_NAMES = {4.72: "about 5", 18.88: "about 20", 37.76: "about 40", 54.72: "about 55", 72.97: "about 73", 87.5: "about 88"}


def render_loss_effect(data: pd.DataFrame, today_share: float, today_month: pd.Timestamp) -> None:
    data = data[data["in_figure"]].copy()
    sizes = {"19.9m": "19.9M", "35.8m": "35.8M", "86.2m": "86.2M", "135m": "135M", "268m": "268M"}
    r_today = today_share / (1 - today_share)
    with st.container(key="loss_effect"):
        _heading(
            "What AI text does to a model that learns from it",
            "For a model with a fixed human-token budget, what happens to its loss on human text when AI text, or fresh "
            "human text, is added?",
        )
        st.caption("Unit: percent change in loss (bits per byte on C4) against the same model trained on human text only. Latest observation: not applicable (a fixed set of released models).")
        c1, c2 = st.columns([3, 2])
        budget = c1.select_slider(
            "Human tokens per parameter (training budget)",
            options=list(BUDGET_NAMES),
            value=18.88,
            format_func=lambda b: f"{BUDGET_NAMES[b]} ({b})",
            key="fig3_budget",
        )
        chosen = c2.multiselect("Model sizes", list(sizes.values()), default=["268M"], key="fig3_sizes")
        d1, d2 = st.columns(2)
        show_human = d1.checkbox("Compare with adding fresh human text", value=True, key="fig3_show_human")
        mark_today = d2.checkbox(
            f"Mark today's web ({_pct(today_share)} AI in {today_month:%b %Y})", value=True, key="fig3_mark_today"
        )
        keep = [k for k, v in sizes.items() if v in chosen]
        frame = data[(data["budget"] == budget) & (data["size"].isin(keep))]
        if not show_human:
            frame = frame[frame["arm"] == "ai"]
        if frame.empty:
            st.info(EMPTY)
        else:
            frame = frame.assign(
                size_label=frame["size"].map(sizes),
                arm_label=frame["arm"].map({"ai": "AI text added", "human": "Fresh human text added"}),
            )
            size_order = [sizes[k] for k in sizes if k in set(frame["size"])]
            x = alt.X(
                "x:Q",
                scale=alt.Scale(type="log", domain=[0.002, 100]),
                title="Tokens added per human token (log scale)",
                axis=alt.Axis(values=[0.01, 0.1, 1, 10, 100], labelExpr="datum.value + '×'", grid=False),
            )
            y = alt.Y("change_pct:Q", title="Change in loss vs human-only control (%)")
            colour = alt.Color(
                "arm_label:N",
                scale=alt.Scale(domain=["AI text added", "Fresh human text added"], range=[AI, HUMAN]),
                legend=alt.Legend(title="Added to a fixed human corpus"),
            )
            sized = alt.Size("size_label:O", sort=size_order, scale=alt.Scale(range=[30, 170]), legend=alt.Legend(title="Model size"))
            tooltip = [
                alt.Tooltip("name:N", title="Run"),
                alt.Tooltip("arm_label:N", title="Added"),
                alt.Tooltip("x:Q", format=".3f", title="Tokens added per human token"),
                alt.Tooltip("change_pct:Q", format="+.2f", title="Change in loss (%)"),
                alt.Tooltip("bpb:Q", format=".4f", title="Run loss (bpb)"),
                alt.Tooltip("ctrl_bpb:Q", format=".4f", title="Control loss (bpb)"),
            ]
            zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=INK2, strokeWidth=1).encode(y="y:Q")
            lines = alt.Chart(frame).mark_line(strokeWidth=1.5, opacity=0.8).encode(x=x, y=y, color=colour, detail=alt.Detail(["size_label:N", "arm_label:N"]))
            points = alt.Chart(frame).mark_point(filled=True, opacity=0.95, stroke="white", strokeWidth=0.8).encode(x=x, y=y, color=colour, size=sized, tooltip=tooltip)
            layers = [zero, lines, points]
            # Print the value at every point.  With three or more sizes the labels would collide, so only the
            # largest selected size is labelled and the caption says so.
            labelled = frame if len(size_order) <= LABEL_ALL_UP_TO else frame[frame["size_label"] == size_order[-1]]
            labelled = labelled.assign(text=labelled["change_pct"].map(lambda v: f"{v:+.2f}%"))
            # AI labels sit above the point, moving to the upper left where the curve climbs; human labels sit below.
            steep = (labelled["arm"] == "ai") & (labelled["x"] >= 0.3)
            for part, props in (
                (labelled[(labelled["arm"] == "ai") & ~steep], dict(dy=-15)),
                (labelled[steep], dict(align="right", dx=-9, dy=-7)),
                (labelled[labelled["arm"] == "human"], dict(dy=16)),
            ):
                layers.append(alt.Chart(part).mark_text(fontSize=11, **props).encode(x=x, y=y, text="text:N", color=alt.Color("arm_label:N", legend=None)))
            if mark_today:
                today = pd.DataFrame({"x": [r_today], "text": [f"today's web ≈ {_pct(today_share, 0)} AI, r ≈ {r_today:.2f}"]})
                layers.append(alt.Chart(today).mark_rule(color=NEUTRAL, strokeDash=[4, 3]).encode(x="x:Q"))
                layers.append(
                    alt.Chart(today).mark_text(color=INK2, align="left", dx=5, baseline="top", fontSize=11).encode(x="x:Q", y=alt.value(6), text="text:N")
                )
            st.altair_chart(style(alt.layer(*layers), height=420), theme=None, width="stretch")
            ai = frame[frame["arm"] == "ai"]
            hu = frame[frame["arm"] == "human"]
            m1, m2, m3 = st.columns(3)
            if not ai.empty:
                best, worst = ai.loc[ai["change_pct"].idxmin()], ai.loc[ai["change_pct"].idxmax()]
                m1.metric("Best result with AI text", f"{best['change_pct']:+.2f}%", delta=f"run {best['name']}", delta_color="off", delta_arrow="off", border=True)
                m2.metric("Worst result with AI text", f"{worst['change_pct']:+.2f}%", delta=f"run {worst['name']}", delta_color="off", delta_arrow="off", border=True)
            if not hu.empty:
                hb = hu.loc[hu["change_pct"].idxmin()]
                m3.metric("Best result with fresh human text", f"{hb['change_pct']:+.2f}%", delta=f"run {hb['name']}", delta_color="off", delta_arrow="off", border=True)
        n_sizes = len(keep)
        printed = (
            "The value is printed at every point (AI text above the point, fresh human text below)."
            if n_sizes <= LABEL_ALL_UP_TO
            else f"With {n_sizes} sizes selected only the largest is labelled, to keep the labels legible; every value is in the data table below."
        )
        st.caption(
            f"Below zero means the model predicts human text better than its human-only twin. {printed} Each added-text amount is a "
            "separate trained model. The x position is the realised ratio of added tokens to human tokens. An AI share s of all "
            "training tokens corresponds to r = s / (1 − s), which is how the marker for today's web is placed. These are "
            "constructed mixtures of AI and human documents, not recursive training, so this does not test model collapse "
            "in the recursive sense. Only the 19.9M to 268M models are drawn, as in Figure 3 of the paper; the 477M and 973M "
            "models were held out to test the authors' scaling law."
        )
        _footer(
            frame.drop(columns=["size_label", "arm_label"], errors="ignore") if not frame.empty else data.head(0),
            "Download filtered runs",
            "loss_effect_runs.csv",
            "loss_download",
            f"{WILDAI_CITE} Files `models.csv`, `losses.csv` (evaluation set C4).",
            "Reproduction of Figure 3, rebuilt from the released CSVs with the logic described for the authors' figure code. "
            "For each size and budget the AI ladder is the group with the most AI runs; fresh-human points use every group.",
        )


# ----------------------------------------------------------------------------- 5. cost
TARGETS = {
    "Human-written web text (C4)": "c4",
    "Mixed 2026 web text (22.3% AI)": "fw26",
    "AI-written text (Cosmopedia)": "cosmopedia",
}
SCENARIOS = [("2026 crawl", None), ("August 2026", None), ("end of 2027", "2027-12-01"), ("end of 2028", "2028-12-01")]


def render_cost(cost: pd.DataFrame, ai_share: pd.DataFrame) -> None:
    ai_share = ai_share.copy()
    ai_share["month"] = pd.to_datetime(ai_share["month"])
    forecast = ai_share[ai_share["kind"] == "forecast"].set_index("month")
    with st.container(key="compute_cost"):
        _heading(
            "The bill: extra compute when web text is not filtered",
            "How much extra compute does a model trained on unfiltered web text need to match one trained on its human-written "
            "subset, as the AI share rises?",
        )
        st.caption("Unit: compute multiplier (1× = same compute as training on the human subset). Output of the authors' fitted scaling law, not a measurement. Latest observation: not applicable.")
        c1, c2 = st.columns([3, 2])
        label = c1.radio("What should the model be good at?", list(TARGETS), horizontal=True, key="cost_target")
        budget = c2.number_input(
            "Illustrative: your training budget with filtered data ($)", min_value=0, value=1_000_000, step=100_000, key="cost_budget",
            help="An input for illustration only. It is not data from the paper.",
        )
        target = TARGETS[label]
        curve_all = cost[(cost["target"] == target) & (cost["model_size"] == "268M")].sort_values("ai_share")
        finite = curve_all[np.isfinite(curve_all["cost"])]
        if curve_all.empty:
            st.info(EMPTY)
        else:
            scen = curve_all[curve_all["scenario"].notna() & (curve_all["scenario"] != "")].copy()
            scen["scenario"] = pd.Categorical(scen["scenario"], [s for s, _ in SCENARIOS], ordered=True)
            scen = scen.sort_values("scenario")
            lows, highs = [], []
            for name, month in SCENARIOS:
                if month is None:
                    lows.append(np.nan); highs.append(np.nan)
                else:
                    lows.append(float(forecast.loc[pd.Timestamp(month), "lo80"])); highs.append(float(forecast.loc[pd.Timestamp(month), "hi80"]))
            scen["lo80"], scen["hi80"] = lows, highs
            xs, ys = finite["ai_share"].to_numpy(), finite["cost"].to_numpy()
            max_finite = float(xs.max())

            def interp(share: float) -> float:
                if np.isnan(share):
                    return float("nan")
                return float(np.interp(share, xs, ys)) if share <= max_finite else float("inf")

            scen["cost_lo"] = scen["lo80"].map(interp)
            scen["cost_hi"] = scen["hi80"].map(interp)
            scen["budget"] = scen["cost"] * budget

            m = st.columns(3)
            for col, (name, _) in zip(m, SCENARIOS[1:]):
                row = scen[scen["scenario"] == name].iloc[0]
                col.metric(
                    f"{name.capitalize() if name != 'August 2026' else name} ({_pct(row['ai_share'])} AI)",
                    f"{row['cost']:.2f}×",
                    delta=f"${row['budget']:,.0f} on your budget",
                    delta_color="off",
                    delta_arrow="off",
                    border=True,
                )
            x_enc = alt.X("ai_share:Q", title="AI share of the web text used for training", axis=alt.Axis(format="%", grid=False, values=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]), scale=alt.Scale(domain=[0, 0.6]))
            lo_dom = min(0.8, float(finite["cost"].min()) / 1.3)
            hi_dom = max(2.0, min(8.0, float(finite["cost"].max()) * 1.3))
            ticks = [t for t in (0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8) if lo_dom <= t <= hi_dom]
            y_enc = alt.Y("cost:Q", title="Compute multiplier (log scale)", scale=alt.Scale(type="log", domain=[lo_dom, hi_dom], nice=False, clamp=True), axis=alt.Axis(values=ticks, labelExpr="datum.value + '×'"))
            one = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(color=INK2, strokeWidth=1).encode(y="y:Q")
            one_label = alt.Chart(pd.DataFrame({"y": [1.0], "t": ["1× = same compute as human-only"]})).mark_text(color=INK2, align="left", dx=4, dy=12, fontSize=11).encode(x=alt.value(4), y="y:Q", text="t:N")
            line = alt.Chart(finite).mark_line(color=AI, strokeWidth=2.5).encode(x=x_enc, y=y_enc)
            layers = [one, one_label, line]
            if len(finite) < len(curve_all):
                inf_start = float(curve_all[~np.isfinite(curve_all["cost"])]["ai_share"].min())
                gap = pd.DataFrame({"a": [inf_start], "b": [0.6], "t": ["no finite compute matches"]})
                layers.append(alt.Chart(gap).mark_rect(color=AI, opacity=0.12).encode(x="a:Q", x2="b:Q"))
                layers.append(alt.Chart(gap).mark_text(color=INK2, align="right", dx=12, baseline="top", fontSize=11, angle=270).encode(x="a:Q", y=alt.value(6), text="t:N"))
            band_rows = scen.dropna(subset=["lo80"]).copy()
            band_rows["hi_plot"] = band_rows["hi80"].clip(upper=0.6)
            layers.append(alt.Chart(band_rows).mark_rule(color=NEUTRAL, strokeWidth=2, opacity=0.7).encode(x="lo80:Q", x2="hi_plot:Q", y=y_enc))
            tip = [
                alt.Tooltip("scenario:N", title="Scenario"),
                alt.Tooltip("ai_share:Q", format=".1%", title="AI share"),
                alt.Tooltip("cost:Q", format=".2f", title="Compute multiplier"),
            ]
            layers.append(alt.Chart(scen).mark_point(filled=True, color=AI, size=110, stroke="white", strokeWidth=1.2, opacity=1).encode(x=x_enc, y=y_enc, tooltip=tip))
            layers.append(
                alt.Chart(scen.assign(t=scen.apply(lambda r: f"{r['scenario']}: {r['cost']:.2f}×", axis=1)))
                .mark_text(color=INK, align="right", dx=-8, dy=-18, fontSize=12)
                .encode(x=x_enc, y=y_enc, text="t:N")
            )
            st.altair_chart(style(alt.layer(*layers), height=420), theme=None, width="stretch")
            table = pd.DataFrame(
                {
                    "Scenario": scen["scenario"].astype(str),
                    "AI share": scen["ai_share"].map(_pct),
                    "80% band of the share (forecast)": [
                        "" if np.isnan(a) else f"{_pct(a)} to {_pct(b)}" for a, b in zip(scen["lo80"], scen["hi80"])
                    ],
                    "Multiplier at the point estimate": scen["cost"].map(lambda v: f"{v:.2f}×"),
                    "Multiplier across the band (derived)": [
                        "" if np.isnan(a) else f"{a:.2f}× to {'unbounded' if math.isinf(b) else f'{b:.2f}×'}"
                        for a, b in zip(scen["cost_lo"], scen["cost_hi"])
                    ],
                    "Illustrative cost on your budget ($)": scen["budget"].map(lambda v: f"{v:,.0f}"),
                }
            )
            st.dataframe(table, hide_index=True, width="stretch")
            eight = cost[(cost["target"] == target) & (cost["model_size"] == "8B")]
            note = ""
            if not eight.empty and np.isfinite(float(eight["cost"].iloc[0])):
                note = (
                    f" The same law at 8B parameters gives {float(eight['cost'].iloc[0]):.2f}× at {_pct(float(eight['ai_share'].iloc[0]))} AI, "
                    "an extrapolation beyond the 19.9M to 268M models it was fitted on."
                )
        st.caption(
            "Multipliers are for 268M parameters trained on 20 human tokens per parameter, as in the paper's headline. "
            "Below 1× means AI text helps for that target. Grey bars mark the 80% band of the forecast AI share. Read the three targets side by side: the same unfiltered data "
            "looks costly when judged on human text and cheap when judged on a mixed or AI-written test set, which is why "
            "the authors recommend reporting human and AI loss separately. The band columns are our derivation: the 80% band of "
            "the forecast AI share (file `ai_share_forecast.csv`) pushed through the curve by linear interpolation; they are not in the paper." + note
        )
        _footer(
            curve_all,
            "Download filtered curve",
            "compute_cost_curve.csv",
            "cost_download",
            f"{WILDAI_CITE} File `cost_of_not_filtering.csv`; forecast bands from `ai_share_forecast.csv`.",
            "In the source file the multiplier is infinite from 59% AI share for the human-text targets (no compute matches "
            "under the fitted law).",
        )
