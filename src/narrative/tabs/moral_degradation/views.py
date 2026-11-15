import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


def render_reports_timeseries(
    df_incidents: pd.DataFrame, df_reports: pd.DataFrame
) -> None:
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

    chart = (
        (band90 + band50 + bars + line + median_line)
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
        st.caption(
            f"The number of {label.lower()} has soared as AI has significantly progressed in its capabilities. These include automating "
            "attack vectors and in their scale of reach. Examples include automated scam calls and large scale data breaches. "
            "The shaded fan shows the 50% and 90% forecast ranges projected from the selected year. "
            "Source: [[AI Incidents Database]](https://incidentdatabase.ai/apps/incidents/) ",
            text_alignment="center",
        )


def render_() -> None:
    st.header("2. AI's Self-awareness of Morality")


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


def render_ai_validates_ai(data: pd.DataFrame) -> None:
    pass
