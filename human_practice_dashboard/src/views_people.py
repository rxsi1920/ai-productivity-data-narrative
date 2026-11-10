"""Renderers for the workforce charts (adoption, output and skill findings, entry-level employment), the
web-composition chart, and the page's answer, decision, limits and sources blocks."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from .charts import AI, GRID, HUMAN, INK, INK2, MIXED, NEUTRAL, STRENGTH_COLOURS, STRENGTH_ORDER, STRENGTH_SHAPES, style
from .data import WILDAI_COMMIT, WORKFORCE_COMMIT
from .views import EMPTY, KPI_HEIGHT, WILDAI_CITE, _footer, _heading, _pct

KARAN_REPO = "https://github.com/karanmakhijauts/at-3-dvn"
BTOS_CITE = (
    "US Census Bureau, Business Trends and Outlook Survey (BTOS), https://www.census.gov/hfp/btos; file `btos_ai.csv` "
    f"as collected by Karan Makhija ([repo]({KARAN_REPO}), commit `{WORKFORCE_COMMIT[:7]}`)."
)
OWID_CITE = (
    "Our World in Data, *Estimated share of working-age adults who use generative AI* (modelled from Microsoft AI "
    "Diffusion Report data), https://ourworldindata.org/grapher/estimated-share-people-generative-ai; file `owid_genai.csv`."
)
EVIDENCE_CITE = (
    f"Findings hand-built from the cited papers by Karan Makhija ([repo]({KARAN_REPO}), commit `{WORKFORCE_COMMIT[:7]}`), "
    "file `evidence.csv`. Each row links its paper."
)
CANARIES_URL = "https://digitaleconomy.stanford.edu/app/uploads/2026/08/Canaries_August2026.pdf"
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
def render_answer(tables: dict[str, pd.DataFrame]) -> None:
    evidence, entry, comp, cost = tables["evidence"], tables["entry_level"], tables["web_composition"], tables["cost"]
    adoption = tables["adoption"]
    obs = _observed(tables["ai_share"])
    last_month = obs["month"].iloc[-1]
    two_years = last_month - pd.DateOffset(years=2)
    human_then, human_now = _human_share(comp, two_years), _human_share(comp, last_month)
    out = evidence[evidence["panel"] == "output"]
    gains = int((out["direction"] == "gain").sum())
    exposed, other, shortfall = _relative_gap(entry)
    yes = adoption[adoption["answer"] == "Yes"].sort_values("period_order")
    first, latest = yes.iloc[0], yes.iloc[-1]
    aug = cost[(cost["target"] == "c4") & (cost["model_size"] == "268M") & (cost["scenario"] == "August 2026")].iloc[0]

    with st.container(key="answer", border=True):
        st.markdown(
            "**Our answer: the early signs say yes, but it is not yet proven.** "
            f"AI is raising measured output today ({gains} of {len(out)} output findings on this page show a gain). "
            "Over the same period three things that people and models learn from are thinning: early-career employment in "
            f"AI-exposed occupations, the human-written share of web text, and the value of that web text for training. "
            "The first is a descriptive association, the second is a share of a sample, and the third is a prediction "
            "from a fitted law on small models. A reader could weigh the same numbers the other way: the gains are "
            "measured, the costs are early indicators."
        )
    cols = st.columns(4)
    cols[0].metric(
        "US firms using AI",
        f"{latest['share_pct']:.1f}%",
        delta=f"from {first['share_pct']:.1f}% ({first['period_label']} to {latest['period_label']})",
        delta_color="off", delta_arrow="off", border=True, height=KPI_HEIGHT,
    )
    cols[1].metric(
        "Jobs held by ages 22-25, AI-exposed work",
        f"{exposed:+.0f}%",
        delta=f"less-exposed peers {other:+.0f}%",
        delta_color="off", delta_arrow="off", border=True, height=KPI_HEIGHT,
    )
    cols[2].metric(
        "Human-labelled share of web text",
        _pct(human_now),
        delta=f"from {_pct(human_then)} in {two_years:%b %Y}",
        delta_color="off", delta_arrow="off", border=True, height=KPI_HEIGHT,
    )
    cols[3].metric(
        "Compute to match human-only training",
        f"{aug['cost']:.2f}×",
        delta=f"predicted, at {_pct(aug['ai_share'])} AI text",
        delta_color="off", delta_arrow="off", border=True, height=KPI_HEIGHT,
    )
    st.caption(
        f"Units and baselines differ. Firms: per cent of US firms answering Yes, two-week periods. Jobs: per cent change in "
        f"employment from November 2022 to June 2026, US payroll data from one provider. Web text: share of tokens in a "
        f"monthly sample of about 5,000 documents, latest {last_month:%B %Y}. Compute: a multiplier predicted by a fitted "
        "law for a 268M-parameter model, not a measured cost. Each figure is charted, with its source and limits, below."
    )


# ----------------------------------------------------------------------------- adoption
ANSWER_STYLE = {"Yes": (INK, [1, 0]), "No": (NEUTRAL, [6, 3]), "Do not know": (NEUTRAL, [2, 3])}


def render_adoption(adoption: pd.DataFrame, genai_use: pd.DataFrame) -> None:
    with st.container(key="adoption"):
        _heading("AI use at work is spreading", "How quickly are firms and working-age adults taking up AI?")
        latest_label = adoption.sort_values("period_order")["period_label"].iloc[-1]
        st.caption(
            f"Unit: per cent of US firms giving each answer to the BTOS AI-use question, by two-week collection period. "
            f"Latest observation: {latest_label}. Periods are numbered within the year (P24 of 2025 to P21 of 2026, about "
            "11 months). US firms only; one survey question; this is use, not intensity or quality of use."
        )
        left, right = st.columns([3, 2], gap="large")
        with left:
            answers = st.multiselect("Answers to show", list(ANSWER_STYLE), default=["Yes"], key="adoption_answers")
            frame = adoption[adoption["answer"].isin(answers)].sort_values("period_order")
            if frame.empty:
                st.info(EMPTY)
            else:
                labels = adoption.drop_duplicates("period_order").sort_values("period_order")
                ticks = labels[(labels["period_order"] - 1) % 4 == 0]
                expr = " : ".join(f"datum.value == {int(o)} ? '{l}'" for o, l in zip(ticks["period_order"], ticks["period_label"])) + " : ''"
                n = int(labels["period_order"].max())
                x = alt.X(
                    "period_order:Q",
                    title="Two-week collection period (year-period)",
                    scale=alt.Scale(domain=[0, n + 2.5]),
                    axis=alt.Axis(values=[int(v) for v in ticks["period_order"]], labelExpr=expr, grid=False),
                )
                y = alt.Y("share_pct:Q", title="Share of US firms (%)", scale=alt.Scale(zero=True))
                shown = [a for a in ANSWER_STYLE if a in answers]
                colour = alt.Color("answer:N", scale=alt.Scale(domain=shown, range=[ANSWER_STYLE[a][0] for a in shown]), legend=alt.Legend(title="Answer"))
                dash = alt.StrokeDash("answer:N", scale=alt.Scale(domain=shown, range=[ANSWER_STYLE[a][1] for a in shown]), legend=None)
                line = alt.Chart(frame).mark_line(strokeWidth=2).encode(x=x, y=y, color=colour, strokeDash=dash)
                ends = frame[frame["period_order"].isin([1, n])].assign(text=lambda f: f["share_pct"].map(lambda v: f"{v:.1f}%"))
                dots = alt.Chart(ends).mark_point(filled=True, size=60, opacity=1).encode(x=x, y=y, color=colour)
                first_lab = alt.Chart(ends[ends["period_order"] == 1]).mark_text(color=INK, align="left", dx=-4, dy=-12, fontSize=12).encode(x=x, y=y, text="text:N")
                last_lab = alt.Chart(ends[ends["period_order"] == n]).mark_text(color=INK, align="left", dx=8, fontSize=12).encode(x=x, y=y, text="text:N")
                st.altair_chart(style(line + dots + first_lab + last_lab, height=320), theme=None, width="stretch")
        with right:
            entities = sorted(e for e in genai_use["entity"].unique() if e != "World")
            country = st.selectbox(
                "Working-age adults using generative AI: compare a country with the world",
                entities,
                index=entities.index("Australia") if "Australia" in entities else 0,
                key="adoption_country",
            )
            for name in ("World", country):
                rows = genai_use[genai_use["entity"] == name].sort_values("day")
                if rows.empty:
                    st.info(EMPTY)
                    continue
                a, b = rows.iloc[0], rows.iloc[-1]
                st.metric(
                    f"{name}: adults aged 15 to 64 using generative AI",
                    f"{b['share_pct']:.1f}%",
                    delta=f"from {a['share_pct']:.1f}% ({a['day']} to {b['day']})",
                    delta_color="off", delta_arrow="off", border=True,
                )
            st.caption(
                "Unit: per cent of people aged 15 to 64. Modelled estimates from Microsoft usage data with three dates "
                f"only; not a survey. Latest observation: {genai_use['day'].max()}."
            )
        _footer(frame if not frame.empty else adoption.head(0), "Download filtered BTOS rows", "btos_ai_use.csv", "adoption_download", f"{BTOS_CITE} {OWID_CITE}")


# ----------------------------------------------------------------------------- output vs skill
def _evidence_panel(frame: pd.DataFrame, title: str, key: str) -> None:
    st.markdown(f"**{title}**")
    if frame.empty:
        st.info(EMPTY)
        return
    frame = frame.assign(text=frame.apply(lambda r: ("▲ " if r["direction"] == "gain" else "▼ ") + r["short_label"], axis=1))
    order = list(frame.sort_values("sample_size", ascending=False)["label"])
    y = alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelLimit=230, grid=True))
    x = alt.X(
        "sample_size:Q",
        title="People in the study (log scale)",
        scale=alt.Scale(type="log", domain=[100, 300000]),
        axis=alt.Axis(values=[100, 300, 1000, 3000, 10000], format=",d", grid=False),
    )
    points = alt.Chart(frame).mark_point(filled=True, size=170, opacity=1).encode(
        x=x,
        y=y,
        color=alt.Color("evidence_strength:N", scale=alt.Scale(domain=STRENGTH_ORDER, range=STRENGTH_COLOURS), legend=alt.Legend(title="Evidence strength")),
        shape=alt.Shape("evidence_strength:N", scale=alt.Scale(domain=STRENGTH_ORDER, range=STRENGTH_SHAPES), legend=alt.Legend(title="Evidence strength")),
        tooltip=[alt.Tooltip("label:N", title="Study"), alt.Tooltip("design:N", title="Design"), alt.Tooltip("finding:N", title="Finding")],
    )
    text = alt.Chart(frame).mark_text(color=INK, align="left", dx=12, fontSize=12).encode(x=x, y=y, text="text:N")
    st.altair_chart(style(points + text, height=70 + 55 * len(frame)), theme=None, width="stretch", key=key)


def render_evidence(evidence: pd.DataFrame) -> None:
    with st.container(key="output_vs_skill"):
        _heading("Output gains against skill signals", "The same tools that raise output: what do they do to judgement and learning?")
        st.caption(
            "Unit: one dot per finding, placed by the number of people studied; the printed label is the finding, with ▲ for a "
            "gain and ▼ for a loss. The findings measure different things, so they are not combined into one score. "
            "Studies date from 2023 to 2025. Latest observation: not applicable (published studies)."
        )
        strengths = st.multiselect("Evidence strength", STRENGTH_ORDER, default=STRENGTH_ORDER, key="evidence_strength")
        frame = evidence[evidence["evidence_strength"].isin(strengths)]
        out, skill = frame[frame["panel"] == "output"], frame[frame["panel"] == "skill"]
        if frame.empty:
            st.info(EMPTY)
        else:
            st.markdown(
                f"##### {int((out['direction'] == 'gain').sum())} of {len(out)} output findings show a gain. Of {len(skill)} skill "
                f"findings, {int((skill['direction'] == 'loss').sum())} show a loss and {int((skill['direction'] == 'gain').sum())} a gain."
            )
            c1, c2 = st.columns(2, gap="large")
            with c1:
                _evidence_panel(out, "Output gains", "evidence_output_chart")
            with c2:
                _evidence_panel(skill, "Skill and learning signals", "evidence_skill_chart")
            with st.expander("Read each finding, its design and how far it was checked", expanded=False):
                st.dataframe(
                    frame[["panel_title", "label", "design", "sample_size", "sample_unit", "finding", "evidence_strength", "strength_rationale", "source_url", "location_in_source", "check_status"]],
                    hide_index=True,
                    width="stretch",
                    column_config={"source_url": st.column_config.LinkColumn("source"), "panel_title": "panel"},
                )
        st.caption(
            "Skill findings are task accuracy, self-reported thinking or a hint of learning. None is a long-run test of "
            "ability. Evidence strength is a judgement made for this dashboard (see `strength_rationale`); `check_status` "
            "says how much of each paper was read. The Dell'Acqua et al. rows were entered from a summary and still need "
            "checking against the paper."
        )
        _footer(frame, "Download filtered findings", "output_skill_findings.csv", "evidence_download", EVIDENCE_CITE)


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
            "observation: June 2026. The values are rounded in the paper (\"about\")."
        )
        exposed, other, shortfall = _relative_gap(entry)
        left, right = st.columns([3, 2], gap="large")
        with left:
            frame = entry.assign(
                text=entry["change_pct"].map(lambda v: f"{v:+.0f}%"),
                highlight=entry["highlight"].astype(str).str.lower().eq("true"),
            )
            order = list(frame.sort_values("change_pct")["group"])
            y = alt.Y("group:N", sort=order, title=None, axis=alt.Axis(labelLimit=280, grid=False))
            x = alt.X("change_pct:Q", title="Change in employment, Nov 2022 to Jun 2026 (%)", scale=alt.Scale(domain=[-16, 16]))
            bars = alt.Chart(frame).mark_bar(size=26).encode(
                x=x,
                y=y,
                color=alt.Color(
                    "highlight:N",
                    scale=alt.Scale(domain=[True, False], range=[AI, NEUTRAL]),
                    legend=None,
                ),
            )
            zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=INK2).encode(x="x:Q")
            pos = alt.Chart(frame[frame["change_pct"] >= 0]).mark_text(color=INK, align="left", dx=6, fontSize=13).encode(x=x, y=y, text="text:N")
            neg = alt.Chart(frame[frame["change_pct"] < 0]).mark_text(color=INK, align="right", dx=-6, fontSize=13).encode(x=x, y=y, text="text:N")
            st.altair_chart(style(bars + zero + pos + neg, height=250), theme=None, width="stretch")
        with right:
            st.metric(
                "Gap between the two groups aged 22 to 25",
                f"{other - exposed:.0f} points",
                delta=f"a {shortfall:.0f}% relative shortfall",
                delta_color="off", delta_arrow="off", border=True,
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
            "causal effect of AI, and report that the size of the gap is specific to the ADP data. \"AI-exposed\" means the "
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
LABELS = {"Human": ("Human-labelled", HUMAN, 0), "Mixed": ("Mixed", MIXED, 1), "AI": ("AI-labelled", AI, 2)}


def render_web_composition(comp: pd.DataFrame) -> None:
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
        basis = st.radio("Measure the share by", ["Tokens", "Documents"], horizontal=True, key="composition_basis")
        col = "token_share" if basis == "Tokens" else "document_share"
        wide = comp.pivot(index="month", columns="label", values=col).reindex(columns=list(LABELS)).fillna(0.0)
        long = wide.reset_index().melt(id_vars="month", var_name="label", value_name="share")
        long["name"] = long["label"].map(lambda v: LABELS[v][0])
        long["order"] = long["label"].map(lambda v: LABELS[v][2])
        names = [v[0] for v in LABELS.values()]
        cols = st.columns(3)
        for box, key in zip(cols, LABELS):
            box.metric(
                f"{LABELS[key][0]} share, {last:%b %Y}",
                _pct(wide.loc[last, key]),
                delta=f"{_pct(wide.loc[then, key])} in {then:%b %Y}",
                delta_color="off", delta_arrow="off", border=True,
            )
        x = alt.X(
            "month:T",
            title=None,
            axis=alt.Axis(format="%Y", tickCount="year", grid=False),
            scale=alt.Scale(domain=[comp["month"].min().isoformat(), (last + pd.DateOffset(months=9)).isoformat()]),
        )
        area = alt.Chart(long).mark_area(opacity=0.9).encode(
            x=x,
            y=alt.Y("share:Q", stack="zero", title=f"Share of sampled web {basis.lower()}", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("name:N", scale=alt.Scale(domain=names, range=[v[1] for v in LABELS.values()]), legend=alt.Legend(title="Pangram label")),
            order=alt.Order("order:Q"),
        )
        end = wide.loc[last]
        mids, base = [], 0.0
        for key in LABELS:
            mids.append({"month": last, "y": base + end[key] / 2, "text": f"{LABELS[key][0]} {_pct(end[key])}"})
            base += end[key]
        # keep the two thin top bands' labels from overlapping
        mids[1]["y"] = min(mids[1]["y"], mids[2]["y"] - 0.07)
        ends = alt.Chart(pd.DataFrame(mids)).mark_text(color=INK, align="left", dx=6, fontSize=12).encode(x="month:T", y=alt.Y("y:Q"), text="text:N")
        st.altair_chart(style(area + ends, height=340), theme=None, width="stretch")
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
            f"{WILDAI_CITE} File `monthly_topic_format.csv`, summed by month and label.",
        )


# ----------------------------------------------------------------------------- decision
def render_decision(tables: dict[str, pd.DataFrame]) -> None:
    evidence, entry, comp, cost = tables["evidence"], tables["entry_level"], tables["web_composition"], tables["cost"]
    out = evidence[evidence["panel"] == "output"]
    gains = int((out["direction"] == "gain").sum())
    exposed, other, shortfall = _relative_gap(entry)
    obs = _observed(tables["ai_share"])
    last = obs["month"].iloc[-1]
    human_now, human_then = _human_share(comp, last), _human_share(comp, last - pd.DateOffset(years=2))
    c4 = cost[(cost["target"] == "c4") & (cost["model_size"] == "268M")].set_index("scenario")["cost"]
    e4 = evidence.set_index("id").loc["E4", "short_label"] if "E4" in set(evidence["id"]) else ""
    with st.container(key="decision"):
        st.subheader("Where to prioritise human skilled input, and where AI-efficient output")
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
    adoption, use = tables["adoption"], tables["genai_use"]
    obs = _observed(tables["ai_share"])
    with st.container(key="sources"):
        st.subheader("Sources and last data refresh")
        rows = pd.DataFrame(
            [
                {"Dataset": "US firms using AI (Census Bureau BTOS)", "Latest observation": adoption.sort_values("period_order")["period_label"].iloc[-1], "Copied into this app": f"26 Oct 2026 (Karan's repo, commit {WORKFORCE_COMMIT[:7]})", "Licence": "US government work"},
                {"Dataset": "Adults using generative AI (Our World in Data / Microsoft)", "Latest observation": str(use["day"].max()), "Copied into this app": f"26 Oct 2026 (Karan's repo, commit {WORKFORCE_COMMIT[:7]})", "Licence": "CC BY 4.0 (OWID)"},
                {"Dataset": "Output and skill findings (five papers, 2023 to 2025)", "Latest observation": "2025 (Lee et al.)", "Copied into this app": f"26 Oct 2026 (Karan's repo, commit {WORKFORCE_COMMIT[:7]})", "Licence": "Cited facts"},
                {"Dataset": "Early-career employment (Brynjolfsson, Chandar and Chen)", "Latest observation": "June 2026", "Copied into this app": "10 Nov 2026 (from the August 2026 paper)", "Licence": "Cited facts"},
                {"Dataset": "Web text and model runs (WildAI, Russell et al.)", "Latest observation": f"{obs['month'].iloc[-1]:%B %Y}", "Copied into this app": f"3 Nov 2026 (commit {WILDAI_COMMIT[:7]})", "Licence": "CC BY-NC-SA 4.0"},
                {"Dataset": "Definitions of model collapse (Schaeffer et al.)", "Latest observation": "2025 (arXiv v2)", "Copied into this app": "26 Oct 2026 (table written from the paper)", "Licence": "Cited facts"},
            ]
        )
        st.table(rows.set_index("Dataset"))
        st.caption(
            "Last data refresh: 10 November 2026. Every number on this page is in, or computed from, the files in "
            "`data/processed/`, which `python -m src.data` rebuilds from the source copies in `data/`. See `DATA_DICTIONARY.md`."
        )
