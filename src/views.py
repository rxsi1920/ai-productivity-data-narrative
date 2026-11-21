############################################################################################################################
# --------------------------------------- MORAL DEGRADATION ----------------------------------------------------------------
############################################################################################################################

import ast
import functools
import re

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import pycountry
import streamlit as st


def _shares_line(counts) -> str:
    """Every answer's share of respondents as visible text, e.g. "Low 33% · Moderate 34% · High 33% (n = 12,000)"."""
    if counts is None or len(counts) == 0:
        return ""
    total = int(counts.sum())
    parts = " · ".join(f"{k} {v / total:.0%}" for k, v in counts.items())
    return f"{parts} (n = {total:,})"


# Date the moral-degradation files in data/raw/ were downloaded (first committed 16 Nov 2026; latest report 15 Nov 2026).
LAST_REFRESH = "16 Nov 2026"
DATE_LABEL = "Latest observation"
DOWNLOAD_LABEL = "Download CSV"
EMPTY_TEXT = "No data matches the current selection."
_DATE_COLUMNS = ["date_published", "date", "date_submitted", "published_date"]

SOURCES = {
    "aiid": (
        "AI Incident Database",
        "Responsible AI Collaborative",
        "https://incidentdatabase.ai/",
    ),
    "ethics": (
        "Scientometric LLM Ethics Benchmark",
        "universe-szw",
        "https://github.com/universe-szw/scientometric-llm-ethics-benchmark",
    ),
    "kaggle": (
        "Global AI Adoption & Workforce Impact Survey 24-26",
        "M. K. Suraj (Kaggle)",
        "https://www.kaggle.com/datasets/meruvakodandasuraj/global-ai-adoption-and-workforce-impact-survey-24-26",
    ),
    "girai": (
        "Global Index on Responsible AI",
        "Global Center on AI Governance",
        "https://www.global-index.ai/",
    ),
    "ipsos": ("Ipsos AI Monitor", "Ipsos", "https://www.ipsos.com/"),
    "cheng": (
        "Sycophantic AI Decreases Prosocial Intentions and Promotes Dependence",
        "Cheng et al. (Science, 2026)",
        "https://arxiv.org/abs/2510.01395",
    ),
}


def _view(view_id: str):
    """Render the wrapped function inside a container keyed by the view id."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with st.container(key=view_id):
                return fn(*args, **kwargs)

        return wrapper

    return decorator


def _source(*ids: str, url: str | None = None) -> str:
    parts = []
    for i, sid in enumerate(ids):
        title, publisher, default = SOURCES[sid]
        parts.append(f"[{title}]({url if url and i == 0 else default}), {publisher}")
    return "Source: " + "; ".join(parts) + "."


def _footer(unit: str, frame=None) -> None:
    st.caption(f"Unit: {unit}", text_alignment="center")
    latest = (
        _latest_date(frame, _DATE_COLUMNS) if isinstance(frame, pd.DataFrame) else None
    )
    st.caption(
        f"{DATE_LABEL}: {latest}" if latest else f"{DATE_LABEL}: not applicable",
        text_alignment="center",
    )


def _download(frame, key: str, file_name: str) -> None:
    if not isinstance(frame, pd.DataFrame):
        return
    st.download_button(
        DOWNLOAD_LABEL,
        frame.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=key,
    )


def _empty(frame, key: str, file_name: str) -> None:
    st.info(EMPTY_TEXT)
    _download(frame, key, file_name)


@_view("reports_timeseries")
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

    choice = st.selectbox(
        "Select data", list(datasets.keys()), index=0, key="reports_dataset"
    )
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
        key="reports_forecast_year",
    )
    show_fan = st.toggle("Show fan", value=True, key="reports_show_fan")

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

    # The count above each bar, so values are readable without hovering.
    bar_labels = base.mark_text(dy=-9, fontSize=10, color="#1f2d3d").encode(
        text=alt.Text("count:Q", format=",")
    )

    layers = [bars, line, bar_labels]
    if show_fan:
        layers = [band90, band50, bars, line, median_line, bar_labels]

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

    def _count_in(year: int) -> int:
        hit = yearly_counts.loc[yearly_counts["year"].astype(int) == year, "count"]
        return int(hit.iloc[0]) if len(hit) else 0

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        fan_note = (
            "The shaded fan shows the 50% and 90% forecast ranges projected from the selected year. "
            if show_fan
            else ""
        )
        st.caption(
            f"{label} per year rose from {_count_in(2015):,} in 2015 to {_count_in(2025):,} in 2025. "
            "A rising count can reflect more incidents, more media attention or more editors logging them, "
            "so it is an indicator of harm, not a measure of it. "
            f"{fan_note}"
            + _source("aiid", url="https://incidentdatabase.ai/apps/incidents/"),
            text_alignment="center",
        )
        _footer(f"{unit} per year", source_df)
        _download(
            source_df.loc[df.index],
            "reports_download",
            f"ai_{unit}.csv",
        )


@_view("gmf_failures")
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
        "and shares do not sum to 100%. "
        + _source("aiid", url="https://incidentdatabase.ai/taxonomies/gmf/")
    )

    st.altair_chart(chart, use_container_width=True, theme=None)
    st.caption(caption, text_alignment="center")
    _footer("incidents", data)
    _download(data, "gmf_download", "gmf_failures.csv")


def render_() -> None:
    st.header("2. AI's Self-awareness of Morality")


def render_moral_summary(data: pd.DataFrame, label: str = "Our answer") -> None:

    # Latest full year in the data. Counted by publication date, the same as the section 1 chart and Home.
    last_year = 2025
    published = pd.to_datetime(data["date_published"], errors="coerce", utc=True)
    total_last_year = f"{(published.dt.year == last_year).sum():,}"

    with st.container(key="moral_answer", border=True):
        st.markdown(f"""
            **{label}: Early on, AI weakens moral judgement and safeguards are thin, but no provable cause.** In controlled experiments, people who talked to a flattering AI felt more in the right and were less willing to repair the conflict. Around that, it was reported that AI incidents reached {total_last_year} in {last_year} and are still accelerating, models differ widely in how closely their moral scores match human validation, and only a minority of countries have a binding national framework. The effect on judgement is measured in surveys, the failures and gaps are indicators, and more importantly there is no time-series data available which indicates erosion of moral judgement.
        """)


@_view("human_validation_scores")
def render_human_validation_scores(data: pd.DataFrame) -> None:
    st.subheader("Human validation of AI moral scores")
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
    selected_dimension = st.selectbox(
        "Select Ethical/Safety Dimension", dimensions, key="human_validation_dimension"
    )

    if selected_dimension != "Overall":
        df = df[df["dimension"] == selected_dimension]

    if df.empty:
        _empty(df, "human_validation_download", "human_validation_scores.csv")
        return

    selected_rows = df.copy()
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
            f"Each dot is one model: its mean score from human raters (x) and from GPT-5.5 as judge (y), on a 0–10 scale. "
            f"Human means range from {agg_df['human_mean_score'].min():.2f} ({agg_df.loc[agg_df['human_mean_score'].idxmin(), 'evaluated_model_name']}) "
            f"to {agg_df['human_mean_score'].max():.2f} ({agg_df.loc[agg_df['human_mean_score'].idxmax(), 'evaluated_model_name']}), "
            f"and the two scores move together (r = {agg_df['human_mean_score'].corr(agg_df['gpt55_score']):+.2f}, {len(agg_df)} models). "
            "A lower score means the model's answers were rated less safe or less aligned on the benchmark's test prompts; "
            "it does not show that a model's behaviour gets worse over time. "
            + _source(
                "ethics",
                url="https://github.com/universe-szw/scientometric-llm-ethics-benchmark/blob/main/scoring_results/human_validation_scores_merged.csv",
            ),
            text_alignment="center",
        )
        _footer("score (0-10)", data)
        _download(
            selected_rows, "human_validation_download", "human_validation_scores.csv"
        )


@_view("judge_agreement_heatmap")
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

    st.subheader("Do AI judges agree on how ethically models behave?")
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
        _empty(df, "judge_heatmap_download", "judge_agreement.csv")
        return

    selected_rows = df.copy()

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
    caption += _source("ethics")

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(caption, text_alignment="center")
        _footer("mean score (0-10)", data)
        _download(selected_rows, "judge_heatmap_download", "judge_agreement.csv")


@_view("trust_chart")
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
        f"Average trust level: {trust_level}<br>{_shares_line(counts)}<br>{_source('kaggle')}",
        text_alignment="center",
        unsafe_allow_html=True,
    )
    _footer("respondents by trust level", data)
    _download(data, "trust_download", "ai_trust.csv")


@_view("ai_replacement")
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
        f"Average answer: {fear_level}<br>{_shares_line(counts)}<br>"
        + _source("kaggle"),
        text_alignment="center",
        unsafe_allow_html=True,
    )
    _footer("respondents by answer", data)
    _download(data, "ai_replacement_download", "ai_job_replacement_fear.csv")


@_view("ai_framework_coverage")
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
        _empty(df, "framework_download", "ai_frameworks.csv")
        return

    order = ["Binding", "Non-binding", "Draft only", "No framework"]
    # "No framework" is a light grey so it stays distinct from "Non-binding" under colour-vision deficiency.
    colors = ["#0e7490", "#67b7d1", "#f2b134", "#d5d9de"]
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
        # Separate colour scales, so the % labels use text_colors instead of the bar colours (which hid them).
        .resolve_scale(color="independent")
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
        + _source("girai")
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(caption, text_alignment="center")
        _footer("share of countries (%)", frameworks)
        _download(df, "framework_download", "ai_frameworks.csv")

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


@_view("ai_trust_choropleth")
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

    # Print each surveyed country's value on the map, so it can be read without hovering.
    fig.add_scattergeo(
        locations=df["iso3"],
        text=df["value"].astype(str),
        mode="text",
        textfont={"size": 10, "color": "#0b1118"},
        hoverinfo="skip",
        showlegend=False,
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
    caption += "Countries in grey were not surveyed. " + _source("ipsos")

    with st.container():
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": True, "displaylogo": False},
        )
        st.caption(caption, text_alignment="center")
        _footer("% of respondents who agree", source_df)
        _download(source_df, "trust_choropleth_download", "ai_trust_by_country.csv")


@_view("syco_effects")
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
        + _source("cheng")
    )

    with st.container():
        for chart in charts:
            st.altair_chart(chart, use_container_width=True, theme=None)
        st.caption(caption, text_alignment="center")
        _footer("points on a 1 to 7 scale", study2_df)
        _download(effects, "syco_effects_download", "syco_effects.csv")

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


@_view("syco_rightness_distribution")
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
        + _source("cheng")
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True, theme=None)
        st.caption(caption, text_alignment="center")
        _footer("share of participants (%)", study2_df)
        _download(
            shares[["group", "rating", "n", "share"]],
            "syco_distribution_download",
            "syco_rightness_distribution.csv",
        )

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


@_view("syco_scenario_effects")
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
    caption += _source("cheng")

    with st.container():
        left, right = st.columns([1.5, 1], gap="small")
        with left:
            st.altair_chart(
                panel("rightorwrong", True), use_container_width=True, theme=None
            )
        with right:
            st.altair_chart(
                panel("repair_score", False), use_container_width=True, theme=None
            )

        st.caption(caption, text_alignment="center")
        _footer("points on a 1 to 7 scale", df)
        _download(effects, "syco_scenario_download", "syco_scenario_effects.csv")

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
    st.caption(
        f"Last data refresh: {LAST_REFRESH}. Every number on this page is in, or computed from, "
        "the files in data/processed/."
    )


def render_data_limitations() -> None:
    st.markdown("""
    - Most data used involve surveys and may not reflect actual data or real events. This counts as self-reported and short-term.
    - AIID reportings may not include incidents that are not reported such as attacks endured by firms not being disclosed publicly and that only incidents that editors classified under the GMF taxonomy appear in that chart.
    - The trust maps use online surveys from different years. Ipsos surveyed adults under 75 online (30 countries in 2025, 32 in 2026). Online samples under-represent people with limited internet access, so results are not fully representative of each country. Government trust comes from the 2025 edition and the other questions from 2026.
    - The ethics benchmark experiments on constructed prompts, but no connections to real incident data. Human validation covers a subset of items and the AI judges share a family with some of the models they score.
    """)


def render_moral_decision(
    ai_reports_data: pd.DataFrame,
    human_validation_data: pd.DataFrame,
    frameworks_data: pd.DataFrame,
    gov_trust_ipsos_data: pd.DataFrame,
    syco_study2_data: pd.DataFrame,
    syco_study3_data: pd.DataFrame,
) -> None:
    FW_COUNTRY, FW_AREA, FW_STATUS, FW_BINDING = "country", "area", "status", "Binding"

    def safe(fn) -> str:
        try:
            return fn()
        except Exception:
            return "data not available"

    def syco() -> str:
        s2 = (
            syco_study2_data["is_syco"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "1.0"])
        )
        cond = syco_study3_data["Condition"].astype(str).str.lower()
        s3 = cond.str.contains("syco") & ~cond.str.contains("non")

        def gap(df, mask, col):
            return df.loc[mask, col].mean() - df.loc[~mask, col].mean()

        right = [
            gap(syco_study2_data, s2, "rightorwrong"),
            gap(syco_study3_data, s3, "rightorwrong"),
        ]
        repair = [
            gap(syco_study2_data, s2, "repair_score"),
            gap(syco_study3_data, s3, "repair_score"),
        ]
        return (
            f"After chatting with a flattering AI, people rated themselves "
            f"{sum(right) / 2:+.2f} points more in the right and "
            f"{sum(repair) / 2:+.2f} on willingness to repair "
            f"(vs a non-sycophantic AI, averaged over 2 studies)."
        )

    def validation() -> str:
        d = human_validation_data
        m = d.groupby("evaluated_model_name")["human_mean_score"].mean().sort_values()
        gap = (d["gpt55_score"] - d["human_mean_score"]).abs().mean()
        return (
            f"Mean human-validation score runs from {m.iloc[0]:.1f} ({m.index[0]}) "
            f"to {m.iloc[-1]:.1f} ({m.index[-1]}) across {len(m)} models; "
            f"GPT-5.5 as judge is off human scores by {gap:.1f} points on average."
        )

    def governance() -> str:
        fw = frameworks_data
        binding = fw["fr1_enforceability"].eq("Binding") | fw["fr2_enforceability"].eq(
            "Binding"
        )
        share = binding.groupby(fw["indicator"]).mean().sort_values()
        return (
            f"Share of {fw['country'].nunique()} countries with a binding framework: "
            f"{share.iloc[-1]:.0%} in {share.index[-1]} (best covered) "
            f"down to {share.iloc[0]:.0%} in {share.index[0]}."
        )

    def incidents() -> str:
        dates = pd.to_datetime(
            ai_reports_data["date_published"], errors="coerce"
        ).dropna()
        per_year = dates.dt.year.value_counts().sort_index()
        per_year = per_year[per_year.index < pd.Timestamp.now().year]
        return (
            f"{per_year.iloc[-1]:,} reports published in {per_year.index[-1]}, "
            f"{per_year.iloc[-1] / per_year.iloc[-2] - 1:+.0%} on {per_year.index[-2]}."
        )

    def trust() -> str:
        g = gov_trust_ipsos_data
        g = g[~g["Country"].str.contains("average", case=False)]
        s = g.set_index("Country")["Agree"].astype(float).sort_values()
        return (
            f"Agreement that government can implement guardrails runs from "
            f"{s.iloc[-1]:.0f}% in {s.index[-1]} to {s.iloc[0]:.0f}% in {s.index[0]}."
        )

    st.subheader("Where to prioritise moral changes?")
    df = pd.DataFrame(
        [
            {
                "Area": "Assistants that talk to customers or staff",
                "Lean towards": "Test for flattery before launch; keep human review on advice",
                "Evidence on this page": safe(syco),
                "Not settled": "One conversation, lab setting; lasting effects are untested.",
            },
            {
                "Area": "Choosing and approving models",
                "Lean towards": "Human-validated, independent testing, not a model grading itself",
                "Evidence on this page": safe(validation),
                "Not settled": "Constructed scenarios, not real decisions; AI-judge self-preference is suggestive only.",
            },
            {
                "Area": "Compliance and governance",
                "Lean towards": "Write internal rules where national rules are thin; Lobby the government to make rule changes.",
                "Evidence on this page": safe(governance),
                "Not settled": "Rules on paper are not enforcement; state-level rules are not counted.",
            },
            {
                "Area": "Incident monitoring",
                "Lean towards": "Log and review incidents, starting with the common failure types",
                "Evidence on this page": safe(incidents),
                "Not settled": "Self-reported and media-driven; more reports may mean more attention, not more harm.",
            },
            {
                "Area": "Public trust and communication",
                "Lean towards": "Show safeguards first, then ask for trust",
                "Evidence on this page": safe(trust),
                "Not settled": "Online samples under-represent people with less access; trust is not proof that safeguards work.",
            },
        ]
    )
    st.table(df)


def render_moral_rollout(
    ai_reports_data: pd.DataFrame,
    human_validation_data: pd.DataFrame,
    frameworks_data: pd.DataFrame,
    gov_trust_ipsos_data: pd.DataFrame,
    syco_study2_data: pd.DataFrame,
    syco_study3_data: pd.DataFrame,
) -> None:
    def safe(fn) -> str:
        try:
            return fn()
        except Exception as e:
            return f"data not available ({type(e).__name__}: {e})"

    def syco_gaps() -> tuple[float, float]:
        s2 = (
            syco_study2_data["is_syco"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "1.0"])
        )
        cond = syco_study3_data["Condition"].astype(str).str.lower()
        s3 = cond.str.contains("syco") & ~cond.str.contains("non")

        def gap(df, mask, col):
            return df.loc[mask, col].mean() - df.loc[~mask, col].mean()

        right = (
            gap(syco_study2_data, s2, "rightorwrong")
            + gap(syco_study3_data, s3, "rightorwrong")
        ) / 2
        repair = (
            gap(syco_study2_data, s2, "repair_score")
            + gap(syco_study3_data, s3, "repair_score")
        ) / 2
        return right, repair

    def binding_share() -> float:
        fw = frameworks_data
        return (
            fw["fr1_enforceability"].eq("Binding")
            | fw["fr2_enforceability"].eq("Binding")
        ).mean()

    def report_growth() -> tuple[int, int, float]:
        dates = pd.to_datetime(
            ai_reports_data["date_published"], errors="coerce"
        ).dropna()
        per_year = dates.dt.year.value_counts().sort_index()
        per_year = per_year[
            per_year.index < pd.Timestamp.now().year
        ]  # drop partial current year
        return (
            per_year.index[-1],
            per_year.iloc[-1],
            per_year.iloc[-1] / per_year.iloc[-2] - 1,
        )

    def trust_series() -> pd.Series:
        g = gov_trust_ipsos_data
        g = g[~g["Country"].str.contains("average", case=False)]
        return g.set_index("Country")["Agree"].astype(float)

    def model_scores() -> pd.Series:
        return (
            human_validation_data.groupby("evaluated_model_name")["human_mean_score"]
            .mean()
            .sort_values()
        )

    # --- Option 1: leave it to national regulation ---
    def reg_for() -> str:
        s = trust_series()
        return (
            f"In {(s >= 50).sum()} of {len(s)} surveyed countries, most people agree "
            f"their government can implement AI guardrails (median agreement {s.median():.0f}%)."
        )

    def reg_against() -> str:
        year, n, g = report_growth()
        return (
            f"Only {binding_share():.0%} of country-by-area framework slots are legally binding, "
            f"while reported incidents grew {g:+.0%} in {year}."
        )

    # --- Option 2: leave it to companies and voluntary safeguards ---
    def self_for() -> str:
        m = model_scores()
        return (
            f"Models already differ widely on human-validated moral scores "
            f"({m.iloc[0]:.1f} for {m.index[0]} to {m.iloc[-1]:.1f} for {m.index[-1]}), "
            f"so better-behaved options exist to buy or build."
        )

    def self_against() -> str:
        right, repair = syco_gaps()
        return (
            f"A flattering AI moved people {right:+.2f} points toward feeling in the right and "
            f"{repair:+.2f} on willingness to repair, an effect users may not notice themselves."
        )

    # --- Option 3: binding rules plus independent human-validated testing ---
    def combo_for() -> str:
        d = human_validation_data
        gap = (d["gpt55_score"] - d["human_mean_score"]).abs().mean()
        return (
            f"Targets both gaps: thin binding rules ({binding_share():.0%} of slots) and "
            f"automated scoring that drifts from human judgement (GPT-5.5 is off by {gap:.1f} points on average)."
        )

    st.subheader("Options to make moral fixes towards AI usage")
    st.caption(
        "The page does not make the decision. This shows what the evidence loaded so far "
        "says for and against each option. It is an interpretation, not a finding of any one source."
    )

    df = pd.DataFrame(
        [
            {
                "Option": "Leave it to national regulation",
                "What supports it": safe(reg_for),
                "What argues against it": safe(reg_against),
            },
            {
                "Option": "Leave it to companies and voluntary safeguards",
                "What supports it": safe(self_for),
                "What argues against it": safe(self_against),
            },
            {
                "Option": "Binding rules plus independent, human-validated testing",
                "What supports it": safe(combo_for),
                "What argues against it": (
                    "This evidence does not test whether the combination works, "
                    "or what it costs. That is an open question."
                ),
            },
        ]
    )
    st.table(df)
    st.caption(
        "Limits: the sycophancy studies are single conversations in a lab, the benchmarks use "
        "constructed scenarios, and a framework on paper is not enforcement."
    )


def render_moral_questions_and_changes() -> None:
    with st.container(key="moral_questions_and_change"):
        with st.expander("Questions to take to your own organisation"):
            st.markdown("""
            - In what would ways should we test AI tools to ensure a moral balance, before outputs reach customers or staff members?
            - What corporate governance should be put into place where national rules are thin or non-binding and protect moral
            - How do we validate the AI tools we buy against human judgement? Should humans still stay in the loop or be replaced with advanced models?
            - How should we use AI in the business automation, whilst considering the moral limitations?
            - Which rules apply in each country we operate in, and are we meeting the strictest of them or only the minimum?
            """)
        with st.expander("What would change the answer"):
            st.markdown("""
            - **Better incident data:** Current reports available are either self-reported and media-driven, so it may consider the attention over actual harm, so better and standardised reporting should be mandated.
            - **Evidence from real decisions:** Model benchmarks used throughout the studies use constructed scenarios but not results from live decision-making processes.
            - **Better understanding of data:** Data needs clarification on the specific circumstances each incident took place in, or whether firms were ill-prepared or the situation was out of reach.
            - **A change in the rules you operate under.** New binding national rules in your markets would shift how much your own internal governance needs to cover.
            """)


############################################################################################################################
# --------------------------------------- HUMAN PRACTICE -------------------------------------------------------------------
############################################################################################################################

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
def render_answer_text(
    tables: dict[str, pd.DataFrame], label: str = "Our answer"
) -> None:
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
