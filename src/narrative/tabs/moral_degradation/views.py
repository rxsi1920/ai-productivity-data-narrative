import altair as alt
import pandas as pd
import streamlit as st

import plotly.graph_objects as go
import plotly.express as px

from countrycode import countrycode


def render_deforestation_map(data: pd.DataFrame) -> None:
    with st.container():
        BG = "#0b1118"
        LAND = "#16212d"
        OCEAN = "#0a1a2b"
        COAST = "rgba(150,180,210,0.35)"
        BORDER = "rgba(150,180,210,0.25)"
        MUTED = "#7d8fa3"
        ACCENT = "#4fc3e8"

        df = data.copy()

        df["iso3"] = countrycode(
            df["country"].astype(str).str.strip().tolist(),
            origin="country.name",
            destination="iso3c",
        )
        df = df.dropna(subset=["iso3"])

        df = df.groupby(["iso3", "country", "year"], as_index=False)["loss"].sum()
        df["loss_plot"] = df["loss"].clip(lower=1)

        globe_geos = dict(
            projection_type="orthographic",
            projection_rotation=dict(lon=-20, lat=15),
            showland=True,
            landcolor=LAND,
            showocean=True,
            oceancolor=OCEAN,
            showcountries=True,
            countrycolor=BORDER,
            showcoastlines=True,
            coastlinecolor=COAST,
            showframe=False,
            bgcolor="rgba(0,0,0,0)",
        )

        colorbar_cfg = dict(
            title=dict(text="Tree cover loss (ha)", side="top", font=dict(color=MUTED)),
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.05,
            yanchor="top",
            len=0.6,
            thickness=12,
            tickfont=dict(color=MUTED),
        )

        globe_layout = dict(
            height=450,
            margin=dict(l=0, r=0, t=20, b=60),
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font=dict(color=MUTED),
        )

        fig = px.choropleth(
            df,
            locations="iso3",
            color="loss_plot",
            hover_name="country",
            hover_data={"loss": ":,.0f", "loss_plot": False, "iso3": False},
            animation_frame="year",
            color_continuous_scale="YlOrRd",
            range_color=(
                df["loss_plot"].quantile(0.05),
                df["loss_plot"].quantile(0.95),
            ),
            labels={"loss_plot": "Tree cover loss (ha)"},
        )
        fig.update_geos(**globe_geos)
        fig.update_layout(
            **globe_layout,
            coloraxis_colorbar=colorbar_cfg,
            sliders=[
                dict(
                    currentvalue=dict(prefix="Year: ", font=dict(color=MUTED)),
                    font=dict(color=MUTED),
                    bgcolor="rgba(255,255,255,0.05)",
                    activebgcolor=ACCENT,
                    bordercolor=COAST,
                )
            ],
        )

        st.plotly_chart(fig, use_container_width=True, key="deforestation_map")
        st.caption(
            "3D globe view of tree cover loss counts per country. From this, it can be "
            "observed that most developed nations face the highest levels of deforestation. "
            "2025 has the far worst destruction of global forests yet. Alternative charts "
            "Source: Hansen Global Forest Change",
            text_alignment="center",
        )

        show_table = st.toggle("Show data", key="deforestation_map_table")
        if show_table:
            table = (
                df[["country", "iso3", "year", "loss"]]
                .rename(columns={"loss": "Tree cover loss (ha)"})
                .sort_values(["year", "Tree cover loss (ha)"], ascending=[False, False])
            )
            st.dataframe(table, use_container_width=True, hide_index=True)


def render_reports_timeseries(data: pd.DataFrame) -> None:
    if data.empty:
        st.warning("No data to display.")
        return

    date_col = next(
        (
            c
            for c in ["date_published", "date", "date_submitted", "published_date"]
            if c in data.columns
        ),
        None,
    )
    if date_col is None:
        st.error("No date column found (expected 'date_published', 'date', etc.).")
        return

    df = data.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    if df.empty:
        st.warning("No valid dates found.")
        return

    df["year"] = df[date_col].dt.year
    df = df[df["year"] >= 2010]

    yearly_counts = (
        df.groupby("year").size().reset_index(name="count").sort_values("year")
    )

    base = alt.Chart(yearly_counts).encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("count:Q", title="Number of Reports"),
    )

    bars = base.mark_bar(opacity=0.65, color="steelblue").encode(
        tooltip=["year:O", "count:Q"]
    )

    line = base.mark_line(color="firebrick", strokeWidth=2, point=True).encode(
        tooltip=["year:O", "count:Q"]
    )

    chart = (
        (bars + line)
        .properties(
            title=alt.TitleParams(
                "AI Incident Reports Over Time (Yearly from 2010)", anchor="middle"
            ),
            height=400,
        )
        .configure(background="transparent")
    )

    with st.container():
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "The number of reports has soared as AI has significantly progressed in its capabilities. These include automating "
            "attack vectors and in their scale of reach. Examples include automated scam calls and large scale data breaches."
            "Source: [[AI Incidents Database]](https://incidentdatabase.ai/apps/incidents/) ",
            text_alignment="center",
        )


def render_facilities_metrics(data: pd.DataFrame) -> tuple[float, str]:
    with st.container():
        if data.empty:
            st.warning("No facility data available.")
            return 0.0, ""

        st.markdown(
            "<h3 style='text-align: center; color: #d9e4ef;'>Top 5 Data Center Operators by Impact</h3>",
            unsafe_allow_html=True,
        )

        metric_options = {
            "Water Consumption (Mgy)": "metrics.waterConsumptionMgy",
            "Carbon Emissions (Tons CO2e)": "metrics.annualCo2eTons",
            "Electricity Usage (MWh)": "metrics.annualItMwh",
        }

        chosen_metric_label = st.selectbox(
            "Select a metric to compare:", options=list(metric_options.keys()), index=2
        )
        chosen_col = metric_options[chosen_metric_label]

        if "operator" not in data.columns or chosen_col not in data.columns:
            st.error(f"Missing required columns: 'operator' or '{chosen_col}'.")
            return 0.0, chosen_metric_label

        df_agg = (
            data.dropna(subset=["operator", chosen_col])
            .groupby("operator")[chosen_col]
            .sum()
            .reset_index()
        )
        df_agg = df_agg.sort_values(by=chosen_col, ascending=False).head(5)

        if df_agg.empty:
            st.warning("No valid data to display for this metric.")
            return 0.0, chosen_metric_label

        df_agg = df_agg.rename(columns={chosen_col: "value"})
        total_val = df_agg["value"].sum()

        base = alt.Chart(df_agg).encode(
            y=alt.Y("operator:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
            x=alt.X("value:Q", title=chosen_metric_label),
        )

        bars = base.mark_bar(cornerRadiusEnd=6, height=30).encode(
            color=alt.Color(
                "value:Q", scale=alt.Scale(scheme="tealblues"), legend=None
            ),
            tooltip=[
                alt.Tooltip("operator:N", title="Operator"),
                alt.Tooltip("value:Q", title=chosen_metric_label, format=",.0f"),
            ],
        )

        text = base.mark_text(
            align="left",
            baseline="middle",
            dx=8,
            color="#d9e4ef",
            fontSize=13,
            fontWeight="bold",
        ).encode(text=alt.Text("value:Q", format=",.0f"))

        chart = (
            (bars + text)
            .properties(
                title=alt.TitleParams(
                    f"Top 5 Operators by {chosen_metric_label}",
                    anchor="middle",
                    color="#d9e4ef",
                ),
                height=300,
            )
            .configure_view(
                strokeWidth=0,
            )
            .configure_axis(
                grid=True,
                gridColor="rgba(150, 180, 210, 0.1)",
                domainColor="rgba(150, 180, 210, 0.4)",
                tickColor="rgba(150, 180, 210, 0.4)",
                labelColor="#7d8fa3",
                titleColor="#7d8fa3",
            )
            .configure(background="transparent")
        )

        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "Top data center operators and their yearly resource consumption and emissions. "
            "The top 4 companies across all metrics are consistently Meta, Microsoft, Amazon and "
            "Google. Source: US Data Center Facilities Dataset. Metrics aggregated per operator."
        )

        return total_val, chosen_metric_label


def render_student_ai_impact(data: pd.DataFrame) -> None:
    if not isinstance(data, pd.DataFrame) or data.empty:
        st.warning("No student performance data available.")
        return

    required = {
        "grade_level", "gender", "uses_ai", "study_hours_per_day",
        "final_score", "ai_usage_time_minutes", "ai_usage_purpose",
        "ai_dependency_score", "performance_category", "passed",
    }
    missing = required - set(data.columns)
    if missing:
        st.error(f"Missing required columns: {sorted(missing)}")
        return

    FG = "#d9e4ef"
    MUTED = "#7d8fa3"
    GRID = "rgba(150, 180, 210, 0.1)"
    DOMAIN = "rgba(150, 180, 210, 0.4)"

    st.markdown(
        "<h3 style='text-align:center;color:#d9e4ef;'>Student Performance & AI Impact</h3>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        grade_opts = ["All"] + sorted(data["grade_level"].dropna().astype(str).unique())
        grade_sel = st.selectbox("Grade level", grade_opts, key="sp_grade")
    with c2:
        gender_opts = ["All"] + sorted(data["gender"].dropna().astype(str).unique())
        gender_sel = st.selectbox("Gender", gender_opts, key="sp_gender")
    with c3:
        ai_sel = st.selectbox("Uses AI", ["All", "Yes", "No"], key="sp_ai")

    df = data.copy()
    if grade_sel != "All":
        df = df[df["grade_level"].astype(str) == grade_sel]
    if gender_sel != "All":
        df = df[df["gender"].astype(str) == gender_sel]
    if ai_sel == "Yes":
        df = df[df["uses_ai"] == 1]
    elif ai_sel == "No":
        df = df[df["uses_ai"] == 0]

    if df.empty:
        st.warning("No students match the selected filters.")
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Students", f"{len(df):,}")
    k2.metric("Avg final score", f"{df['final_score'].mean():.1f}")
    k3.metric("Pass rate", f"{df['passed'].mean() * 100:.1f}%")
    k4.metric("Avg AI usage", f"{df['ai_usage_time_minutes'].mean():.0f} min/day")

    st.markdown(
        "<h4 style='text-align:center;color:#d9e4ef;'>Study time vs Final score</h4>",
        unsafe_allow_html=True,
    )
    color_opts = {
        "Performance category": "performance_category:N",
        "Uses AI": "uses_ai:N",
        "AI dependency score": "ai_dependency_score:Q",
        "AI usage purpose": "ai_usage_purpose:N",
    }
    color_choice = st.selectbox("Color by", list(color_opts.keys()), key="sp_color")

    st.markdown(
        "<h4 style='text-align:center;color:#d9e4ef;'>Final score distribution by AI dependency score</h4>",
        unsafe_allow_html=True,
    )
    box = (
        alt.Chart(df.dropna(subset=["ai_dependency_score"]))
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X("ai_dependency_score:O", title="AI dependency score"),
            y=alt.Y("final_score:Q", title="Final score"),
            color=alt.Color(
                "ai_dependency_score:O",
                scale=alt.Scale(scheme="tealblues"),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("ai_dependency_score:O", title="Dependency"),
                alt.Tooltip("median(final_score):Q", title="Median"),
            ],
        )
        .properties(height=340)
        .configure_view(strokeWidth=0)
        .configure_axis(
            grid=True, gridColor=GRID, domainColor=DOMAIN, tickColor=DOMAIN,
            labelColor=MUTED, titleColor=MUTED,
        )
        .configure(background="transparent")
    )
    st.altair_chart(box, use_container_width=True)

    st.caption(
        "Student-performance comparison. Study time is generally positively associated with the "
        "final score, but that relationship weakens at high AI-usage levels, suggesting "
        "AI can help or hurt performance depending on how it is used. "
        "Source: AI Impact on Student Performance Dataset. Alternative chart could be a scatter "
        "plot however for a large dataset of 8,000 students it would be limited in its ability to ",
        text_alignment="center",
    )