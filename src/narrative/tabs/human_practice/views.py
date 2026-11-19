"""Renderers for the human-practice page: the web-data and model-training charts (WildAI and Schaeffer et al.),
the workforce charts, and the page's answer, decision, limits and sources blocks.  Each view sits in a keyed
container and carries its own title, unit, source, latest-observation caption, controls, outputs and a CSV download."""

from __future__ import annotations

import math

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from narrative.human_practice_data import CONTEXT_NOTE, WILDAI_COMMIT, WORKFORCE_COMMIT

HUMAN = "#2a78d6"
AI = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"
NEUTRAL = "#6b6a66"


def style(chart: alt.TopLevelMixin, height: int = 380) -> alt.TopLevelMixin:
    """Apply the page's chart theme: recessive grid, text in ink tokens, legend on top."""
    return (
        chart.properties(height=height)
        .configure(background=SURFACE)
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=INK2,
            titleColor=INK,
            titleFontWeight="normal",
            labelFontSize=12,
            titleFontSize=12,
            gridColor=GRID,
            domainColor=GRID,
            tickColor=GRID,
        )
        .configure_legend(
            labelColor=INK2,
            titleColor=INK2,
            labelFontSize=12,
            titleFontSize=12,
            orient="top",
            direction="horizontal",
            symbolStrokeWidth=2,
        )
        .configure_title(color=INK, fontWeight="normal")
    )


# Third label in the web-composition chart (documents Pangram labels as mixed human and AI).
MIXED = "#a3a29c"
# Evidence strength is a judgement, shown by an ink ramp and by shape so it survives a CVD check.
STRENGTH_ORDER = ["High", "Medium", "Low"]
STRENGTH_COLOURS = ["#0b0b0b", "#6b6a66", "#a3a29c"]
STRENGTH_SHAPES = ["circle", "square", "triangle-up"]


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


def _footer(
    frame: pd.DataFrame,
    label: str,
    file_name: str,
    key: str,
    source: str,
    note: str | None = None,
) -> None:
    with st.expander("Show the data table"):
        st.dataframe(frame, hide_index=True, width="stretch")
    st.caption(f"Source: {source}")
    if note:
        st.caption(note)
    st.download_button(
        label, data=_csv(frame), file_name=file_name, mime="text/csv", key=key
    )


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
        st.caption(
            "Unit: definitions (n = 8). Latest observation: not applicable (a literature review of 28 papers)."
        )
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
        chosen = st.multiselect(
            "Filter by family", families, default=families, key="family_filter"
        )
        mask = defs["families"].map(
            lambda value: any(f in value.split(" | ") for f in chosen)
        )
        shown = defs[mask]
        if shown.empty:
            st.info(EMPTY)
        else:
            compact = pd.DataFrame(
                {
                    "#": shown["id"],
                    "Definition": shown["short_name"],
                    "Family": shown["families"].str.replace(" | ", "; ", regex=False),
                    "Collapse: accumulate?": shown["collapse_accumulate"].map(
                        {True: "yes", False: "no"}
                    ),
                    "Collapse: replace?": shown["collapse_replace"].map(
                        {True: "yes", False: "no"}
                    ),
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
                    "Collapse: accumulate?": st.column_config.TextColumn(
                        "Collapse: accumulate?", width=140
                    ),
                    "Collapse: replace?": st.column_config.TextColumn(
                        "Collapse: replace?", width=120
                    ),
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
            st.markdown(
                f"**In this dashboard ({row['covered_in']}):** {row['coverage_note']}"
            )
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
            "Definition 5 sits in two of the paper's families, so it appears under both filters. \"Realistic "
            "conditions\" and the Section 5 forecast are the authors' judgement in a position paper.",
        )


# ----------------------------------------------------------------------------- 4. Figure 3
LABEL_ALL_UP_TO = (
    2  # print a value at every point while this many model sizes or fewer are selected
)
BUDGET_NAMES = {
    4.72: "about 5",
    18.88: "about 20",
    37.76: "about 40",
    54.72: "about 55",
    72.97: "about 73",
    87.5: "about 88",
}


def render_loss_effect(
    data: pd.DataFrame, today_share: float, today_month: pd.Timestamp
) -> None:
    data = data[data["in_figure"]].copy()
    sizes = {
        "19.9m": "19.9M",
        "35.8m": "35.8M",
        "86.2m": "86.2M",
        "135m": "135M",
        "268m": "268M",
    }
    r_today = today_share / (1 - today_share)
    with st.container(key="loss_effect"):
        _heading(
            "What AI text does to a model that learns from it",
            "For a model with a fixed human-token budget, what happens to its loss on human text when AI text, or fresh "
            "human text, is added?",
        )
        st.caption(
            "Unit: percent change in loss (bits per byte on C4) against the same model trained on human text only. Latest observation: not applicable (a fixed set of released models)."
        )
        c1, c2 = st.columns([3, 2])
        budget = c1.select_slider(
            "Human tokens per parameter (training budget)",
            options=list(BUDGET_NAMES),
            value=18.88,
            format_func=lambda b: f"{BUDGET_NAMES[b]} ({b})",
            key="fig3_budget",
        )
        chosen = c2.multiselect(
            "Model sizes", list(sizes.values()), default=["268M"], key="fig3_sizes"
        )
        d1, d2 = st.columns(2)
        show_human = d1.checkbox(
            "Compare with adding fresh human text", value=True, key="fig3_show_human"
        )
        mark_today = d2.checkbox(
            f"Mark today's web ({_pct(today_share)} AI in {today_month:%b %Y})",
            value=True,
            key="fig3_mark_today",
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
                arm_label=frame["arm"].map(
                    {"ai": "AI text added", "human": "Fresh human text added"}
                ),
            )
            size_order = [sizes[k] for k in sizes if k in set(frame["size"])]
            x = alt.X(
                "x:Q",
                scale=alt.Scale(type="log", domain=[0.002, 100]),
                title="Tokens added per human token (log scale)",
                axis=alt.Axis(
                    values=[0.01, 0.1, 1, 10, 100],
                    labelExpr="datum.value + '×'",
                    grid=False,
                ),
            )
            y = alt.Y("change_pct:Q", title="Change in loss vs human-only control (%)")
            colour = alt.Color(
                "arm_label:N",
                scale=alt.Scale(
                    domain=["AI text added", "Fresh human text added"],
                    range=[AI, HUMAN],
                ),
                legend=alt.Legend(title="Added to a fixed human corpus"),
            )
            sized = alt.Size(
                "size_label:O",
                sort=size_order,
                scale=alt.Scale(range=[30, 170]),
                legend=alt.Legend(title="Model size"),
            )
            tooltip = [
                alt.Tooltip("name:N", title="Run"),
                alt.Tooltip("arm_label:N", title="Added"),
                alt.Tooltip("x:Q", format=".3f", title="Tokens added per human token"),
                alt.Tooltip("change_pct:Q", format="+.2f", title="Change in loss (%)"),
                alt.Tooltip("bpb:Q", format=".4f", title="Run loss (bpb)"),
                alt.Tooltip("ctrl_bpb:Q", format=".4f", title="Control loss (bpb)"),
            ]
            zero = (
                alt.Chart(pd.DataFrame({"y": [0]}))
                .mark_rule(color=INK2, strokeWidth=1)
                .encode(y="y:Q")
            )
            lines = (
                alt.Chart(frame)
                .mark_line(strokeWidth=1.5, opacity=0.8)
                .encode(
                    x=x,
                    y=y,
                    color=colour,
                    detail=alt.Detail(["size_label:N", "arm_label:N"]),
                )
            )
            points = (
                alt.Chart(frame)
                .mark_point(filled=True, opacity=0.95, stroke="white", strokeWidth=0.8)
                .encode(x=x, y=y, color=colour, size=sized, tooltip=tooltip)
            )
            layers = [zero, lines, points]
            # Print the value at every point.  With three or more sizes the labels would collide, so only the
            # largest selected size is labelled and the caption says so.
            labelled = (
                frame
                if len(size_order) <= LABEL_ALL_UP_TO
                else frame[frame["size_label"] == size_order[-1]]
            )
            labelled = labelled.assign(
                text=labelled["change_pct"].map(lambda v: f"{v:+.2f}%")
            )
            # AI labels sit above the point, moving to the upper left where the curve climbs; human labels sit below.
            steep = (labelled["arm"] == "ai") & (labelled["x"] >= 0.3)
            for part, props in (
                (labelled[(labelled["arm"] == "ai") & ~steep], dict(dy=-15)),
                (labelled[steep], dict(align="right", dx=-9, dy=-7)),
                (labelled[labelled["arm"] == "human"], dict(dy=16)),
            ):
                layers.append(
                    alt.Chart(part)
                    .mark_text(fontSize=11, **props)
                    .encode(
                        x=x,
                        y=y,
                        text="text:N",
                        color=alt.Color("arm_label:N", legend=None),
                    )
                )
            if mark_today:
                today = pd.DataFrame(
                    {
                        "x": [r_today],
                        "text": [
                            f"today's web ≈ {_pct(today_share, 0)} AI, r ≈ {r_today:.2f}"
                        ],
                    }
                )
                layers.append(
                    alt.Chart(today)
                    .mark_rule(color=NEUTRAL, strokeDash=[4, 3])
                    .encode(x="x:Q")
                )
                layers.append(
                    alt.Chart(today)
                    .mark_text(
                        color=INK2, align="left", dx=5, baseline="top", fontSize=11
                    )
                    .encode(x="x:Q", y=alt.value(6), text="text:N")
                )
            st.altair_chart(
                style(alt.layer(*layers), height=420), theme=None, width="stretch"
            )
            ai = frame[frame["arm"] == "ai"]
            hu = frame[frame["arm"] == "human"]
            m1, m2, m3 = st.columns(3)
            if not ai.empty:
                best, worst = (
                    ai.loc[ai["change_pct"].idxmin()],
                    ai.loc[ai["change_pct"].idxmax()],
                )
                m1.metric(
                    "Best result with AI text",
                    f"{best['change_pct']:+.2f}%",
                    delta=f"run {best['name']}",
                    delta_color="off",
                    delta_arrow="off",
                    border=True,
                )
                m2.metric(
                    "Worst result with AI text",
                    f"{worst['change_pct']:+.2f}%",
                    delta=f"run {worst['name']}",
                    delta_color="off",
                    delta_arrow="off",
                    border=True,
                )
            if not hu.empty:
                hb = hu.loc[hu["change_pct"].idxmin()]
                m3.metric(
                    "Best result with fresh human text",
                    f"{hb['change_pct']:+.2f}%",
                    delta=f"run {hb['name']}",
                    delta_color="off",
                    delta_arrow="off",
                    border=True,
                )
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
            frame.drop(columns=["size_label", "arm_label"], errors="ignore")
            if not frame.empty
            else data.head(0),
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
SCENARIOS = [
    ("2026 crawl", None),
    ("August 2026", None),
    ("end of 2027", "2027-12-01"),
    ("end of 2028", "2028-12-01"),
]


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
        st.caption(
            "Unit: compute multiplier (1× = same compute as training on the human subset). Output of the authors' fitted scaling law, not a measurement. Latest observation: not applicable."
        )
        c1, c2 = st.columns([3, 2])
        label = c1.radio(
            "What should the model be good at?",
            list(TARGETS),
            horizontal=True,
            key="cost_target",
        )
        budget = c2.number_input(
            "Illustrative: your training budget with filtered data ($)",
            min_value=0,
            value=1_000_000,
            step=100_000,
            key="cost_budget",
            help="An input for illustration only. It is not data from the paper.",
        )
        target = TARGETS[label]
        curve_all = cost[
            (cost["target"] == target) & (cost["model_size"] == "268M")
        ].sort_values("ai_share")
        finite = curve_all[np.isfinite(curve_all["cost"])]
        if curve_all.empty:
            st.info(EMPTY)
        else:
            scen = curve_all[
                curve_all["scenario"].notna() & (curve_all["scenario"] != "")
            ].copy()
            scen["scenario"] = pd.Categorical(
                scen["scenario"], [s for s, _ in SCENARIOS], ordered=True
            )
            scen = scen.sort_values("scenario")
            lows, highs = [], []
            for name, month in SCENARIOS:
                if month is None:
                    lows.append(np.nan)
                    highs.append(np.nan)
                else:
                    lows.append(float(forecast.loc[pd.Timestamp(month), "lo80"]))
                    highs.append(float(forecast.loc[pd.Timestamp(month), "hi80"]))
            scen["lo80"], scen["hi80"] = lows, highs
            xs, ys = finite["ai_share"].to_numpy(), finite["cost"].to_numpy()
            max_finite = float(xs.max())

            def interp(share: float) -> float:
                if np.isnan(share):
                    return float("nan")
                return (
                    float(np.interp(share, xs, ys))
                    if share <= max_finite
                    else float("inf")
                )

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
            x_enc = alt.X(
                "ai_share:Q",
                title="AI share of the web text used for training",
                axis=alt.Axis(
                    format="%", grid=False, values=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
                ),
                scale=alt.Scale(domain=[0, 0.6]),
            )
            lo_dom = min(0.8, float(finite["cost"].min()) / 1.3)
            hi_dom = max(2.0, min(8.0, float(finite["cost"].max()) * 1.3))
            ticks = [
                t for t in (0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8) if lo_dom <= t <= hi_dom
            ]
            y_enc = alt.Y(
                "cost:Q",
                title="Compute multiplier (log scale)",
                scale=alt.Scale(
                    type="log", domain=[lo_dom, hi_dom], nice=False, clamp=True
                ),
                axis=alt.Axis(values=ticks, labelExpr="datum.value + '×'"),
            )
            one = (
                alt.Chart(pd.DataFrame({"y": [1.0]}))
                .mark_rule(color=INK2, strokeWidth=1)
                .encode(y="y:Q")
            )
            one_label = (
                alt.Chart(
                    pd.DataFrame({"y": [1.0], "t": ["1× = same compute as human-only"]})
                )
                .mark_text(color=INK2, align="left", dx=4, dy=12, fontSize=11)
                .encode(x=alt.value(4), y="y:Q", text="t:N")
            )
            line = (
                alt.Chart(finite)
                .mark_line(color=AI, strokeWidth=2.5)
                .encode(x=x_enc, y=y_enc)
            )
            layers = [one, one_label, line]
            if len(finite) < len(curve_all):
                inf_start = float(
                    curve_all[~np.isfinite(curve_all["cost"])]["ai_share"].min()
                )
                gap = pd.DataFrame(
                    {"a": [inf_start], "b": [0.6], "t": ["no finite compute matches"]}
                )
                layers.append(
                    alt.Chart(gap)
                    .mark_rect(color=AI, opacity=0.12)
                    .encode(x="a:Q", x2="b:Q")
                )
                layers.append(
                    alt.Chart(gap)
                    .mark_text(
                        color=INK2,
                        align="right",
                        dx=12,
                        baseline="top",
                        fontSize=11,
                        angle=270,
                    )
                    .encode(x="a:Q", y=alt.value(6), text="t:N")
                )
            band_rows = scen.dropna(subset=["lo80"]).copy()
            band_rows["hi_plot"] = band_rows["hi80"].clip(upper=0.6)
            layers.append(
                alt.Chart(band_rows)
                .mark_rule(color=NEUTRAL, strokeWidth=2, opacity=0.7)
                .encode(x="lo80:Q", x2="hi_plot:Q", y=y_enc)
            )
            tip = [
                alt.Tooltip("scenario:N", title="Scenario"),
                alt.Tooltip("ai_share:Q", format=".1%", title="AI share"),
                alt.Tooltip("cost:Q", format=".2f", title="Compute multiplier"),
            ]
            layers.append(
                alt.Chart(scen)
                .mark_point(
                    filled=True,
                    color=AI,
                    size=110,
                    stroke="white",
                    strokeWidth=1.2,
                    opacity=1,
                )
                .encode(x=x_enc, y=y_enc, tooltip=tip)
            )
            layers.append(
                alt.Chart(
                    scen.assign(
                        t=scen.apply(
                            lambda r: f"{r['scenario']}: {r['cost']:.2f}×", axis=1
                        )
                    )
                )
                .mark_text(color=INK, align="right", dx=-8, dy=-18, fontSize=12)
                .encode(x=x_enc, y=y_enc, text="t:N")
            )
            st.altair_chart(
                style(alt.layer(*layers), height=420), theme=None, width="stretch"
            )
            table = pd.DataFrame(
                {
                    "Scenario": scen["scenario"].astype(str),
                    "AI share": scen["ai_share"].map(_pct),
                    "80% band of the share (forecast)": [
                        "" if np.isnan(a) else f"{_pct(a)} to {_pct(b)}"
                        for a, b in zip(scen["lo80"], scen["hi80"])
                    ],
                    "Multiplier at the point estimate": scen["cost"].map(
                        lambda v: f"{v:.2f}×"
                    ),
                    "Multiplier across the band (derived)": [
                        ""
                        if np.isnan(a)
                        else f"{a:.2f}× to {'unbounded' if math.isinf(b) else f'{b:.2f}×'}"
                        for a, b in zip(scen["cost_lo"], scen["cost_hi"])
                    ],
                    "Illustrative cost on your budget ($)": scen["budget"].map(
                        lambda v: f"{v:,.0f}"
                    ),
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
            "the forecast AI share (file `ai_share_forecast.csv`) pushed through the curve by linear interpolation; they are not in the paper."
            + note
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


KARAN_REPO = "https://github.com/karanmakhijauts/at-3-dvn"
BTOS_CITE = (
    "US Census Bureau, Business Trends and Outlook Survey (BTOS), https://www.census.gov/hfp/btos; file `btos_ai.csv` "
    f"as collected by Karan Makhija ([repo]({KARAN_REPO}), commit `{WORKFORCE_COMMIT[:7]}`)."
)
EVIDENCE_CITE = (
    f"Findings hand-built from the cited papers by Karan Makhija ([repo]({KARAN_REPO}), commit `{WORKFORCE_COMMIT[:7]}`), "
    "file `evidence.csv`. Each row links its paper."
)
CANARIES_URL = (
    "https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf"
)
CANARIES_CITE = (
    "Brynjolfsson, Chandar and Chen (August 2026), *Canaries in the Coal Mine? Six Facts about the Recent Employment "
    f"Effects of Artificial Intelligence*, Stanford Digital Economy Lab, [PDF]({CANARIES_URL}); file `entry_level_employment.csv`."
)


def _observed(ai_share: pd.DataFrame) -> pd.DataFrame:
    obs = ai_share[ai_share["kind"] == "observed"].copy()
    obs["month"] = pd.to_datetime(obs["month"])
    return obs.sort_values("month")


def _human_share(comp: pd.DataFrame, month: pd.Timestamp) -> float:
    rows = comp[(pd.to_datetime(comp["month"]) == month) & (comp["label"] == "Human")]
    return float(rows["token_share"].iloc[0])


def _relative_gap(entry: pd.DataFrame) -> tuple[float, float, float]:
    """Young exposed vs young less-exposed: (exposed change, less-exposed change, relative shortfall in %)."""
    by_id = entry.set_index("id")["change_pct"].astype(float)
    exposed, other = by_id["C1"], by_id["C2"]
    return exposed, other, 100 * (1 - (100 + exposed) / (100 + other))


# ----------------------------------------------------------------------------- answer
def render_answer_text(tables: dict[str, pd.DataFrame], label: str = "Our answer") -> None:
    evidence = tables["evidence"]
    out = evidence[evidence["panel"] == "output"]
    gains = int((out["direction"] == "gain").sum())
    with st.container(key="answer", border=True):
        st.markdown(
            f"**{label}: early signs of a real cost, but not yet a proven one.** "
            f"The efficiency is measured: AI is raising output today ({gains} of {len(out)} output findings show a gain). "
            "The cost falls on what tomorrow's workers and models learn from. For workers, early-career employment in "
            "AI-exposed occupations is thinning. For models, both the human-written share of web text and the value of "
            "that text for training are falling. The first is a descriptive association, the second is a share of a "
            "sample, and the third is a prediction from a fitted law on small models. A reader could weigh the same "
            "numbers the other way: the gains are measured, the costs are early indicators."
        )


def render_answer(tables: dict[str, pd.DataFrame]) -> None:
    evidence, entry, comp, cost = (
        tables["evidence"],
        tables["entry_level"],
        tables["web_composition"],
        tables["cost"],
    )
    adoption = tables["adoption"]
    obs = _observed(tables["ai_share"])
    last_month = obs["month"].iloc[-1]
    two_years = last_month - pd.DateOffset(years=2)
    human_then, human_now = (
        _human_share(comp, two_years),
        _human_share(comp, last_month),
    )
    out = evidence[evidence["panel"] == "output"]  # can be deleted if ruff complains
    gains = int((out["direction"] == "gain").sum())  # can be deleted if ruff complains
    exposed, other, shortfall = _relative_gap(entry)
    yes = adoption[adoption["answer"] == "Yes"].sort_values("period_order")
    first, latest = yes.iloc[0], yes.iloc[-1]
    aug = cost[
        (cost["target"] == "c4")
        & (cost["model_size"] == "268M")
        & (cost["scenario"] == "August 2026")
    ].iloc[0]

    render_answer_text(tables)

    cols = st.columns(4)
    cols[0].metric(
        "US firms using AI",
        f"{latest['share_pct']:.1f}%",
        delta=f"from {first['share_pct']:.1f}% ({first['period_label']} to {latest['period_label']})",
        delta_color="off",
        delta_arrow="off",
        border=True,
        height=KPI_HEIGHT,
    )
    cols[1].metric(
        "Jobs held by ages 22-25, AI-exposed work",
        f"{exposed:+.0f}%",
        delta=f"less-exposed peers {other:+.0f}%",
        delta_color="off",
        delta_arrow="off",
        border=True,
        height=KPI_HEIGHT,
    )
    cols[2].metric(
        "Human-labelled share of web text",
        _pct(human_now),
        delta=f"from {_pct(human_then)} in {two_years:%b %Y}",
        delta_color="off",
        delta_arrow="off",
        border=True,
        height=KPI_HEIGHT,
    )
    cols[3].metric(
        "Compute to match human-only training",
        f"{aug['cost']:.2f}×",
        delta=f"predicted, at {_pct(aug['ai_share'])} AI text",
        delta_color="off",
        delta_arrow="off",
        border=True,
        height=KPI_HEIGHT,
    )
    st.caption(
        f"Units and baselines differ. Firms: per cent of US firms answering Yes to the Census Bureau BTOS AI-use question, two-week periods (source: `btos_ai.csv`). Jobs: per cent change in "
        f"employment from November 2022 to June 2026, US payroll data from one provider. Web text: share of tokens in a "
        f"monthly sample of about 5,000 documents, latest {last_month:%B %Y}. Compute: a multiplier predicted by a fitted "
        "law for a 268M-parameter model, not a measured cost. Each figure is charted, with its source and limits, below."
    )


# ----------------------------------------------------------------------------- output vs skill
PANEL_HEADERS = {"output": "OUTPUT GAINS", "skill": "SKILL AND LEARNING SIGNALS"}


def _evidence_chart(frame: pd.DataFrame) -> alt.LayerChart:
    """One chart, two labelled groups: output findings on top, skill findings below."""
    rows, order = [], []
    for panel, header in PANEL_HEADERS.items():
        part = frame[frame["panel"] == panel].sort_values(
            "sample_size", ascending=False
        )
        order.append(header)
        rows.append(
            {
                "row": header,
                "kind": "header",
                "text": "" if len(part) else "no findings at the selected strength",
                "sample_size": 100,
            }
        )
        for r in part.itertuples():
            order.append(r.label)
            rows.append(
                {
                    "row": r.label,
                    "kind": "finding",
                    "text": ("▲ " if r.direction == "gain" else "▼ ") + r.short_label,
                    "sample_size": r.sample_size,
                    "evidence_strength": r.evidence_strength,
                    "design": r.design,
                    "finding": r.finding,
                }
            )
    data = pd.DataFrame(rows)
    findings, headers = data[data["kind"] == "finding"], data[data["kind"] == "header"]
    is_header = f"indexof({list(PANEL_HEADERS.values())!r}, datum.value) >= 0"
    y = alt.Y(
        "row:N",
        sort=order,
        title=None,
        axis=alt.Axis(
            labelLimit=260,
            grid=True,
            labelFontWeight={"expr": f"{is_header} ? 'bold' : 'normal'"},
            labelColor={"expr": f"{is_header} ? '{INK}' : '{INK2}'"},
        ),
    )
    x = alt.X(
        "sample_size:Q",
        title="People in the study (log scale)",
        scale=alt.Scale(type="log", domain=[100, 300000]),
        axis=alt.Axis(values=[100, 300, 1000, 3000, 10000], format=",d", grid=False),
    )
    legend = alt.Legend(title="Evidence strength")
    points = (
        alt.Chart(findings)
        .mark_point(filled=True, size=170, opacity=1)
        .encode(
            x=x,
            y=y,
            color=alt.Color(
                "evidence_strength:N",
                scale=alt.Scale(domain=STRENGTH_ORDER, range=STRENGTH_COLOURS),
                legend=legend,
            ),
            shape=alt.Shape(
                "evidence_strength:N",
                scale=alt.Scale(domain=STRENGTH_ORDER, range=STRENGTH_SHAPES),
                legend=legend,
            ),
            tooltip=[
                alt.Tooltip("row:N", title="Study"),
                alt.Tooltip("design:N", title="Design"),
                alt.Tooltip("finding:N", title="Finding"),
            ],
        )
    )
    text = (
        alt.Chart(findings)
        .mark_text(color=INK, align="left", dx=12, fontSize=12)
        .encode(x=x, y=y, text="text:N")
    )
    notes = (
        alt.Chart(headers)
        .mark_text(color=INK2, align="left", fontSize=12, fontStyle="italic")
        .encode(x=x, y=y, text="text:N")
    )
    return style(alt.layer(notes, points, text), height=90 + 44 * len(order))


def render_evidence(evidence: pd.DataFrame) -> None:
    with st.container(key="output_vs_skill"):
        _heading(
            "Output gains against skill signals",
            "The same tools that raise output: what do they do to judgement and learning?",
        )
        st.caption(
            "Unit: one dot per finding, placed by the number of people studied; the printed label is the finding, with ▲ for a "
            "gain and ▼ for a loss. The findings measure different things, so they are not combined into one score. "
            "Studies date from 2023 to 2025. Latest observation: not applicable (published studies)."
        )
        strengths = st.multiselect(
            "Evidence strength",
            STRENGTH_ORDER,
            default=STRENGTH_ORDER,
            key="evidence_strength",
        )
        frame = evidence[evidence["evidence_strength"].isin(strengths)]
        out, skill = frame[frame["panel"] == "output"], frame[frame["panel"] == "skill"]
        if frame.empty:
            st.info(EMPTY)
        else:
            st.markdown(
                f"##### {int((out['direction'] == 'gain').sum())} of {len(out)} output findings show a gain. Of {len(skill)} skill "
                f"findings, {int((skill['direction'] == 'loss').sum())} show a loss and {int((skill['direction'] == 'gain').sum())} a gain."
            )
            st.altair_chart(
                _evidence_chart(frame),
                theme=None,
                width="stretch",
                key="evidence_chart",
            )
            with st.expander(
                "Read each finding, its design and how far it was checked",
                expanded=False,
            ):
                st.dataframe(
                    frame[
                        [
                            "panel_title",
                            "label",
                            "design",
                            "sample_size",
                            "sample_unit",
                            "finding",
                            "evidence_strength",
                            "strength_rationale",
                            "source_url",
                            "location_in_source",
                            "check_status",
                        ]
                    ],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "source_url": st.column_config.LinkColumn("source"),
                        "panel_title": "panel",
                    },
                )
        st.caption(
            "Skill findings are task accuracy, self-reported thinking or a hint of learning. None is a long-run test of "
            "ability. Evidence strength is a judgement made for this dashboard (see `strength_rationale`); `check_status` "
            "says how much of each paper was read. The Dell'Acqua et al. rows were entered from a summary and still need "
            "checking against the paper."
        )
        _footer(
            frame,
            "Download filtered findings",
            "output_skill_findings.csv",
            "evidence_download",
            EVIDENCE_CITE,
        )


# ----------------------------------------------------------------------------- entry level
def render_entry_level(entry: pd.DataFrame) -> None:
    with st.container(key="entry_level"):
        _heading(
            "Fewer early-career seats in AI-exposed work",
            "Where do people learn a job by doing it, and are those places shrinking?",
        )
        st.caption(
            "Unit: per cent change in employment, November 2022 to June 2026, in US payroll records from one provider "
            "(ADP; 3.5 to 5 million employees a month). Baseline: each group's own November 2022 level. Latest "
            'observation: June 2026. The values are rounded in the paper ("about").'
        )
        exposed, other, shortfall = _relative_gap(entry)
        left, right = st.columns([3, 2], gap="large")
        with left:
            frame = entry.assign(
                text=entry["change_pct"].map(lambda v: f"{v:+.0f}%"),
                highlight=entry["highlight"].astype(str).str.lower().eq("true"),
            )
            order = list(frame.sort_values("change_pct")["group"])
            y = alt.Y(
                "group:N",
                sort=order,
                title=None,
                axis=alt.Axis(labelLimit=280, grid=False),
            )
            x = alt.X(
                "change_pct:Q",
                title="Change in employment, Nov 2022 to Jun 2026 (%)",
                scale=alt.Scale(domain=[-16, 16]),
            )
            bars = (
                alt.Chart(frame)
                .mark_bar(size=26)
                .encode(
                    x=x,
                    y=y,
                    color=alt.Color(
                        "highlight:N",
                        scale=alt.Scale(domain=[True, False], range=[AI, NEUTRAL]),
                        legend=None,
                    ),
                )
            )
            zero = (
                alt.Chart(pd.DataFrame({"x": [0]}))
                .mark_rule(color=INK2)
                .encode(x="x:Q")
            )
            pos = (
                alt.Chart(frame[frame["change_pct"] >= 0])
                .mark_text(color=INK, align="left", dx=6, fontSize=13)
                .encode(x=x, y=y, text="text:N")
            )
            neg = (
                alt.Chart(frame[frame["change_pct"] < 0])
                .mark_text(color=INK, align="right", dx=-6, fontSize=13)
                .encode(x=x, y=y, text="text:N")
            )
            st.altair_chart(
                style(bars + zero + pos + neg, height=250), theme=None, width="stretch"
            )
        with right:
            st.metric(
                "Gap between the two groups aged 22 to 25",
                f"{other - exposed:.0f} points",
                delta=f"a {shortfall:.0f}% relative shortfall",
                delta_color="off",
                delta_arrow="off",
                border=True,
            )
            st.markdown(
                f"Put another way, employment of the exposed group is {shortfall:.0f}% below where it would be had it kept "
                "pace with less-exposed peers of the same age. "
                "The authors report that the gap comes mainly from **reduced hiring**, not more people leaving, and that "
                "it is concentrated where AI use substitutes for tasks."
            )
        st.caption(
            "This is where the page's argument makes an inference. The paper measures employment; it does not measure "
            "learning. Fewer early-career hires means fewer people doing the entry-level work through which skills are "
            "normally built, which is our reading. The authors call their results descriptive, say they do not estimate a "
            'causal effect of AI, and report that the size of the gap is specific to the ADP data. "AI-exposed" means the '
            "two highest of five exposure groups (Eloundou et al. 2024 ratings)."
        )
        _footer(
            entry,
            "Download employment changes",
            "entry_level_employment.csv",
            "entry_download",
            CANARIES_CITE,
            "The four values were entered from an automated summary of the PDF on 10 November 2026; the quoted sentences and "
            "page numbers are in the table. The orange bar is the group the paper highlights. The 19% is recomputed here "
            "as 1 − (100 − 11) / (100 + 10).",
        )


# ----------------------------------------------------------------------------- web composition
LABELS = {
    "Human": ("Human-labelled", HUMAN, 0),
    "Mixed": ("Mixed", MIXED, 1),
    "AI": ("AI-labelled", AI, 2),
}


def render_web_composition(comp: pd.DataFrame, ai_share: pd.DataFrame) -> None:
    comp = comp.copy()
    comp["month"] = pd.to_datetime(comp["month"])
    last = comp["month"].max()
    then = last - pd.DateOffset(years=2)
    with st.container(key="web_composition"):
        _heading(
            "Human writing is a shrinking share of new web text",
            "How much of the web text collected each month is still written by people alone?",
        )
        st.caption(
            f"Unit: share of sampled web text by label, per month (January 2021 to {last:%B %Y}). Latest observation: "
            f"{last:%B %Y}. Each month is about 5,000 sampled documents that pass FineWeb's quality filters, labelled by "
            "Pangram's detector as human, AI or mixed. The sampling source changes in July 2025 (FineWeb to random Common "
            "Crawl files)."
        )
        basis = st.radio(
            "Measure the share by",
            ["Tokens", "Documents"],
            horizontal=True,
            key="composition_basis",
        )
        col = "token_share" if basis == "Tokens" else "document_share"
        wide = (
            comp.pivot(index="month", columns="label", values=col)
            .reindex(columns=list(LABELS))
            .fillna(0.0)
        )
        long = wide.reset_index().melt(
            id_vars="month", var_name="label", value_name="share"
        )
        long["name"] = long["label"].map(lambda v: LABELS[v][0])
        long["order"] = long["label"].map(lambda v: LABELS[v][2])
        names = [v[0] for v in LABELS.values()]
        cols = st.columns(3)
        for box, key in zip(cols, LABELS):
            box.metric(
                f"{LABELS[key][0]} share, {last:%b %Y}",
                _pct(wide.loc[last, key]),
                delta=f"{_pct(wide.loc[then, key])} in {then:%b %Y}",
                delta_color="off",
                delta_arrow="off",
                border=True,
            )
        x = alt.X(
            "month:T",
            title=None,
            axis=alt.Axis(format="%Y", tickCount="year", grid=False),
            scale=alt.Scale(
                domain=[
                    comp["month"].min().isoformat(),
                    (last + pd.DateOffset(months=9)).isoformat(),
                ]
            ),
        )
        area = (
            alt.Chart(long)
            .mark_area(opacity=0.9)
            .encode(
                x=x,
                y=alt.Y(
                    "share:Q",
                    stack="zero",
                    title=f"Share of sampled web {basis.lower()}",
                    axis=alt.Axis(format="%"),
                    scale=alt.Scale(domain=[0, 1]),
                ),
                color=alt.Color(
                    "name:N",
                    scale=alt.Scale(
                        domain=names, range=[v[1] for v in LABELS.values()]
                    ),
                    legend=alt.Legend(title="Pangram label"),
                ),
                order=alt.Order("order:Q"),
            )
        )
        end = wide.loc[last]
        mids, base = [], 0.0
        for key in LABELS:
            mids.append(
                {
                    "month": last,
                    "y": base + end[key] / 2,
                    "text": f"{LABELS[key][0]} {_pct(end[key])}",
                }
            )
            base += end[key]
        # keep the two thin top bands' labels from overlapping
        mids[1]["y"] = min(mids[1]["y"], mids[2]["y"] - 0.07)
        ends = (
            alt.Chart(pd.DataFrame(mids))
            .mark_text(color=INK, align="left", dx=6, fontSize=12)
            .encode(x="month:T", y=alt.Y("y:Q"), text="text:N")
        )
        st.altair_chart(style(area + ends, height=340), theme=None, width="stretch")
        forecast = (
            ai_share[ai_share["kind"] == "forecast"]
            .assign(month=lambda f: pd.to_datetime(f["month"]))
            .set_index("month")
        )
        f27, f28 = (
            forecast.loc[pd.Timestamp("2027-12-01")],
            forecast.loc[pd.Timestamp("2028-12-01")],
        )
        st.markdown(
            f"**Where the trend points.** If the recent trend continues, the source's forecast puts the AI-labelled share of "
            f"tokens at {_pct(f27['share'])} by the end of 2027 (80% band {_pct(f27['lo80'])} to {_pct(f27['hi80'])}) and "
            f"{_pct(f28['share'])} by the end of 2028 (80% band {_pct(f28['lo80'])} to {_pct(f28['hi80'])}). This is an "
            "extrapolation of the monthly series (a random walk with drift), not an observation; the compute chart in "
            "section 4 marks both scenarios."
        )
        st.caption(
            "Read this as a share, not a volume: every month is the same size of sample, so the chart cannot show whether "
            "people are writing less in total, only that their writing is a smaller part of what a crawler now collects. "
            "Labels depend on one detector (false-positive rate 0.05% and false-negative rate 1.99%, as reported by "
            "Pangram's own team)."
        )
        _footer(
            comp.assign(month=comp["month"].dt.strftime("%Y-%m")),
            "Download web composition",
            "web_composition.csv",
            "composition_download",
            f"{WILDAI_CITE} File `monthly_topic_format.csv`, summed by month and label; forecast from `ai_share_forecast.csv`.",
        )


# ----------------------------------------------------------------------------- decision
def render_decision(tables: dict[str, pd.DataFrame]) -> None:
    evidence, entry, comp, cost = (
        tables["evidence"],
        tables["entry_level"],
        tables["web_composition"],
        tables["cost"],
    )
    out = evidence[evidence["panel"] == "output"]
    gains = int((out["direction"] == "gain").sum())
    exposed, other, shortfall = _relative_gap(entry)
    obs = _observed(tables["ai_share"])
    last = obs["month"].iloc[-1]
    human_now, human_then = (
        _human_share(comp, last),
        _human_share(comp, last - pd.DateOffset(years=2)),
    )
    c4 = cost[(cost["target"] == "c4") & (cost["model_size"] == "268M")].set_index(
        "scenario"
    )["cost"]
    e4 = (
        evidence.set_index("id").loc["E4", "short_label"]
        if "E4" in set(evidence["id"])
        else ""
    )
    with st.container(key="decision"):
        st.subheader(
            "Where to prioritise human skilled input, and where AI-efficient output"
        )
        st.caption(
            "This table is our reading of the evidence above for a C-suite reader. It is an interpretation, not a finding "
            "of any one source, and the last column says what would need testing first."
        )
        rows = pd.DataFrame(
            [
                {
                    "Area": "Routine drafting and support tasks AI handles well",
                    "Lean towards": "AI-efficient output",
                    "Evidence on this page": f"{gains} of {len(out)} output findings show a gain, largest for less experienced workers.",
                    "Not settled": "Single firms and short tasks; whether gains last is untested here.",
                },
                {
                    "Area": "Judgement calls where AI can be confidently wrong",
                    "Lean towards": "Human skilled input, with AI as a second opinion",
                    "Evidence on this page": f"On a task built to mislead the AI, accuracy was {e4} (unaided vs with AI).",
                    "Not settled": "One designed task; shows a risk, not a typical effect.",
                },
                {
                    "Area": "Entry-level roles and on-the-job training",
                    "Lean towards": "Human practice: keep junior hiring and unaided practice",
                    "Evidence on this page": f"Employment of 22 to 25 year olds in AI-exposed jobs changed {exposed:+.0f}% against {other:+.0f}% for less-exposed peers.",
                    "Not settled": "Descriptive, not causal; employment is measured, learning is not.",
                },
                {
                    "Area": "The firm's own human-written knowledge",
                    "Lean towards": "Human skilled input: keep, label and govern it as an asset",
                    "Evidence on this page": f"Human-labelled share of sampled web text fell from {_pct(human_then)} to {_pct(human_now)} in two years.",
                    "Not settled": "A share of a sample, not a volume; says nothing about any one firm's data.",
                },
                {
                    "Area": "Training, fine-tuning or buying models built on web text",
                    "Lean towards": "Filter AI text; test on human and AI text separately",
                    "Evidence on this page": f"Predicted compute to match human-only training: {c4['August 2026']:.2f}× now, {c4['end of 2027']:.2f}× at the end-2027 forecast share.",
                    "Not settled": "A fitted law on models up to 268M parameters; pre-training only.",
                },
            ]
        )
        st.table(rows.set_index("Area"))


def render_rollout(tables: dict[str, pd.DataFrame]) -> None:
    """Karan Makhija's three rollout options (from "Smarter, or slipping?"), counts taken live from the evidence table."""
    evidence = tables["evidence"]
    n_gain = int((evidence[evidence["panel"] == "output"]["direction"] == "gain").sum())
    n_loss = int((evidence[evidence["panel"] == "skill"]["direction"] == "loss").sum())
    with st.container(key="rollout_options"):
        st.subheader("Rollout options for staff")
        st.caption(
            "The page does not make the decision. This shows what the evidence loaded so far says for and against each "
            "option. It is an interpretation, not a finding of any one source."
        )
        options = pd.DataFrame(
            [
                {
                    "Option": "Roll out to everyone",
                    "What supports it": f"{n_gain} findings show output gains, biggest for weaker or less experienced workers in all three.",
                    "What argues against it": f"{n_loss} findings show a skill or accuracy loss, including worse accuracy where AI can be convincingly wrong.",
                },
                {
                    "Option": "Restrict AI",
                    "What supports it": "Skill-loss signals, though the strongest comes from one deliberately tricky task.",
                    "What argues against it": "Gains in the larger and randomised studies, and no evidence here of a long-run skill decline.",
                },
                {
                    "Option": "Roll out with training and guardrails",
                    "What supports it": "Matches both sides: keeps the gains, and targets the risk where AI is wrong or over-trusted.",
                    "What argues against it": "This evidence does not test whether training works. That is an open question.",
                },
            ]
        )
        st.table(options.set_index("Option"))
        st.caption(
            "Limits: mostly short-term studies of single firms or tasks, so results may not carry over to your sector."
        )


def render_limits() -> None:
    with st.container(key="limits_and_questions"):
        st.subheader("What the data cannot show")
        st.markdown(
            "- **That AI caused the fall in early-career employment.** The source is descriptive, uses one payroll provider, "
            "and reports that divergent trends began around COVID-19.\n"
            "- **That people are learning less.** No dataset here measures skill over time. The link from fewer "
            "early-career seats to less learning is our inference.\n"
            "- **That people are writing less.** The web series is a share of a fixed-size monthly sample, labelled by one "
            "detector whose makers co-wrote the paper.\n"
            "- **That future models will get worse.** The model experiments mix AI text into human text once; they do not "
            "train models on their own output generation after generation. The compute multipliers are predictions from a "
            "law fitted on small models, in an arXiv preprint (v1, 30 September 2026) whose peer-review status we have not confirmed.\n"
            "- **Whether the gains outweigh the costs in money.** Profitability and the moral questions are covered on other "
            "pages of this app.\n"
            "- **Anything about one firm.** Most output and skill findings come from single firms or single tasks."
        )


def render_questions_and_changes() -> None:
    with st.container(key="questions_and_change"):
        with st.expander("Questions to take to your own organisation"):
            st.markdown(
                "- Which entry-level tasks are now done with AI, and where do juniors still practise unaided?\n"
                "- Do we record which of our documents are human-written and which are AI-assisted?\n"
                "- Do we train, fine-tune or buy models trained on web data, and how do our vendors handle AI text?\n"
                "- Do we test models on human text and AI text separately?\n"
                "- What would a 1.3× to 1.6× compute penalty cost us?"
            )
        with st.expander("What would change the answer"):
            st.markdown(
                "A causal study of AI and early-career hiring; a long-run measure of skill in AI-using teams; a count of "
                "human-written text by volume; peer review or a larger-scale replication of Russell et al.; and evidence on "
                "recursive training with realistic mixes of human and AI data."
            )


def render_sources(tables: dict[str, pd.DataFrame]) -> None:
    adoption = tables["adoption"]
    obs = _observed(tables["ai_share"])
    with st.container(key="sources"):
        st.subheader("Sources and last data refresh")
        rows = pd.DataFrame(
            [
                {
                    "Dataset": "US firms using AI (Census Bureau BTOS)",
                    "Latest observation": adoption.sort_values("period_order")[
                        "period_label"
                    ].iloc[-1],
                    "Copied into this app": f"26 Oct 2026 (Karan's repo, commit {WORKFORCE_COMMIT[:7]})",
                    "Licence": "US government work",
                },
                {
                    "Dataset": "Output and skill findings (five papers, 2023 to 2025)",
                    "Latest observation": "2025 (Lee et al.)",
                    "Copied into this app": f"26 Oct 2026 (Karan's repo, commit {WORKFORCE_COMMIT[:7]})",
                    "Licence": "Cited facts",
                },
                {
                    "Dataset": "Early-career employment (Brynjolfsson, Chandar and Chen)",
                    "Latest observation": "June 2026",
                    "Copied into this app": "10 Nov 2026 (from the August 2026 paper)",
                    "Licence": "Cited facts",
                },
                {
                    "Dataset": "Web text and model runs (WildAI, Russell et al.)",
                    "Latest observation": f"{obs['month'].iloc[-1]:%B %Y}",
                    "Copied into this app": f"3 Nov 2026 (commit {WILDAI_COMMIT[:7]})",
                    "Licence": "CC BY-NC-SA 4.0",
                },
                {
                    "Dataset": "Definitions of model collapse (Schaeffer et al.)",
                    "Latest observation": "2025 (arXiv v2)",
                    "Copied into this app": "26 Oct 2026 (table written from the paper)",
                    "Licence": "Cited facts",
                },
            ]
        )
        st.table(rows.set_index("Dataset"))
        st.caption(
            "Last data refresh: 11 November 2026. Every number on this page is in, or computed from, the files in "
            "`data/processed/human_practice/`, which `human_practice_data.py` rebuilds from the source copies in `data/raw/human_practice/`. See `data/DATA_DICTIONARY.md`."
        )
