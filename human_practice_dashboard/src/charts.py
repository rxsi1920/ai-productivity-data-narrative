"""Shared chart styling.  Colours follow one rule: blue = human text, orange = AI text.

The two hues pass the dataviz palette validator in light mode (adjacent CVD delta E 24.7,
normal-vision delta E 33.6, contrast >= 3:1 on the #fcfcfb surface).
"""

from __future__ import annotations

import altair as alt

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
