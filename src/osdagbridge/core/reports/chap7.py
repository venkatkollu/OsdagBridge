# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# -----------------------------------------------------------------------------
# Table formatting comes exclusively from
# ``osdagbridge.core.reports.theme`` so that the whole report can be restyled
# from one place.  The quantity values themselves are produced by the BOQ
# generator (``osdagbridge.core.boq``) and injected into ``input_dict``.
# =============================================================================

from osdagbridge.core.reports import theme as _theme


# (S.N., description, prefix used by the BOQ generator)
_BOQ_ITEMS = [
    ("1",    r"Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", r"Cross Bracing --- Top Chord",            "bracing_top"),
    ("2(b)", r"Cross Bracing --- Bottom Chord",         "bracing_bot"),
    ("2(c)", r"Cross Bracing --- Diagonal",             "bracing_diag"),
    ("2(d)", r"End Diaphragms (both supports)",         "end_diaphragm"),
    ("3",    r"Concrete (M40) for Deck Slab",           "concrete_deck"),
    ("4",    r"Reinforcement Steel (Fe 500)",           "rebar_deck"),
    ("5",    r"Shear Stud Connectors",                  "shear_studs"),
    ("6",    r"Crash Barrier",                          "crash_barrier"),
]


def _val(input_dict, key, default="N.A."):
    value = input_dict.get(key, default)
    return str(value) if value not in (None, "") else default


def _boq_rows(input_dict):
    rows = []
    for sn, desc, prefix in _BOQ_ITEMS:
        rows.append(
            sn + " & " + desc
            + " & " + _val(input_dict, f"{prefix}_vol_formula")
            + " & " + _val(input_dict, f"{prefix}_qty")
            + " & " + _val(input_dict, f"{prefix}_vol_total")
            + " & " + _val(input_dict, f"{prefix}_wt_single")
            + " & " + _val(input_dict, f"{prefix}_wt_total")
            + r" \\"
        )
    return rows


def _material_figures(input_dict, assets_dir, assets_rel):
    """Render and embed the Chapter 7 material charts."""
    if not assets_dir:
        return ""
    try:
        import os
        from osdagbridge.core.reports.charts import material_quantity_charts

        charts = material_quantity_charts(input_dict, assets_dir)
        if not charts:
            return ""
        base = (assets_rel or "images").rstrip("/")
        blocks = ["\\section{Material Quantity Visualisation}",
                  "\\label{sec:material-charts}"]
        if "steel_tonnage" in charts:
            blocks.append(_theme.figure(
                base + "/steel_tonnage.png",
                "Structural steel tonnage by element (MT).",
                width=r"0.88\textwidth",
            ))
        if "concrete_rebar" in charts:
            blocks.append(_theme.figure(
                base + "/concrete_rebar.png",
                "Deck concrete volume (m³) and reinforcement steel weight (MT).",
                width=r"0.92\textwidth",
            ))
        return "\n".join(blocks) + "\n"
    except Exception:
        # Charts are supplementary: never break report generation.
        return ""


def ch7_quantities(input_dict, assets_dir=None, assets_rel=None):
    table = _theme.longtable(
        colspec=r"|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|",
        header_rows=[
            r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & "
            r"\textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & "
            r"\textbf{Total Weight (MT)} \\[6pt]"
        ],
        body_rows=_boq_rows(input_dict),
        caption=r"\textbf{Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}",
        label="tab:boq",
        note="Weights are computed from the designed section properties and unit weights of steel (7850 kg/m³) and concrete (2500 kg/m³).",
        font_size=r"\footnotesize",
    )

    figures = _material_figures(input_dict, assets_dir, assets_rel)

    return (
        "\n\\chapter{Material Take-off \\& Quantity Summary}\n"
        "\\label{ch:material-takeoff}\n\n"
        "This chapter consolidates the quantities of structural steel, concrete, "
        "reinforcement and ancillary items required for the bridge.\n\n"
        + table + "\n"
        + figures
    )
