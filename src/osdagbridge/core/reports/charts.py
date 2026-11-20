"""Programmatic charts embedded in the OsdagBridge design report.

All figures are produced with matplotlib's Agg backend (headless), saved as PNG
into the report's temporary asset directory, and embedded by the chapter
modules with :func:`osdagbridge.core.reports.theme.figure`.

Two families are provided:

* :func:`utilization_ratio_chart` — overall demand/capacity summary for the
  primary elements, with the pass/fail threshold at UR = 1.0.
* :func:`material_quantity_charts` — steel tonnage and concrete/rebar
  quantities derived from the Chapter 7 bill of materials.
"""

from __future__ import annotations

import os
from typing import Iterable, Mapping, Optional, Sequence

from .theme import PALETTE, REPORT_STYLE, SERIES_COLORS, apply_chart_theme


def _new_figure(width_in: float = 6.6, height_in: float = 3.0):
    apply_chart_theme()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(width_in, height_in))
    fig.patch.set_facecolor("white")
    return fig, ax


def _save(fig, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, facecolor="white")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return out_path


def _wrap(label: str, width: int = 16) -> str:
    """Wrap a category label so long element names stay readable on the axis."""
    import textwrap

    return textwrap.fill(str(label), width=width)


def _as_float(value) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f


# ---------------------------------------------------------------------------
# Utilization ratio summary
# ---------------------------------------------------------------------------

def utilization_ratio_chart(
    categories: Sequence[tuple],
    out_path: str,
    threshold: float = 1.0,
    title: str = "Overall Utilization Ratio by Primary Element",
) -> Optional[str]:
    """Bar chart of UR values with a red dashed threshold line at ``threshold``.

    ``categories`` is a sequence of ``(label, ur)`` pairs.  Non-numeric or
    missing values are skipped.  The utilization ratio is plotted on the
    y-axis and the UR = 1.0 limit is a horizontal red dashed line, as the
    report specification requires.
    """
    rows = [(lbl, _as_float(ur)) for lbl, ur in categories]
    rows = [(lbl, ur) for lbl, ur in rows if ur is not None]
    if not rows:
        return None

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    fig, ax = _new_figure(width_in=6.8, height_in=3.2)

    x = list(range(len(rows)))
    colors = [("#" + PALETTE["fail"]) if v > threshold else ("#" + PALETTE["primary"])
              for v in values]
    bars = ax.bar(x, values, color=colors, width=0.55,
                  edgecolor="white", linewidth=0.8, zorder=3)

    ax.axhline(threshold, color="#" + PALETTE["fail"], linestyle="--",
               linewidth=1.2, zorder=4,
               label=f"Acceptance limit (UR = {threshold:.2f})")

    for bar, val in zip(bars, values):
        # Keep the value label clear of the dashed limit line: bars that reach
        # close to the limit get an inset label instead of one above the bar.
        near_limit = val > threshold - 0.12
        ax.text(bar.get_x() + bar.get_width() / 2,
                (val - max(values) * 0.04) if near_limit else (val + max(values) * 0.02),
                f"{val:.2f}", ha="center",
                va="top" if near_limit else "bottom", fontsize=8,
                color="white" if near_limit else ("#" + PALETTE["text"]), zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels([_wrap(lbl, 16) for lbl in labels])
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.set_ylim(0, max(max(values) * 1.18, threshold * 1.18))
    ax.set_title(title)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)

    return _save(fig, out_path)


# ---------------------------------------------------------------------------
# Material take-off charts
# ---------------------------------------------------------------------------

def _steel_series(quantities: Mapping[str, object]) -> list:
    """Aggregate steel tonnage (MT) by structural element."""
    def qty(key):
        return _as_float(quantities.get(key))

    series = []
    girders = qty("steel_girders_wt_total")
    if girders:
        series.append(("Girders", girders))

    bracing_parts = [qty(k) for k in (
        "bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    bracing = sum(v for v in bracing_parts if v)
    if bracing:
        series.append(("Cross bracing", bracing))

    ed = sum(v for k in ("end_diaphragm_wt_total", "ed_wt_total")
             if (v := qty(k)))
    if ed:
        series.append(("End diaphragms", ed))

    studs = qty("shear_studs_wt_total")
    if studs:
        series.append(("Shear studs", studs))

    return series


def material_quantity_charts(quantities: Mapping[str, object],
                             out_dir: str) -> dict:
    """Render the Chapter 7 material charts. Returns ``{name: absolute_path}``."""
    os.makedirs(out_dir, exist_ok=True)
    out = {}

    steel = _steel_series(quantities)
    if steel:
        fig, ax = _new_figure(width_in=6.6, height_in=3.0)
        labels = [s[0] for s in steel]
        values = [s[1] for s in steel]
        colors = [SERIES_COLORS[i % len(SERIES_COLORS)] for i in range(len(steel))]
        bars = ax.bar(labels, values, color=colors, width=0.55,
                      edgecolor="white", linewidth=0.8, zorder=3)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(values) * 0.02,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=8)
        ax.set_ylabel("Weight (MT)")
        ax.set_title("Structural Steel Tonnage by Element")
        ax.set_ylim(0, max(values) * 1.18)
        ax.grid(axis="y", zorder=0)
        ax.set_axisbelow(True)
        out["steel_tonnage"] = _save(fig, os.path.join(out_dir, "steel_tonnage.png"))

    concrete = _as_float(quantities.get("concrete_deck_vol_total"))
    rebar = _as_float(quantities.get("rebar_deck_wt_total"))
    if concrete or rebar:
        apply_chart_theme()
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9))
        fig.patch.set_facecolor("white")

        if concrete:
            bars = axes[0].bar(["Deck slab"], [concrete], width=0.45,
                               color="#" + PALETTE["accent"], zorder=3)
            for bar, val in zip(bars, [concrete]):
                axes[0].text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + concrete * 0.02,
                             f"{val:.1f}", ha="center", va="bottom", fontsize=8)
            axes[0].set_ylim(0, concrete * 1.18)
        axes[0].set_ylabel("Volume (m³)")
        axes[0].set_title("Concrete Volume")
        axes[0].grid(axis="y", zorder=0)
        axes[0].set_axisbelow(True)

        if rebar:
            bars = axes[1].bar(["Reinforcement"], [rebar], width=0.45,
                               color="#" + PALETTE["warn"], zorder=3)
            for bar, val in zip(bars, [rebar]):
                axes[1].text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + rebar * 0.02,
                             f"{val:.2f}", ha="center", va="bottom", fontsize=8)
            axes[1].set_ylim(0, rebar * 1.18)
        axes[1].set_ylabel("Weight (MT)")
        axes[1].set_title("Reinforcement Steel")
        axes[1].grid(axis="y", zorder=0)
        axes[1].set_axisbelow(True)

        fig.tight_layout()
        out["concrete_rebar"] = _save(fig, os.path.join(out_dir, "concrete_rebar.png"))

    return out


__all__ = ["utilization_ratio_chart", "material_quantity_charts"]
