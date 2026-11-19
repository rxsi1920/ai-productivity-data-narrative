import ast
import re

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import pycountry
import streamlit as st


def render_reports_timeseries(
    df_incidents: pd.DataFrame, df_reports: pd.DataFrame
) -> None:
    st.subheader(
        "Current advacements in AI technologies have consistently risen the incident rate."
    )
    st.markdown(
        "**Question:** Historically, how many incidents and reports have taken place and to what extent is this true? Is it worsening?"
    )
    metrics_box = st.container()

    datasets = {"Reports": df_reports, "Incidents": df_incidents}

    choice = st.selectbox("Select data", list(datasets.keys()), index=0)
    label = choice
    source_df = datasets[choice]

    if source_df is None or source_df.empty:
        st.warning("No data to display.")
        return

    date_col = next(
        (
            c
            for c in ["date_published", "date", "date_submitted", "published_date"]
            if c in source_df.columns
        ),
        None,
    )
    if date_col is None:
        st.error("No date column found (expected 'date_published', 'date', etc.).")
        return

    df = source_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    df = df.dropna(subset=[date_col])
    if df.empty:
        st.warning("No valid dates found.")
        return

    df["year"] = df[date_col].dt.year
    df = df[df["year"].between(2010, 2025)]

    yearly_counts = (
        df.groupby("year").size().reset_index(name="count").sort_values("year")
    )

    if len(yearly_counts) < 4:
        st.warning("Not enough yearly data to build a forecast.")
        return

    min_year = int(yearly_counts["year"].min()) + 3
    max_year = int(yearly_counts["year"].max())
    sel_year = st.slider(
        "Forecast from year",
        min_year,
        max_year,
        min(max(2025, min_year), max_year),
        step=1,
    )
    show_fan = st.toggle("Show fan", value=True)

    hist = yearly_counts[yearly_counts["year"] <= sel_year]
    counts = hist["count"].tolist()
    last, prev, prev2 = counts[-1], counts[-2], counts[-3]
    yoy_pct = (last - prev) / prev * 100 if prev else 0.0
    acceleration = (last - prev) - (prev - prev2)
    cumulative = int(hist["count"].sum())

    unit = label.lower()
    yoy_color = "#09ab3b" if yoy_pct >= 0 else "#ff2b2b"

    metric_specs = [
        (
            f"{label} in {sel_year}",
            f"{last:,}",
            f"{unit}/yr",
            f"{yoy_pct:+.1f}% vs {sel_year - 1}",
            yoy_color,
            "",
        ),
        (
            "Acceleration",
            f"{acceleration:+,}",
            f"{unit}/yr²",
            f"{last - prev:+,} {unit}/yr latest YoY change",
            "inherit",
            "Second difference of annual counts: how much the year-over-year increase itself grew or shrank.",
        ),
        (
            f"Cumulative {label} (2010 to {sel_year})",
            f"{cumulative:,}",
            unit,
            "",
            "inherit",
            "",
        ),
    ]

    with metrics_box:
        for col, (m_label, m_value, m_unit, m_delta, m_color, m_help) in zip(
            st.columns(3), metric_specs
        ):
            delta_html = (
                f'<div style="font-size:0.9rem;color:{m_color};">{m_delta}</div>'
                if m_delta
                else ""
            )
            col.markdown(
                f'<div title="{m_help}">'
                f'<div style="font-size:0.875rem;opacity:0.7;">{m_label}</div>'
                f'<div style="font-size:2.25rem;line-height:1.3;">{m_value}'
                f'<span style="font-size:0.9rem;opacity:0.7;margin-left:0.35rem;">{m_unit}</span>'
                f"</div>"
                f"{delta_html}"
                f"</div>",
                unsafe_allow_html=True,
            )

    recent = hist.tail(6)
    log_recent = np.log1p(recent["count"].to_numpy(dtype=float))
    slope, intercept = np.polyfit(recent["year"].to_numpy(dtype=float), log_recent, 1)
    resid = log_recent - (slope * recent["year"].to_numpy(dtype=float) + intercept)
    sigma = max(float(resid.std(ddof=1)), 0.05)

    fan_years = np.arange(sel_year, max_year + 4)
    h = fan_years - sel_year
    center = np.log1p(float(last)) + slope * h
    spread = sigma * np.sqrt(h)

    fan = pd.DataFrame(
        {
            "year": fan_years,
            "median": np.expm1(center),
            "lo50": np.clip(np.expm1(center - 0.674 * spread), 0, None),
            "hi50": np.expm1(center + 0.674 * spread),
            "lo90": np.clip(np.expm1(center - 1.645 * spread), 0, None),
            "hi90": np.expm1(center + 1.645 * spread),
        }
    )

    y_title = f"Number of {label}"

    base = alt.Chart(yearly_counts).encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("count:Q", title=y_title),
    )

    bars = base.mark_bar(opacity=0.7, color="#1941d6").encode(
        tooltip=["year:O", "count:Q"]
    )

    line = base.mark_line(color="firebrick", strokeWidth=2, point=True).encode(
        tooltip=["year:O", "count:Q"]
    )

    fan_base = alt.Chart(fan).encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0))
    )

    band90 = fan_base.mark_area(opacity=0.15, color="#7f7f7f").encode(
        y=alt.Y("lo90:Q", title=y_title),
        y2="hi90:Q",
        tooltip=[
            "year:O",
            alt.Tooltip("lo90:Q", title="90% low", format=".0f"),
            alt.Tooltip("hi90:Q", title="90% high", format=".0f"),
        ],
    )

    band50 = fan_base.mark_area(opacity=0.3, color="#7f7f7f").encode(
        y=alt.Y("lo50:Q", title=y_title),
        y2="hi50:Q",
        tooltip=[
            "year:O",
            alt.Tooltip("lo50:Q", title="50% low", format=".0f"),
            alt.Tooltip("hi50:Q", title="50% high", format=".0f"),
        ],
    )

    median_line = fan_base.mark_line(
        color="firebrick", strokeWidth=2, strokeDash=[6, 4]
    ).encode(
        y=alt.Y("median:Q", title=y_title),
        tooltip=[
            "year:O",
            alt.Tooltip("median:Q", title="Median forecast", format=".0f"),
        ],
    )

    layers = [bars, line]
    if show_fan:
        layers = [band90, band50, bars, line, median_line]

    chart = (
        alt.layer(*layers)
        .properties(
            title=alt.TitleParams(
                f"Annual AI-Incident {label} Since 2010", anchor="middle"
            ),
            height=400,
        )
        .configure(background="transparent")
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        fan_note = (
            "The shaded fan shows the 50% and 90% forecast ranges projected from the selected year. "
            if show_fan
            else ""
        )
        st.caption(
            f"The number of {label.lower()} has soared as AI has significantly progressed in its capabilities. These include automating "
            "attack vectors and in their scale of reach. Examples include automated scam calls and large scale data breaches. "
            f"{fan_note}"
            "Source: [[AI Incidents Database]](https://incidentdatabase.ai/apps/incidents/) ",
            text_alignment="center",
        )


def render_gmf_failures(data: pd.DataFrame) -> None:
    st.subheader("What technically goes wrong?")
    st.markdown(
        "**Question:** When AI incidents happen, which technical failures occur the most often?"
    )
    if not isinstance(data, pd.DataFrame) or data.empty:
        st.warning("No data to display.")
        return

    failure_col = next(
        (
            c
            for c in data.columns
            if "technical failure" in str(c).lower() and "note" not in str(c).lower()
        ),
        None,
    )
    if failure_col is None:
        st.error("No 'Known AI Technical Failure' column found in the dataset.")
        return

    id_col = next(
        (
            c
            for c in data.columns
            if str(c).strip().lower().replace("_", " ")
            in {"incident id", "incidentid", "id"}
        ),
        None,
    )

    splitter = r"\s*[;|\n,]\s*"
    blank = {"nan", "none", "n/a"}

    def parse(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        if isinstance(value, (list, tuple, set)):
            items = [str(v) for v in value]
        else:
            text = str(value).strip()
            if not text:
                return []
            if text.startswith("[") and text.endswith("]"):
                try:
                    parsed = ast.literal_eval(text)
                    items = (
                        [str(v) for v in parsed]
                        if isinstance(parsed, (list, tuple, set))
                        else [text]
                    )
                except (ValueError, SyntaxError):
                    items = re.split(splitter, text.strip("[]"))
            else:
                items = re.split(splitter, text)
        cleaned = [i.strip().strip("'\"") for i in items]
        return [i for i in cleaned if i and i.lower() not in blank]

    dark = st.context.theme.type == "dark"
    fg, muted = ("#d9e4ef", "#7d8fa3") if dark else ("#1f2d3d", "#5b6b7d")
    grid, domain = "rgba(150, 180, 210, 0.1)", "rgba(150, 180, 210, 0.4)"

    df = data.copy()
    df["_incident"] = df[id_col] if id_col is not None else df.index
    df["_failure"] = df[failure_col].apply(parse)

    total_incidents = df["_incident"].nunique()
    exploded = (
        df[["_incident", "_failure"]]
        .explode("_failure")
        .dropna(subset=["_failure"])
        .drop_duplicates()
    )
    if exploded.empty:
        st.warning("No technical-failure classifications found.")
        return

    classified = exploded["_incident"].nunique()
    counts = (
        exploded.groupby("_failure")["_incident"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
    )
    counts.columns = ["failure", "incidents"]
    counts["share"] = counts["incidents"] / classified

    plot = counts.head(12)

    base = alt.Chart(plot).encode(
        y=alt.Y("failure:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320)),
        x=alt.X("incidents:Q", title="No. of Incidents recorded"),
    )

    bars = base.mark_bar(height=22).encode(
        color=alt.Color(
            "incidents:Q", scale=alt.Scale(scheme="tealblues"), legend=None
        ),
        tooltip=[
            alt.Tooltip("failure:N", title="Technical failure"),
            alt.Tooltip("incidents:Q", title="Incidents", format=",d"),
            alt.Tooltip("share:Q", title="Share of classified incidents", format=".1%"),
        ],
    )

    labels = base.mark_text(
        align="left", baseline="middle", dx=8, color=fg, fontSize=13, fontWeight="bold"
    ).encode(text=alt.Text("incidents:Q", format=",d"))

    chart = (
        (bars + labels)
        .properties(
            title=alt.TitleParams(
                "Most Common Technical Failures in Recorded AI Incidents",
                anchor="middle",
                color=fg,
            ),
            height=max(260, 30 * len(plot)),
            background="transparent",
        )
        .configure_view(strokeWidth=0)
        .configure_title(color=fg)
        .configure_axis(
            grid=True,
            gridColor=grid,
            domainColor=domain,
            tickColor=domain,
            labelColor=muted,
            titleColor=muted,
        )
    )

    top = counts.iloc[0]
    caption = (
        f"Of {total_incidents:,} incidents in the export, {classified:,} "
        f"({classified / total_incidents:.0%}) carry a technical-failure classification, and only those are counted. "
        f"The most frequent is {top['failure']}, recorded in {int(top['incidents']):,} incidents "
        f"({top['share']:.0%} of classified incidents). One incident can have several failures, so bars overlap "
        "and shares do not sum to 100%. Source: [AI Incident Database, GMF taxonomy]"
        "(https://incidentdatabase.ai/taxonomies/gmf/)."
    )

    st.altair_chart(chart, use_container_width=True, theme=None)
    st.caption(caption, text_alignment="center")


def render_() -> None:
    st.header("2. AI's Self-awareness of Morality")


def render_moral_summary(data: pd.DataFrame, label: str = "Our answer") -> None:

    last_year = 2025  # latest full year in the data; same count as the section 1 chart and Home
    published = pd.to_datetime(data["date_published"], errors="coerce", utc=True)
    total_last_year = f"{(published.dt.year == last_year).sum():,}"

    with st.container(key="moral_answer", border=True):
        st.markdown(f"""
            **{label}:** Early on, AI weakens our moral judgement and the safeguards are thin, but does not have a proveable cause. In controlled experiments, people who talked to a flattering AI felt more in the right and were less willing to repair the conflict, and this held in more than one study. Around that, the safety net is clean, in that reported AI incidents reached {total_last_year} in {last_year} and are still accelerating, models differ widely in how closely their moral scores match human validation, and in most areas of responsible AI only a minority of countries have a binding national framework. The first is a single-conversation experiment, the second is a count of reports, and the third is a snapshot of policy status. The effect on judgement is measured in surveys, the failures and gaps are indicators, and more importantly lacks a time-series data that indicates people's moral judgement erodes over time.
        """)


def render_human_validation_scores(data: pd.DataFrame) -> None:
    st.markdown(
        "**Question:** How do models place themselves against human validation?"
    )
    if data.empty:
        st.warning("No data to display.")
        return

    required_cols = [
        "evaluated_model_name",
        "dimension",
        "human_mean_score",
        "gpt55_score",
        "response_label_within_item",
    ]
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        st.error(f"Missing expected columns in dataset: {missing}")
        return

    df = data.copy()

    dimensions = ["Overall"] + sorted(df["dimension"].dropna().unique().tolist())
    selected_dimension = st.selectbox("Select Ethical/Safety Dimension", dimensions)

    if selected_dimension != "Overall":
        df = df[df["dimension"] == selected_dimension]

    if df.empty:
        st.warning("No data matches the selected filters.")
        return

    df["model_family"] = df["evaluated_model_name"].str.extract(r"^([A-Za-z]+)")[0]

    agg_df = (
        df.groupby(["evaluated_model_name", "model_family"])[
            ["human_mean_score", "gpt55_score"]
        ]
        .mean()
        .reset_index()
    )

    base = alt.Chart(agg_df).encode(
        x=alt.X(
            "human_mean_score:Q",
            title="Mean Human Validation Score (0-10)",
            scale=alt.Scale(zero=False),
        ),
        y=alt.Y(
            "gpt55_score:Q",
            title="Mean GPT-5.5 Score (0-10)",
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "model_family:N",
            title="Model Family",
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            "evaluated_model_name:N",
            "model_family:N",
            alt.Tooltip("human_mean_score:Q", format=".2f"),
            alt.Tooltip("gpt55_score:Q", format=".2f"),
        ],
    )

    points = base.mark_circle(size=140, opacity=0.85)
    labels = base.mark_text(align="left", dx=9, dy=-6, fontSize=11).encode(
        text="evaluated_model_name:N"
    )

    chart = (
        (points + labels)
        .properties(
            title=alt.TitleParams(
                "GPT-5.5 Score vs Human Validation Score Across Models",
                anchor="middle",
            ),
            height=500,
        )
        .configure(background="transparent")
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "This chart visualizes human validation and moral alignment scores across different LLM architectures. "
            "Lower scores highlight severe ethical drift, prompt compliance failures, and moral degradation under complex testing scenarios. "
            "Source: [[Human Validation - Scientometric LLM Ethics Benchmark]](https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/human_validation_scores_merged.csv).",
            text_alignment="center",
        )


def render_judge_agreement_heatmap(data: pd.DataFrame) -> None:
    def combine_judge_scores(*frames: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "judge_model_id",
            "evaluated_model_id",
            "evaluated_model_name",
            "run_id",
            "dimension",
            "item_id",
            "score",
            "unsafe_compliance",
        ]
        return pd.concat([f[cols] for f in frames], ignore_index=True)

    st.markdown(
        "**Question:** Do different AI judges agree on how ethically other models behave, "
        "and does a judge treat models from its own family differently?"
    )
    if not isinstance(data, pd.DataFrame) or data.empty:
        st.warning("No data to display.")
        return

    required_cols = ["judge_model_id", "evaluated_model_name", "dimension", "score"]
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        st.error(f"Missing expected columns in dataset: {missing}")
        return

    FG = "#d9e4ef"
    MUTED = "#7d8fa3"
    DARK = "#0b1118"
    GOLD = "#f5b942"

    df = data.copy()
    if "run_id" in df.columns:
        df = df[df["run_id"] == 1]
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["score", "judge_model_id", "evaluated_model_name"])

    dimensions = ["Overall"] + sorted(df["dimension"].dropna().unique().tolist())
    selected_dimension = st.selectbox(
        "Select Ethical/Safety Dimension", dimensions, key="judge_heatmap_dimension"
    )
    if selected_dimension != "Overall":
        df = df[df["dimension"] == selected_dimension]

    if df.empty:
        st.warning("No data matches the selected filters.")
        return

    judge_labels = {
        "gpt-5.5": "GPT-5.5",
        "deepseek-v4-pro": "DeepSeek V4 Pro",
        "qwen3.6-plus": "Qwen3.6 Plus",
    }

    agg = (
        df.groupby(["judge_model_id", "evaluated_model_name"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "mean_score"})
    )
    agg["judge"] = agg["judge_model_id"].map(judge_labels).fillna(agg["judge_model_id"])

    judge_family = agg["judge_model_id"].str.extract(r"^([A-Za-z]+)")[0].str.lower()
    model_family = (
        agg["evaluated_model_name"].str.extract(r"^([A-Za-z]+)")[0].str.lower()
    )
    agg["same_family"] = judge_family == model_family
    agg["offset"] = agg["mean_score"] - agg.groupby("evaluated_model_name")[
        "mean_score"
    ].transform("mean")

    model_order = (
        agg.groupby("evaluated_model_name")["mean_score"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    judge_means = agg.groupby("judge")["mean_score"].mean().sort_values()
    judge_order = judge_means.index.tolist()

    lo, hi = float(agg["mean_score"].min()), float(agg["mean_score"].max())
    mid = (lo + hi) / 2

    base = alt.Chart(agg).encode(
        x=alt.X(
            "judge:N",
            title="Model Judge (strictest to most lenient)",
            sort=judge_order,
            axis=alt.Axis(labelAngle=0, orient="top"),
        ),
        y=alt.Y("evaluated_model_name:N", title=None, sort=model_order),
    )

    heat = base.mark_rect().encode(
        color=alt.Color(
            "mean_score:Q",
            title="Mean score (0-10)",
            scale=alt.Scale(scheme="tealblues", domain=[lo, hi]),
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("evaluated_model_name:N", title="Evaluated model"),
            alt.Tooltip("judge:N", title="Judge"),
            alt.Tooltip("mean_score:Q", title="Mean score", format=".2f"),
            alt.Tooltip("offset:Q", title="Vs. all-judge average", format="+.2f"),
            alt.Tooltip("same_family:N", title="Same family"),
        ],
    )

    labels = base.mark_text(fontSize=13, fontWeight="bold").encode(
        text=alt.Text("mean_score:Q", format=".2f"),
        color=alt.condition(alt.datum.mean_score > mid, alt.value(FG), alt.value(DARK)),
    )

    outline = base.transform_filter(alt.datum.same_family == True).mark_rect(
        filled=False, stroke=GOLD, strokeWidth=3
    )

    chart = (
        (heat + labels + outline)
        .properties(
            title=alt.TitleParams(
                f"How Three AI Models Score Eight Models ({selected_dimension})",
                anchor="middle",
                color="black",
            ),
            height=420,
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=FG, titleColor=MUTED, labelFontSize=12)
        .configure_legend(labelColor=MUTED, titleColor=MUTED)
        .configure(background="transparent")
    )

    gap = float(judge_means.iloc[-1] - judge_means.iloc[0])
    top_by_judge = agg.loc[
        agg.groupby("judge")["mean_score"].idxmax(), "evaluated_model_name"
    ]
    bottom_by_judge = agg.loc[
        agg.groupby("judge")["mean_score"].idxmin(), "evaluated_model_name"
    ]

    caption = (
        f"Each cell is the mean score (0-10) one AI judge gave one model. "
        f"For {selected_dimension.lower()}, {judge_order[0]} is the strictest judge and "
        f"{judge_order[-1]} the most lenient, a gap of {gap:.2f} points."
    )
    if top_by_judge.nunique() == 1 and bottom_by_judge.nunique() == 1:
        caption += (
            f" All three judges nonetheless rank {top_by_judge.iloc[0]} highest and "
            f"{bottom_by_judge.iloc[0]} lowest."
        )
    if agg["same_family"].any() and (~agg["same_family"]).any():
        same_offset = agg.loc[agg["same_family"], "offset"].mean()
        other_offset = agg.loc[~agg["same_family"], "offset"].mean()
        caption += (
            f" Gold outlines mark a judge scoring a model from its own family: those cells sit "
            f"{same_offset:+.2f} points from the model's all-judge average, versus "
            f"{other_offset:+.2f} elsewhere. With only a few same-family pairs, this is suggestive, not conclusive. "
        )
    caption += (
        "Source: [[Human Validation Benchmark Dataset]]"
        "(https://github.com/universe-szw/scientometric-llm-ethics-benchmark)."
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(caption, text_alignment="center")


def render_trust_chart(data: pd.DataFrame) -> None:
    st.markdown("General trust in AI", unsafe_allow_html=True, text_alignment="center")

    trust_order = ["Very low", "Low", "Moderate", "High"]
    emoji_map = {
        "High": "😊",
        "Moderate": "😐",
        "Low": "😟",
        "Very low": "😠",
    }

    if isinstance(data, pd.DataFrame):
        if data.empty or "trust_in_ai_decisions" not in data.columns:
            st.warning("No trust data available.")
            return
        series = data["trust_in_ai_decisions"].dropna()
        scores = series.map({v: i for i, v in enumerate(trust_order)}).dropna()
        if scores.empty:
            st.warning("No trust data available.")
            return
        trust_level = trust_order[round(scores.mean())]
        counts = series.value_counts().reindex(trust_order, fill_value=0)
    else:
        trust_level = str(data)
        counts = None

    emoji = emoji_map.get(trust_level, "❓")

    st.markdown(
        """
    <style>
    .hover-container {
        position: relative;
        display: inline-block;
        font-size: 70px;
        line-height: 1.2;
        cursor: pointer;
    }
    .hover-table {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: opacity 0.2s, visibility 0.2s;
        z-index: 1000;
        font-size: 14px;
        line-height: normal;
        text-align: left;
        white-space: nowrap;
    }
    .hover-container:hover .hover-table {
        visibility: visible;
        opacity: 1;
    }
    .hover-table table {
        border-collapse: collapse;
        margin: 0;
        color: #333333 !important;
    }
    .hover-table th, .hover-table td {
        padding: 6px 12px !important;
        border: 1px solid #eeeeee !important;
        text-align: left;
        color: #333333 !important;
        font-size: 14px !important;
        font-weight: normal !important;
    }
    .hover-table th {
        background-color: #f8f9fa;
        font-weight: bold !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    table_html = ""
    if counts is not None:
        table_html = (
            counts.rename("Count")
            .to_frame()
            .to_html(
                classes="hover-table-inner",
                border=0,
                index=True,
            )
            .replace("\n", "")
        )

    hover_html = f'<div class="hover-container">{emoji}<div class="hover-table">{table_html}</div></div>'

    st.markdown(
        f'<div style="text-align: center;">{hover_html}</div>', unsafe_allow_html=True
    )

    st.caption(
        f"Average trust level: {trust_level}<br>(hover to see table)<br>[Source](https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26)",
        text_alignment="center",
        unsafe_allow_html=True,
    )


def render_ai_replacement(data: pd.DataFrame) -> None:
    st.markdown(
        "Fear of AI replacing my job", unsafe_allow_html=True, text_alignment="center"
    )

    col = "ai_job_replacement_fear"
    if not isinstance(data, pd.DataFrame) or data.empty or col not in data.columns:
        st.warning("No job replacement fear data available.")
        return

    fear_order = [
        "Very unlikely",
        "Unlikely",
        "Neutral",
        "Somewhat likely",
        "Very likely",
    ]
    emoji_map = {
        "Very unlikely": "😎",
        "Unlikely": "🙂",
        "Neutral": "😐",
        "Somewhat likely": "😟",
        "Very likely": "😱",
    }

    series = data[col].dropna()
    scores = series.map({v: i for i, v in enumerate(fear_order)}).dropna()
    if scores.empty:
        st.warning("No job replacement fear data available.")
        return

    fear_level = fear_order[round(scores.mean())]
    emoji = emoji_map.get(fear_level, "❓")
    counts = series.value_counts().reindex(fear_order, fill_value=0)

    st.markdown(
        """
    <style>
    .hover-container {
        position: relative;
        display: inline-block;
        font-size: 70px;
        line-height: 1.2;
        cursor: pointer;
    }
    .hover-table {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: opacity 0.2s, visibility 0.2s;
        z-index: 1000;
        font-size: 14px;
        line-height: normal;
        text-align: left;
        white-space: nowrap;
    }
    .hover-container:hover .hover-table {
        visibility: visible;
        opacity: 1;
    }
    .hover-table table {
        border-collapse: collapse;
        margin: 0;
        color: #333333 !important;
    }
    .hover-table th, .hover-table td {
        padding: 6px 12px !important;
        border: 1px solid #eeeeee !important;
        text-align: left;
        color: #333333 !important;
        font-size: 14px !important;
        font-weight: normal !important;
    }
    .hover-table th {
        background-color: #f8f9fa;
        font-weight: bold !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    table_html = (
        counts.rename("Count")
        .to_frame()
        .to_html(border=0, index=True)
        .replace("\n", "")
    )

    hover_html = (
        f'<div class="hover-container">{emoji}'
        f'<div class="hover-table">{table_html}</div></div>'
    )
    st.markdown(
        f'<div style="text-align: center;">{hover_html}</div>', unsafe_allow_html=True
    )

    st.caption(
        f"Average answer: {fear_level}<br>(hover to see table)<br>"
        "[Source](https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26)",
        text_alignment="center",
        unsafe_allow_html=True,
    )


def render_ai_framework_coverage(
    frameworks: pd.DataFrame, classifications: pd.DataFrame | None = None
) -> None:
    st.subheader("Do governments have rules for responsible AI?")
    st.markdown(
        "**Question:** For each area of responsible AI, how many countries have a national framework, "
        "and is it legally binding?"
    )
    if not isinstance(frameworks, pd.DataFrame) or frameworks.empty:
        st.warning("No framework data available.")
        return

    required = {"ISO3", "dimension", "indicator", "fr1_type", "fr1_enforceability"}
    missing = required - set(frameworks.columns)
    if missing:
        st.error(f"Missing required columns: {sorted(missing)}")
        return

    df = frameworks.copy()

    binding = pd.Series(False, index=df.index)
    adopted = pd.Series(False, index=df.index)
    draft = pd.Series(False, index=df.index)
    for n in ("1", "2"):
        type_col, enf_col = f"fr{n}_type", f"fr{n}_enforceability"
        if type_col not in df.columns or enf_col not in df.columns:
            continue
        ftype = df[type_col].astype("string")
        has_framework = ftype.notna() & (ftype != "No framework")
        is_draft = has_framework & (ftype == "Draft framework")
        is_adopted = has_framework & ~is_draft
        binding |= is_adopted & (df[enf_col] == "Binding")
        adopted |= is_adopted
        draft |= is_draft

    df["status"] = "No framework"
    df.loc[draft, "status"] = "Draft only"
    df.loc[adopted, "status"] = "Non-binding"
    df.loc[binding, "status"] = "Binding"

    group_options = {"All countries": None}
    if isinstance(classifications, pd.DataFrame) and "ISO3" in classifications.columns:
        extra = [
            c
            for c in ("region", "WB_income_group", "developing_status")
            if c in classifications.columns
        ]
        df = df.merge(classifications[["ISO3"] + extra], on="ISO3", how="left")
        labels = {
            "region": "Region",
            "WB_income_group": "Income",
            "developing_status": "Status",
        }
        for col in extra:
            for value in sorted(df[col].dropna().unique()):
                group_options[f"{labels[col]}: {value}"] = (col, value)

    c1, c2 = st.columns(2)
    with c1:
        dimension_options = ["All areas"] + sorted(
            df["dimension"].dropna().unique().tolist()
        )
        selected_dimension = st.selectbox(
            "Responsible AI dimension", dimension_options, key="framework_dimension"
        )
    with c2:
        selected_group = st.selectbox(
            "Country group", list(group_options.keys()), key="framework_group"
        )

    if selected_dimension != "All areas":
        df = df[df["dimension"] == selected_dimension]
    if group_options[selected_group] is not None:
        col, value = group_options[selected_group]
        df = df[df[col] == value]

    if df.empty:
        st.warning("No data matches the selected filters.")
        return

    order = ["Binding", "Non-binding", "Draft only", "No framework"]
    colors = ["#0e7490", "#67b7d1", "#f2b134", "#9aa5b1"]
    text_colors = ["#ffffff", "#0b1118", "#0b1118", "#0b1118"]

    n_countries = df["ISO3"].nunique()
    shares = (
        df.groupby(["indicator", "dimension", "status"])
        .size()
        .rename("n")
        .reset_index()
    )
    totals = shares.groupby("indicator")["n"].transform("sum")
    shares["share"] = shares["n"] / totals

    grid = (
        shares[["indicator", "dimension"]]
        .drop_duplicates()
        .assign(key=1)
        .merge(pd.DataFrame({"status": order, "key": 1}), on="key")
        .drop(columns="key")
    )
    shares = grid.merge(
        shares, on=["indicator", "dimension", "status"], how="left"
    ).fillna({"n": 0, "share": 0.0})
    shares["status"] = pd.Categorical(shares["status"], categories=order, ordered=True)
    shares = shares.sort_values(["indicator", "status"])
    shares["end"] = shares.groupby("indicator")["share"].cumsum()
    shares["start"] = shares["end"] - shares["share"]
    shares["mid"] = (shares["start"] + shares["end"]) / 2
    shares["status"] = shares["status"].astype(str)
    shares["label"] = shares.apply(
        lambda r: f"{r['share']:.0%}" if r["share"] >= 0.06 else "", axis=1
    )

    adopted_share = (
        shares[shares["status"].isin(["Binding", "Non-binding"])]
        .groupby("indicator")["share"]
        .sum()
        .sort_values(ascending=False)
    )
    indicator_order = adopted_share.index.tolist()

    base = alt.Chart(shares).encode(
        y=alt.Y(
            "indicator:N",
            sort=indicator_order,
            title=None,
            axis=alt.Axis(labelLimit=320),
        )
    )

    bars = base.mark_bar(height=22).encode(
        x=alt.X(
            "start:Q",
            title="Share of countries",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%"),
        ),
        x2="end:Q",
        color=alt.Color(
            "status:N",
            title="Status of national framework",
            scale=alt.Scale(domain=order, range=colors),
            legend=alt.Legend(
                orient="bottom",
                titleLimit=300,
            ),
        ),
        tooltip=[
            alt.Tooltip("indicator:N", title="Area"),
            alt.Tooltip("dimension:N", title="Dimension"),
            alt.Tooltip("status:N", title="Status"),
            alt.Tooltip("n:Q", title="Countries", format=",d"),
            alt.Tooltip("share:Q", title="Share", format=".0%"),
        ],
    )

    labels = base.mark_text(fontSize=12, fontWeight="bold").encode(
        x="mid:Q",
        text="label:N",
        color=alt.Color(
            "status:N",
            scale=alt.Scale(domain=order, range=text_colors),
            legend=None,
        ),
    )

    chart = (
        (bars + labels)
        .properties(
            title=alt.TitleParams(
                f"National AI Frameworks by Responsible-AI Area ({selected_group})",
                anchor="middle",
            ),
            height=max(260, 34 * len(indicator_order)),
        )
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )

    top, bottom = adopted_share.index[0], adopted_share.index[-1]
    binding_share = (
        shares.loc[shares["status"] == "Binding", "n"].sum() / shares["n"].sum()
    )
    caption = (
        f"Share of {n_countries} countries with a national framework for each area, by legal status. "
        f"{top} is the best covered, with {adopted_share.iloc[0]:.0%} of countries having an adopted framework; "
        f"{bottom} is the least covered at {adopted_share.iloc[-1]:.0%}. "
        f"Across the areas shown, {binding_share:.0%} of country-area pairs have a binding framework. "
        "Binding includes regional law applied to member states, such as the EU AI Act. "
        "Draft only means a framework exists but has not been adopted. "
        "Source: [[Global Index on Responsible AI, Global Survey dataset]](https://www.global-index.ai/)."
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(caption, text_alignment="center")

        if st.toggle("Show data", key="framework_table"):
            table = (
                shares.pivot_table(
                    index=["dimension", "indicator"],
                    columns="status",
                    values="n",
                    aggfunc="sum",
                )
                .reindex(columns=order)
                .astype(int)
                .reset_index()
            )
            st.dataframe(table, use_container_width=True, hide_index=True)


def render_ai_trust_choropleth(
    trust_gov_df: pd.DataFrame,
    trust_comp_df: pd.DataFrame,
    ai_env_trust_df: pd.DataFrame,
    job_sec_df: pd.DataFrame,
) -> None:
    st.subheader("How much do people trust AI around the world?")

    datasets = {
        "Trust in Government to Implement AI Guardrails": (
            trust_gov_df,
            "Agree",
            "Agree (%)",
        ),
        "Trust in Companies to Ensure Data Privacy": (
            trust_comp_df,
            "Agree",
            "Agree (%)",
        ),
        "Benefits from AI outweigh the environmental costs": (
            ai_env_trust_df,
            "Agree",
            "Agree (%)",
        ),
        "Job Security Under AI": (
            job_sec_df,
            "Agree",
            "Agree (%)",
        ),
    }

    choice = st.selectbox(
        "Select survey question", list(datasets.keys()), key="trust_choropleth_choice"
    )
    source_df, value_col, value_title = datasets[choice]

    if (
        not isinstance(source_df, pd.DataFrame)
        or source_df.empty
        or value_col not in source_df.columns
        or "Country" not in source_df.columns
    ):
        st.warning("No data to display.")
        return

    overrides = {"Türkiye": "TUR", "Great Britain": "GBR", "South Korea": "KOR"}

    def to_iso3(name: str):
        if name in overrides:
            return overrides[name]
        try:
            return pycountry.countries.lookup(name).alpha_3
        except LookupError:
            return None

    df = source_df.copy()
    df["Country"] = df["Country"].astype(str).str.strip()
    df["value"] = pd.to_numeric(
        df[value_col].astype(str).str.replace("%", "", regex=False).str.strip(),
        errors="coerce",
    )

    is_average = df["Country"].str.contains("average", case=False)
    average_row = df[is_average & df["value"].notna()]
    average_value = int(average_row["value"].iloc[0]) if not average_row.empty else None

    df = df[~is_average].dropna(subset=["value"])
    df["value"] = df["value"].round().astype(int)
    df["iso3"] = df["Country"].map(to_iso3)

    unmatched = df.loc[df["iso3"].isna(), "Country"].tolist()
    df = df.dropna(subset=["iso3"])

    if df.empty:
        st.warning("No countries could be matched to the map.")
        return

    if unmatched:
        st.warning(f"Could not place on the map: {', '.join(unmatched)}")

    fig = px.choropleth(
        df,
        locations="iso3",
        color="value",
        hover_name="Country",
        hover_data={"iso3": False, "value": ":d"},
        labels={"value": value_title},
        color_continuous_scale="Teal",
        range_color=(int(df["value"].min()), int(df["value"].max())),
    )

    fig.update_geos(
        projection_type="equal earth",
        showframe=False,
        showcoastlines=False,
        showcountries=True,
        countrycolor="#ffffff",
        showland=True,
        landcolor="rgba(154, 165, 177, 0.25)",
        showocean=False,
        showlakes=False,
        bgcolor="rgba(0,0,0,0)",
    )

    fig.update_layout(
        title={"text": f"{choice} ({value_title})", "x": 0.5, "xanchor": "center"},
        height=500,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar={
            "title": value_title,
            "orientation": "h",
            "y": -0.05,
            "yanchor": "top",
            "x": 0.5,
            "xanchor": "center",
            "len": 0.5,
            "thickness": 12,
            "tickformat": "d",
        },
    )

    top = df.loc[df["value"].idxmax()]
    bottom = df.loc[df["value"].idxmin()]
    caption = (
        f"Share of respondents in {len(df)} countries who answered {value_col.lower()}. "
        f"{top['Country']} is highest at {int(top['value'])}% and "
        f"{bottom['Country']} is lowest at {int(bottom['value'])}%. "
    )
    if average_value is not None:
        caption += f"The survey-wide average is {average_value}%. "
    caption += "Countries in grey were not surveyed. Source: [Ipsos AI Monitor](https://www.ipsos.com/)."

    with st.container():
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": True, "displaylogo": False},
        )
        st.caption(caption, text_alignment="center")


def render_syco_effects(study2_df: pd.DataFrame, study3_df: pd.DataFrame) -> None:
    st.subheader("What does flattering AI do to the people who use it?")
    st.markdown(
        "**Question:** After one conversation, how does a sycophantic AI change what people think "
        "of their own behaviour, their willingness to make amends, and their opinion of the AI itself?"
    )

    outcomes = {
        "rightorwrong": ("Felt they were in the right", "Effect on judgement"),
        "repair_score": ("Willing to repair the conflict", "Effect on judgement"),
        "trust_score": ("Trust in the AI", "Opinion of the AI"),
        "return_likelihood": ("Would use the AI again", "Opinion of the AI"),
        "response_quality": ("Rated the response as high quality", "Opinion of the AI"),
    }
    study_colors = {"Study 2": "#0e7490", "Study 3": "#f2b134"}

    def prepare(df, study):
        if not isinstance(df, pd.DataFrame) or df.empty:
            return None
        out = df.copy()
        if "is_syco" in out.columns:
            out["syco"] = out["is_syco"].astype(str).str.lower() == "true"
        elif "Condition" in out.columns:
            out["syco"] = out["Condition"].astype(str).str.lower() == "syco"
        else:
            return None
        out["study"] = study
        return out

    def summarise(df):
        rows = []
        for col, (label, group) in outcomes.items():
            if col not in df.columns:
                continue
            values = pd.to_numeric(df[col], errors="coerce")
            treated = values[df["syco"]].dropna()
            control = values[~df["syco"]].dropna()
            if len(treated) < 2 or len(control) < 2:
                continue
            effect = treated.mean() - control.mean()
            se = np.sqrt(
                treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)
            )
            rows.append(
                {
                    "study": df["study"].iloc[0],
                    "outcome": label,
                    "group": group,
                    "effect": effect,
                    "lo": effect - 1.96 * se,
                    "hi": effect + 1.96 * se,
                    "n_syco": len(treated),
                    "n_control": len(control),
                }
            )
        return rows

    prepared = [
        p
        for p in (prepare(study2_df, "Study 2"), prepare(study3_df, "Study 3"))
        if p is not None
    ]
    if not prepared:
        st.warning("No data to display.")
        return

    effects = pd.DataFrame([row for p in prepared for row in summarise(p)])
    if effects.empty:
        st.warning("No outcome columns found in the data.")
        return

    dark = st.context.theme.type == "dark"
    fg, muted = ("#d9e4ef", "#7d8fa3") if dark else ("#1f2d3d", "#5b6b7d")
    grid, domain = "rgba(150, 180, 210, 0.1)", "rgba(150, 180, 210, 0.4)"

    studies = [s for s in study_colors if s in effects["study"].unique()]
    limit = float(
        np.ceil(max(effects["lo"].abs().max(), effects["hi"].abs().max()) * 2) / 2 + 0.5
    )
    x_scale = alt.Scale(domain=[-limit, limit])

    def panel(group, show_axis_title):
        data = effects[effects["group"] == group]
        order = data.drop_duplicates("outcome")["outcome"].tolist()
        y = alt.Y(
            "outcome:N",
            sort=order,
            title=None,
            axis=alt.Axis(labelLimit=260, minExtent=260),
        )
        x_title = (
            "Sycophantic minus non-sycophantic AI (points on a 1 to 7 scale)"
            if show_axis_title
            else None
        )
        color = alt.Color(
            "study:N",
            title=None,
            scale=alt.Scale(domain=studies, range=[study_colors[s] for s in studies]),
            legend=alt.Legend(orient="bottom") if show_axis_title else None,
        )

        zero = (
            alt.Chart(pd.DataFrame({"zero": [0]}))
            .mark_rule(color=muted, strokeDash=[4, 4])
            .encode(x=alt.X("zero:Q", scale=x_scale))
        )
        spans = (
            alt.Chart(data)
            .mark_rule(strokeWidth=3)
            .encode(
                x=alt.X(
                    "lo:Q",
                    scale=x_scale,
                    title=x_title,
                    axis=alt.Axis(tickMinStep=1),
                ),
                x2="hi:Q",
                y=y,
                yOffset="study:N",
                color=color,
            )
        )
        points = (
            alt.Chart(data)
            .mark_point(filled=True, size=110, opacity=1)
            .encode(
                x=alt.X("effect:Q", scale=x_scale),
                y=y,
                yOffset="study:N",
                color=color,
                tooltip=[
                    alt.Tooltip("study:N", title="Study"),
                    alt.Tooltip("outcome:N", title="Outcome"),
                    alt.Tooltip("effect:Q", title="Difference", format="+.2f"),
                    alt.Tooltip("lo:Q", title="95% CI low", format="+.2f"),
                    alt.Tooltip("hi:Q", title="95% CI high", format="+.2f"),
                    alt.Tooltip("n_syco:Q", title="n sycophantic"),
                    alt.Tooltip("n_control:Q", title="n non-sycophantic"),
                ],
            )
        )
        text_right = (
            alt.Chart(data)
            .mark_text(align="left", dx=9, fontSize=12, fontWeight="bold", color=fg)
            .transform_filter(alt.datum.effect >= 0)
            .encode(
                x=alt.X("hi:Q", scale=x_scale),
                y=y,
                yOffset="study:N",
                text=alt.Text("effect:Q", format="+.2f"),
            )
        )
        text_left = (
            alt.Chart(data)
            .mark_text(align="right", dx=-9, fontSize=12, fontWeight="bold", color=fg)
            .transform_filter(alt.datum.effect < 0)
            .encode(
                x=alt.X("lo:Q", scale=x_scale),
                y=y,
                yOffset="study:N",
                text=alt.Text("effect:Q", format="+.2f"),
            )
        )
        return (
            alt.layer(zero, spans, points, text_right, text_left)
            .properties(
                width="container",
                height=70 * len(order),
                background="transparent",
                title=alt.TitleParams(group, anchor="start", fontSize=14),
            )
            .configure_view(strokeWidth=0)
            .configure_title(color=fg)
            .configure_axis(
                grid=True,
                gridColor=grid,
                domainColor=domain,
                tickColor=domain,
                labelColor=muted,
                titleColor=muted,
            )
            .configure_legend(labelColor=muted, titleColor=muted)
        )

    groups = list(dict.fromkeys(effects["group"]))
    charts = [panel(g, i == len(groups) - 1) for i, g in enumerate(groups)]

    def value(study, label, field="effect"):
        row = effects[(effects["study"] == study) & (effects["outcome"] == label)]
        return float(row[field].iloc[0]) if not row.empty else None

    def phrase(label):
        return " and ".join(
            f"{value(s, label):+.2f} in {s}"
            for s in studies
            if value(s, label) is not None
        )

    sizes = ", ".join(
        f"{s} N={int(value(s, 'Felt they were in the right', 'n_syco') + value(s, 'Felt they were in the right', 'n_control'))}"
        for s in studies
        if value(s, "Felt they were in the right") is not None
    )

    caption = (
        "Difference in mean rating (1 to 7 scale) between people who chatted with a sycophantic AI and those who "
        "chatted with a non-sycophantic one, with 95% confidence intervals. "
        f"Feeling in the right shifted by {phrase('Felt they were in the right')}; "
        f"willingness to repair the conflict by {phrase('Willing to repair the conflict')}; "
        f"trust in the AI by {phrase('Trust in the AI')} ({sizes}). "
        "The AI was instructed to be sycophantic or not, and outcomes are self-reported after a single interaction. "
        "Source: [Cheng et al., 2025](https://arxiv.org/abs/2510.01395)."
    )

    with st.container():
        for chart in charts:
            st.altair_chart(chart, use_container_width=True, theme=None)
        st.caption(caption, text_alignment="center")

        if st.toggle("Show data", key="syco_effects_table"):
            table = effects.rename(
                columns={
                    "study": "Study",
                    "outcome": "Outcome",
                    "group": "Group",
                    "effect": "Difference",
                    "lo": "95% CI low",
                    "hi": "95% CI high",
                    "n_syco": "n sycophantic",
                    "n_control": "n non-sycophantic",
                }
            ).round(2)
            st.dataframe(table, use_container_width=True, hide_index=True)


def render_syco_rightness_distribution(
    study2_df: pd.DataFrame, study3_df: pd.DataFrame
) -> None:
    st.subheader("Does one conversation change how right people feel?")
    st.markdown(
        "**Question:** Beyond the average, how does the whole spread of 'I was in the right' ratings "
        "shift after talking to a sycophantic AI?"
    )

    def prepare(df, study):
        if (
            not isinstance(df, pd.DataFrame)
            or df.empty
            or "rightorwrong" not in df.columns
        ):
            return None
        out = df.copy()
        if "is_syco" in out.columns:
            out["syco"] = out["is_syco"].astype(str).str.lower() == "true"
        elif "Condition" in out.columns:
            out["syco"] = out["Condition"].astype(str).str.lower() == "syco"
        else:
            return None
        out["rating"] = pd.to_numeric(out["rightorwrong"], errors="coerce")
        out = out[out["rating"].between(1, 7)]
        out["rating"] = out["rating"].round().astype(int)
        out["study"] = study
        return out

    prepared = [
        p
        for p in (prepare(study2_df, "Study 2"), prepare(study3_df, "Study 3"))
        if p is not None
    ]
    if not prepared:
        st.warning("No data to display.")
        return

    dark = st.context.theme.type == "dark"
    fg, muted = ("#d9e4ef", "#7d8fa3") if dark else ("#1f2d3d", "#5b6b7d")
    grid, domain = "rgba(150, 180, 210, 0.1)", "rgba(150, 180, 210, 0.4)"

    rows = []
    order = []
    high_share = {}
    for p in prepared:
        study = p["study"].iloc[0]
        for flag, name in ((False, "Non-sycophantic AI"), (True, "Sycophantic AI")):
            sub = p[p["syco"] == flag]
            if sub.empty:
                continue
            group = f"{study} · {name} (mean {sub['rating'].mean():.1f})"
            order.append(group)
            high_share[(study, flag)] = float((sub["rating"] >= 6).mean())
            counts = sub["rating"].value_counts().reindex(range(1, 8), fill_value=0)
            cumulative = 0.0
            for rating, n in counts.items():
                share = n / len(sub)
                rows.append(
                    {
                        "group": group,
                        "rating": int(rating),
                        "n": int(n),
                        "share": share,
                        "start": cumulative,
                        "end": cumulative + share,
                        "mid": cumulative + share / 2,
                        "label": f"{share:.0%}" if share >= 0.07 else "",
                    }
                )
                cumulative += share

    shares = pd.DataFrame(rows)

    base = alt.Chart(shares).encode(
        y=alt.Y("group:N", sort=order, title=None, axis=alt.Axis(labelLimit=340))
    )

    bars = base.mark_bar(height=36).encode(
        x=alt.X(
            "start:Q",
            title="Share of participants",
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%"),
        ),
        x2="end:Q",
        color=alt.Color(
            "rating:O",
            title="Rating (1 to 7)",
            scale=alt.Scale(scheme="tealblues", domain=list(range(1, 8))),
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            alt.Tooltip("group:N", title="Group"),
            alt.Tooltip("rating:O", title="Rating"),
            alt.Tooltip("n:Q", title="Participants", format=",d"),
            alt.Tooltip("share:Q", title="Share", format=".1%"),
        ],
    )

    labels = base.mark_text(fontSize=12, fontWeight="bold").encode(
        x="mid:Q",
        text="label:N",
        color=alt.condition(
            alt.datum.rating >= 5, alt.value("#ffffff"), alt.value("#0b1118")
        ),
    )

    chart = (
        (bars + labels)
        .properties(
            title=alt.TitleParams(
                "How Right People Felt After Talking to an AI",
                anchor="middle",
            ),
            height=max(200, 58 * len(order)),
            background="transparent",
        )
        .configure_view(strokeWidth=0)
        .configure_title(color=fg)
        .configure_axis(
            grid=True,
            gridColor=grid,
            domainColor=domain,
            tickColor=domain,
            labelColor=muted,
            titleColor=muted,
        )
        .configure_legend(labelColor=muted, titleColor=muted)
    )

    studies = list(dict.fromkeys(p["study"].iloc[0] for p in prepared))
    comparisons = "; ".join(
        f"{s}: {high_share[(s, True)]:.0%} with the sycophantic AI versus {high_share[(s, False)]:.0%} with the non-sycophantic one"
        for s in studies
        if (s, True) in high_share and (s, False) in high_share
    )
    caption = (
        "Ratings run from 1 to 7, with higher meaning more convinced they were in the right. "
        f"Share rating themselves 6 or 7 — {comparisons}. "
        "The AI was instructed to be sycophantic or not, and ratings are self-reported after a single conversation. "
        "Source: [Cheng et al., 2025](https://arxiv.org/abs/2510.01395)."
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True, theme=None)
        st.caption(caption, text_alignment="center")

        if st.toggle("Show data", key="syco_distribution_table"):
            table = shares[["group", "rating", "n", "share"]].rename(
                columns={
                    "group": "Group",
                    "rating": "Rating",
                    "n": "Participants",
                    "share": "Share",
                }
            )
            table["Share"] = table["Share"].round(3)
            st.dataframe(table, use_container_width=True, hide_index=True)


def render_syco_scenario_effects(
    study2_df: pd.DataFrame, study3_df: pd.DataFrame
) -> None:
    st.subheader("Is the effect specific to one kind of conflict?")
    st.markdown(
        "**Question:** Does a sycophantic AI shift people's views in the same direction whatever "
        "the conflict they described?"
    )

    studies = {"Study 2": study2_df, "Study 3": study3_df}
    selected = st.selectbox(
        "Select study", list(studies.keys()), key="syco_scenario_study"
    )
    df = studies[selected]

    required = {"scenarioNum", "rightorwrong", "repair_score"}
    if not isinstance(df, pd.DataFrame) or df.empty or not required <= set(df.columns):
        st.warning("No data to display.")
        return

    scenario_labels = {
        "exclusion": "Excluding someone",
        "relationship": "Relationship boundaries",
        "others": "Involving yourself in others' business",
        "uncomfortable": "Making someone uncomfortable",
    }
    outcomes = {
        "rightorwrong": ("Felt they were in the right", "#0e7490"),
        "repair_score": ("Willing to repair the conflict", "#f2b134"),
    }

    def scenario_name(value):
        key = str(value).strip().lower()
        if key in scenario_labels:
            return scenario_labels[key]
        try:
            return f"Scenario {int(float(value))}"
        except ValueError:
            return str(value)

    def effect_row(sub, col, scenario):
        values = pd.to_numeric(sub[col], errors="coerce")
        treated = values[sub["syco"]].dropna()
        control = values[~sub["syco"]].dropna()
        if len(treated) < 2 or len(control) < 2:
            return None
        effect = treated.mean() - control.mean()
        se = np.sqrt(
            treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)
        )
        return {
            "scenario": scenario,
            "outcome": outcomes[col][0],
            "effect": effect,
            "lo": effect - 1.96 * se,
            "hi": effect + 1.96 * se,
            "n": len(treated) + len(control),
        }

    prepared = df.copy()
    if "is_syco" in prepared.columns:
        prepared["syco"] = prepared["is_syco"].astype(str).str.lower() == "true"
    elif "Condition" in prepared.columns:
        prepared["syco"] = prepared["Condition"].astype(str).str.lower() == "syco"
    else:
        st.error("No condition column found in the data.")
        return
    prepared["scenario"] = prepared["scenarioNum"].map(scenario_name)

    rows = []
    scenario_order = sorted(prepared["scenario"].dropna().unique().tolist())
    for col in outcomes:
        for scenario in scenario_order:
            row = effect_row(prepared[prepared["scenario"] == scenario], col, scenario)
            if row:
                rows.append(row)
        overall = effect_row(prepared, col, "All scenarios")
        if overall:
            rows.append(overall)

    effects = pd.DataFrame(rows)
    if effects.empty:
        st.warning("Not enough data to compare scenarios.")
        return

    scenario_order = scenario_order + ["All scenarios"]

    dark = st.context.theme.type == "dark"
    fg, muted = ("#d9e4ef", "#7d8fa3") if dark else ("#1f2d3d", "#5b6b7d")
    grid, domain = "rgba(150, 180, 210, 0.1)", "rgba(150, 180, 210, 0.4)"

    limit = float(
        np.ceil(max(effects["lo"].abs().max(), effects["hi"].abs().max()) * 2) / 2 + 0.5
    )
    x_scale = alt.Scale(domain=[-limit, limit])

    def panel(col, show_labels):
        label, colour = outcomes[col]
        data = effects[effects["outcome"] == label]
        y_axis = (
            alt.Axis(labelLimit=260)
            if show_labels
            else alt.Axis(labels=False, ticks=False, domain=False)
        )
        y = alt.Y("scenario:N", sort=scenario_order, title=None, axis=y_axis)

        zero = (
            alt.Chart(pd.DataFrame({"zero": [0]}))
            .mark_rule(color=muted, strokeDash=[4, 4])
            .encode(x=alt.X("zero:Q", scale=x_scale))
        )
        spans = (
            alt.Chart(data)
            .mark_rule(strokeWidth=3, color=colour)
            .encode(
                x=alt.X(
                    "lo:Q",
                    scale=x_scale,
                    title="Sycophantic minus non-sycophantic (points)",
                ),
                x2="hi:Q",
                y=y,
            )
        )
        points = (
            alt.Chart(data)
            .mark_point(filled=True, size=110, color=colour, opacity=1)
            .encode(
                x=alt.X("effect:Q", scale=x_scale),
                y=y,
                tooltip=[
                    alt.Tooltip("scenario:N", title="Scenario"),
                    alt.Tooltip("effect:Q", title="Difference", format="+.2f"),
                    alt.Tooltip("lo:Q", title="95% CI low", format="+.2f"),
                    alt.Tooltip("hi:Q", title="95% CI high", format="+.2f"),
                    alt.Tooltip("n:Q", title="Participants"),
                ],
            )
        )
        text_right = (
            alt.Chart(data)
            .mark_text(align="left", dx=9, fontSize=12, fontWeight="bold", color=fg)
            .transform_filter(alt.datum.effect >= 0)
            .encode(
                x=alt.X("hi:Q", scale=x_scale),
                y=y,
                text=alt.Text("effect:Q", format="+.2f"),
            )
        )
        text_left = (
            alt.Chart(data)
            .mark_text(align="right", dx=-9, fontSize=12, fontWeight="bold", color=fg)
            .transform_filter(alt.datum.effect < 0)
            .encode(
                x=alt.X("lo:Q", scale=x_scale),
                y=y,
                text=alt.Text("effect:Q", format="+.2f"),
            )
        )
        return (
            alt.layer(zero, spans, points, text_right, text_left)
            .properties(
                width="container",
                height=42 * len(scenario_order),
                background="transparent",
                title=alt.TitleParams(label, anchor="start", fontSize=14),
            )
            .configure_view(strokeWidth=0)
            .configure_title(color=fg)
            .configure_axis(
                grid=True,
                gridColor=grid,
                domainColor=domain,
                tickColor=domain,
                labelColor=muted,
                titleColor=muted,
            )
        )
        
    def spread(label):
        sub = effects[
            (effects["outcome"] == label) & (effects["scenario"] != "All scenarios")
        ]
        return sub, f"{sub['effect'].min():+.2f} to {sub['effect'].max():+.2f}"

    right_sub, right_range = spread("Felt they were in the right")
    repair_sub, repair_range = spread("Willing to repair the conflict")

    caption = (
        f"Difference in mean rating (1 to 7 scale) between sycophantic and non-sycophantic AI conditions in {selected}, "
        "by the type of conflict people described, with 95% confidence intervals. "
        f"Across {len(right_sub)} scenarios, feeling in the right shifted by {right_range} and willingness to repair by {repair_range}. "
    )
    if (right_sub["lo"] > 0).all() or (right_sub["hi"] < 0).all():
        caption += "For feeling in the right, every scenario's interval excludes zero. "
    if (repair_sub["lo"] > 0).all() or (repair_sub["hi"] < 0).all():
        caption += (
            "For willingness to repair, every scenario's interval excludes zero. "
        )
    caption += "Source: [Cheng et al., 2025](https://arxiv.org/abs/2510.01395)."

    with st.container():
        left, right = st.columns([1.5, 1], gap="small")
        with left:
            st.altair_chart(panel("rightorwrong", True), use_container_width=True, theme=None)
        with right:
            st.altair_chart(panel("repair_score", False), use_container_width=True, theme=None)

        st.caption(caption, text_alignment="center")

        if st.toggle("Show data", key="syco_scenario_table"):
            table = effects.rename(
                columns={
                    "scenario": "Scenario",
                    "outcome": "Outcome",
                    "effect": "Difference",
                    "lo": "95% CI low",
                    "hi": "95% CI high",
                    "n": "Participants",
                }
            ).round(2)
            st.dataframe(table, use_container_width=True, hide_index=True)


import pandas as pd


def _latest_date(df: pd.DataFrame, cols: list[str]) -> str | None:
    """Latest parsed date across the given columns, or None if unavailable."""
    dates = []
    for c in cols:
        if c in df.columns:
            dates.append(pd.to_datetime(df[c], errors="coerce", utc=True).max())
    dates = [d for d in dates if pd.notna(d)]
    return max(dates).strftime("%Y-%m-%d") if dates else None


def render_sources(data_list: list[pd.DataFrame]) -> None:
    """
    Expects data_list in this order:
      0 ai_reports, 1 ai_incidents, 2 human_validation, 3 ai_validation,
      4 soft_eng_sat, 5 soft_eng_trust, 6 gmf_class, 7 frameworks,
      8 classifications, 9 gov_trust_ipsos, 10 comp_trust_ipsos,
      11 ai_env_trust_ipsos, 12 job_sec_trust_ipsos, 13 syco_study2, 14 syco_study3
    """
    (
        ai_reports,
        ai_inc,
        _human,
        _ai_val,
        _sat,
        _trust,
        _gmf,
        _frameworks,
        _classifications,
        _gov,
        _comp,
        _env,
        _job,
        _syco2,
        _syco3,
    ) = data_list

    incidents_latest = _latest_date(ai_inc, ["date"]) or "n/a"
    reports_latest = (
        _latest_date(ai_reports, ["date_published", "date_submitted"]) or "n/a"
    )

    rows = [
        {
            "Dataset": "AI Incident Database: incidents",
            "Latest observation": incidents_latest,
            "License": "CC BY-SA 4.0",
        },
        {
            "Dataset": "AI Incident Database: GMF classifications",
            "Latest observation": incidents_latest,
            "License": "CC BY-SA 4.0",
        },
        {
            "Dataset": "AI Incident Database: reports (dates only)",
            "Latest observation": reports_latest,
            "License": "Not covered by AIID's CC BY-SA grant (text field excluded); contact RAIC",
        },
        {
            "Dataset": "Scientometric LLM Ethics Benchmark: human validation + AI judge scores (universe-szw)",
            "Latest observation": "2026 release",
            "License": "MIT",
        },
        {
            "Dataset": "Global AI Adoption & Workforce Impact Survey 24-26 (Kaggle, M. K. Suraj)",
            "Latest observation": "2026-04-07 (last updated)",
            "License": "Apache 2.0",
        },
        {
            "Dataset": "Global Index on Responsible AI (GIRAI), 2nd edition",
            "Latest observation": "Sep 2025 (evidence cut-off), published 2026",
            "License": "CC BY 4.0",
        },
        {
            "Dataset": "Ipsos AI Monitor 2025 (trust in government)",
            "Latest observation": "2025-04-04",
            "License": "Ipsos",
        },
        {
            "Dataset": "Ipsos AI Monitor 2026 (trust in companies, environment, job security)",
            "Latest observation": "2026-04-03",
            "License": "Ipsos",
        },
        {
            "Dataset": "Sycophancy studies 2 & 3 (Cheng et al., Science 2026; OSF)",
            "Latest observation": "2026-03-26",
            "License": "paper cited as CC BY 4.0",
        },
    ]

    st.table(pd.DataFrame(rows))


def render_data_limitations() -> None:
    st.markdown("""
    - Most data used involve surveys and may not reflect actual data or real events. This counts as self-reported and short-term.
    - AIID reportings may not include incidents that are not reported such as attacks endured by firms not being disclosed publicly and that only incidents that editors classified under the GMF taxonomy appear in that chart.
    - The trust maps use online surveys from different years. Ipsos surveyed adults under 75 online (30 countries in 2025, 32 in 2026). Online samples under-represent people with limited internet access, so results are not fully representative of each country. Government trust comes from the 2025 edition and the other questions from 2026.
    - The ethics benchmark experiments on constructed prompts, but no connections to real incident data. Human validation covers a subset of items and the AI judges share a family with some of the models they score.
    """)
