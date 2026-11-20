"""OsdagBridge report — centralized formatting & style system.

This module is the **single source of truth** for every visual/layout rule used
by the design report:

* page geometry and margins;
* the colour palette (LaTeX and matplotlib share it);
* table defaults (padding, rule thickness, row height);
* header / footer themes;
* figure and caption styling;
* the long-table builder that guarantees repeated column headers on every
  page (``\\endfirsthead`` / ``\\endhead``).

Chapter modules must import their formatting from here instead of hard-coding
values.  Changing ``REPORT_STYLE`` therefore restyles the whole document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

# ---------------------------------------------------------------------------
# Palette (hex, no leading '#')
# ---------------------------------------------------------------------------
PALETTE = {
    "primary":      "91B014",   # Osdag green
    "primary_dark": "5F7A0B",
    "accent":       "2E5E8C",
    "pass":         "1E7B34",
    "fail":         "C0392B",
    "warn":         "B7791F",
    "grid":         "C9CDD2",
    "text":         "1F2933",
    "neutral":      "8C99A6",
}

# Ordered colours for multi-series charts.
SERIES_COLORS = ["#91B014", "#2E5E8C", "#B7791F", "#8C99A6", "#C0392B", "#5F7A0B"]


@dataclass(frozen=True)
class PageGeometry:
    paper: str = "a4paper"
    font_size: str = "12pt"
    top: str = "2.4cm"
    bottom: str = "2.8cm"
    left: str = "2.0cm"
    right: str = "2.0cm"
    headheight: str = "18pt"
    headsep: str = "10pt"
    footskip: str = "1.4cm"
    # Extra safety gap kept free above the footer box.
    foot_clearance: str = "6pt"


@dataclass(frozen=True)
class TableStyle:
    colsep: str = "3.0pt"
    arraystretch: str = "1.15"
    extrarowheight: str = "2pt"
    arrayrulewidth: str = "0.5pt"
    longtable_pre: str = "0pt"
    longtable_post: str = "8pt"
    # Minimum free space (in baselines) required before a table starts, so a
    # table can never be flushed against the footer.
    needspace_baselines: int = 7
    font_size: str = "\\small"


@dataclass(frozen=True)
class HeaderFooterStyle:
    header_left: str = "{project} $|$ {job}"
    header_right: str = "{date} $|$ {rev}"
    footer_left: str = "Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
    footer_right: str = "Page \\thepage\\ of \\pageref{LastPage}"


@dataclass(frozen=True)
class FigureStyle:
    default_width: str = "0.9\\textwidth"
    caption_size: str = "small"


@dataclass(frozen=True)
class ReportStyle:
    geometry: PageGeometry = field(default_factory=PageGeometry)
    table: TableStyle = field(default_factory=TableStyle)
    header_footer: HeaderFooterStyle = field(default_factory=HeaderFooterStyle)
    figures: FigureStyle = field(default_factory=FigureStyle)
    palette: dict = field(default_factory=lambda: dict(PALETTE))

    # -- LaTeX fragments ----------------------------------------------------
    def colors(self) -> str:
        defs = [
            r"\definecolor{osdagGreen}{HTML}{%s}" % self.palette["primary"],
            r"\definecolor{osdagGreenDark}{HTML}{%s}" % self.palette["primary_dark"],
            r"\definecolor{osdagAccent}{HTML}{%s}" % self.palette["accent"],
            r"\definecolor{osdagPass}{HTML}{%s}" % self.palette["pass"],
            r"\definecolor{osdagFail}{HTML}{%s}" % self.palette["fail"],
            r"\definecolor{osdagWarn}{HTML}{%s}" % self.palette["warn"],
            r"\definecolor{osdagGrid}{HTML}{%s}" % self.palette["grid"],
            r"\definecolor{osdagNeutral}{HTML}{%s}" % self.palette["neutral"],
        ]
        return "\n".join(defs)

    def table_defaults(self) -> str:
        t = self.table
        return "\n".join([
            r"\setlength{\tabcolsep}{%s}" % t.colsep,
            r"\renewcommand{\arraystretch}{%s}" % t.arraystretch,
            r"\setlength{\arrayrulewidth}{%s}" % t.arrayrulewidth,
            r"\setlength{\extrarowheight}{%s}" % t.extrarowheight,
            r"\setlength{\LTpre}{%s}" % t.longtable_pre,
            r"\setlength{\LTpost}{%s}" % t.longtable_post,
            r"\setlength{\LTleft}{\fill}",
            r"\setlength{\LTright}{\fill}",
            # Never start a table within N baselines of the page bottom.
            # Table typography is part of the theme, not the chapter files.
            r"\AtBeginEnvironment{longtable}{\%s}" % t.font_size.lstrip("\\"),
        ])

    def page_geometry(self) -> str:
        g = self.geometry
        return (r"\usepackage[%s, top=%s, bottom=%s, left=%s, right=%s, "
                r"headheight=%s, headsep=%s, footskip=%s]{geometry}"
                % (g.paper, g.top, g.bottom, g.left, g.right,
                   g.headheight, g.headsep, g.footskip))


REPORT_STYLE = ReportStyle()

# Padding used by unusually wide tables (e.g. the 9-column analysis summary).
TIGHT_COLSEP = "2.5pt"


def table_padding(colsep: Optional[str] = None,
                  arraystretch: Optional[str] = None) -> str:
    """Return LaTeX padding overrides taken from the theme.

    Chapters must not hard-code ``\\setlength{\\tabcolsep}`` themselves; call
    this helper instead when a table genuinely needs tighter padding.
    """
    t = REPORT_STYLE.table
    return "\n".join([
        r"\setlength{\tabcolsep}{%s}" % (colsep or t.colsep),
        r"\renewcommand{\arraystretch}{%s}" % (arraystretch or t.arraystretch),
    ])


def _hdr_foot_defs(main_style: str, project: str, job: str, date: str, rev: str) -> str:
    hf = REPORT_STYLE.header_footer
    left = hf.header_left.format(project=project, job=job)
    right = hf.header_right.format(date=date, rev=rev)
    return rf"""
\fancypagestyle{{{main_style}}}{{
  \fancyhf{{}}
  \fancyhead[L]{{{left}}}
  \fancyhead[R]{{{right}}}
  \fancyfoot[L]{{{hf.footer_left}}}
  \fancyfoot[R]{{{hf.footer_right}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \vspace{{-18pt}}%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}\hfil}}%
      \vspace{{4pt}}%
    }}{{%
      \vspace{{-6pt}}%
    }}%
    \color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{4pt}}%
  }}
}}
"""


def preamble(project_name: str, job_number: str, report_date: str, report_version: str = "Rev 0") -> str:
    """Return the full LaTeX preamble, driven entirely by ``REPORT_STYLE``."""
    from .report_utils import _tex

    pn, jn, rd, rv = _tex(project_name), _tex(job_number), _tex(report_date), _tex(report_version)
    t = REPORT_STYLE.table
    g = REPORT_STYLE.geometry

    template = r"""
\documentclass[<<FONT>>,<<PAPER>>]{report}

% ── Packages ────────────────────────────────────────────────────────────────
<<GEOMETRY>>
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage{placeins}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain,
    font=<<CAPTION_FONT>>
}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}

% ── Table layout (centralized) ──────────────────────────────────────────────
<<TABLE_DEFAULTS>>

% Keep short tables/notes clear of the footer box.
\setlength{\skip\footins}{12pt}
\raggedbottom
\clubpenalty=10000
\widowpenalty=10000

<<COLORS>>

% ── Header / footer themes ──────────────────────────────────────────────────
<<HEADER_MAIN>>
<<HEADER_PLAIN>>
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
% Cover page: the report class restarts the page counter after \end{titlepage},
% so a page number here would print "Page 1" twice.
\fancypagestyle{coverpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}

% Let TeX stretch inter-word space instead of letting a long code number
% (e.g. "Cl.208.2/208.3") push the line into the margin.  Only used as a
% last resort, so normal spacing is unaffected.
\setlength{\emergencystretch}{2em}

% ── Vertical rhythm (single source of truth) ───────────────────────────────
% Chapter modules must use these names instead of literal \vspace{...} values.
\newcommand{\chaptergap}{\vspace{2.2em}}
\newcommand{\sectiongap}{\vspace{1em}}
\newcommand{\subsectiongap}{\vspace{0.6em}}
\newcommand{\tightgap}{\vspace{0.4em}}
\newcommand{\smallgap}{\vspace{0.8em}}
\newcommand{\microgap}{\vspace{0.3em}}

% Left-align a longtable against the text block (used by wide numeric tables).
\newcommand{\longtableleft}{\setlength{\LTleft}{0pt}\setlength{\LTright}{\fill}}

% ── Custom commands ─────────────────────────────────────────────────────────
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""

    for token, value in (
        ("<<FONT>>", g.font_size),
        ("<<PAPER>>", g.paper),
        ("<<GEOMETRY>>", REPORT_STYLE.page_geometry()),
        ("<<CAPTION_FONT>>", REPORT_STYLE.figures.caption_size),
        ("<<TABLE_DEFAULTS>>", REPORT_STYLE.table_defaults()),
        ("<<COLORS>>", REPORT_STYLE.colors()),
        ("<<HEADER_MAIN>>", _hdr_foot_defs("main", pn, jn, rd, rv)),
        ("<<HEADER_PLAIN>>", _hdr_foot_defs("plain", pn, jn, rd, rv)),
    ):
        template = template.replace(token, value)
    return template


# ---------------------------------------------------------------------------
# Long tables with repeated headers
# ---------------------------------------------------------------------------

def longtable(
    colspec: str,
    header_rows: Sequence[str],
    body_rows: Iterable[str],
    caption: Optional[str] = None,
    label: Optional[str] = None,
    note: Optional[str] = None,
    font_size: Optional[str] = None,
) -> str:
    """Build a ``longtable`` that repeats its header on every page.

    Parameters
    ----------
    colspec
        Column specification, e.g. ``|L{5cm}|C{2cm}|``.
    header_rows
        One or more LaTeX rows (``... \\\\``) forming the header.
    body_rows
        Data rows, each already terminated by ``\\\\``.
    caption
        Optional caption (LaTeX, not escaped).
    label
        Optional ``\\label`` key.
    note
        Optional italic note printed under the table.
    font_size
        Optional size command for the table body (defaults to the theme's).
    """
    size = font_size if font_size is not None else REPORT_STYLE.table.font_size
    head = "\n".join(header_rows)
    # Horizontal rules between body rows are part of the table style, so
    # callers only supply content rows.
    body = "\n\\hline\n".join(r.rstrip() for r in body_rows)
    if body.strip() and not body.rstrip().endswith("\\hline"):
        body = body.rstrip() + "\n\\hline"

    cap_tex = ""
    if caption:
        cap_tex = r"\caption{%s}" % caption
        if label:
            cap_tex += r"\label{%s}" % label
        cap_tex += "\n"

    note_tex = ("\n\\noindent\\textit{%s}\n" % note) if note else "\n"

    return (
        "\\begingroup\n"
        f"{size}\n"
        "\\begin{longtable}{" + colspec + "}\n"
        + cap_tex
        + "\\hline\n"
        + head + "\n"
        + "\\hline\n"
        + "\\endfirsthead\n"
        + (("\\caption[]{%s (continued)}\\\\\n" % caption) if caption else "")
        + "\\hline\n"
        + head + "\n"
        + "\\hline\n"
        + "\\endhead\n"
        + "\\hline\n"
        + "\\multicolumn{%d}{r}{\\footnotesize\\itshape continued on next page} \\\\\n" % _ncols(colspec)
        + "\\endfoot\n"
        + "\\hline\n"
        + "\\endlastfoot\n"
        + body + "\n"
        + "\\end{longtable}\n"
        + "\\endgroup"
        + note_tex
    )


def _ncols(colspec: str) -> int:
    """Best-effort column count from a LaTeX column spec."""
    depth = 0
    count = 0
    for ch in colspec:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0 and ch in "lcrpmbXLCR":
            count += 1
    return max(1, count)


def flatten_breakable_multirows(tex: str) -> str:
    """Make group labels page-break-safe.

    ``\\multirow{n}{*}{\\makecell{Label}}`` centres its label over ``n`` rows,
    but when the group happens to straddle a page break the label box can be
    pushed past the bottom margin and print on top of the footer (the reported
    "G4 bleeding into the footer" defect).  Rewriting the label as a plain
    ``\\makecell`` on the group's first row keeps the same visual grouping via
    the existing ``\\cline`` rules, while being completely break-neutral.
    Subsequent rows in the group keep an empty first cell, exactly as if the
    label were vertically centred.
    """
    import re

    pattern = re.compile(r"\\multirow\{\d+\}\{\*\}\{\\makecell\{([^{}]*)\}\}")
    return pattern.sub(lambda m: "\\makecell{" + m.group(1) + "}", tex)


def repeat_longtable_headers(tex: str) -> str:
    """Post-process ``tex`` so every ``longtable`` repeats its header row.

    Many chapter generators emit a plain ``longtable`` whose column headings and
    ``\\hline`` are written once.  On a page break the continuation page then
    loses its headings.  This transform rewrites each such table to the explicit
    ``\\endfirsthead`` / ``\\endhead`` form, reusing the exact heading block
    (including multi-row ``\\makecell`` headers).

    Tables that already define ``\\endhead`` are left untouched.
    """
    out = []
    i = 0
    opener = "\\begin{longtable}"
    closer = "\\end{longtable}"

    while True:
        j = tex.find(opener, i)
        if j < 0:
            out.append(tex[i:])
            break
        out.append(tex[i:j])

        # ── Parse the (possibly brace-nested) column specification ──────────
        k = j + len(opener)
        while k < len(tex) and tex[k] in " \t\n":
            k += 1
        if k < len(tex) and tex[k] == "[":
            k = tex.index("]", k) + 1
            while k < len(tex) and tex[k] in " \t\n":
                k += 1
        if k >= len(tex) or tex[k] != "{":
            out.append(tex[j:j + len(opener)])
            i = j + len(opener)
            continue

        depth = 0
        spec_end = k
        while spec_end < len(tex):
            ch = tex[spec_end]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    break
            spec_end += 1
        spec_end += 1  # position just after the closing brace

        end = tex.find(closer, spec_end)
        if end < 0:                      # malformed — copy verbatim
            out.append(tex[j:])
            break

        body = _terminate_caption(tex[spec_end:end])
        if "\\endhead" in body:
            # A table may declare an empty \endfirsthead/\endhead pair (the
            # original Chapter 2 tables did).  Fill it from the real head so
            # the continuation pages still repeat the column titles.
            out.append(tex[j:spec_end] + _refresh_continuation_head(body) + closer)
            i = end + len(closer)
            continue

        new_body = _with_repeated_header(body)
        out.append(tex[j:spec_end] + new_body + closer)
        i = end + len(closer)

    return "".join(out)


def _caption_span(body: str, pos: int):
    """Return ``(end_index, label_end_index)`` for a ``\\caption`` at ``pos``.

    ``end_index`` is the index just after the closing brace; ``label_end_index``
    also swallows an immediately following ``\\label{...}``.  Returns
    ``(None, None)`` when there is no caption at ``pos``.
    """
    import re

    if not body.startswith("\\caption", pos):
        return None, None
    k = pos + len("\\caption")
    while k < len(body) and body[k] in " \t\n":
        k += 1
    if k < len(body) and body[k] == "[":
        k = body.index("]", k) + 1
        while k < len(body) and body[k] in " \t\n":
            k += 1
    if k >= len(body) or body[k] != "{":
        return None, None
    depth = 0
    while k < len(body):
        if body[k] == "{":
            depth += 1
        elif body[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    caption_end = k + 1

    label_end = caption_end
    m = re.match(r"\s*", body[label_end:])
    p = label_end + m.end()
    if body.startswith("\\label", p):
        brace = body.find("{", p)
        if brace != -1:
            depth = 0
            q = brace
            while q < len(body):
                if body[q] == "{":
                    depth += 1
                elif body[q] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                q += 1
            label_end = q + 1
    return caption_end, label_end


def _terminate_caption(body: str) -> str:
    """Ensure a ``\\caption`` row is terminated with ``\\\\``.

    In ``longtable`` the caption is a table row, so it must end with ``\\\\``
    before the following ``\\hline``.  Without it LaTeX reports a cascade of
    ``Misplaced \\noalign`` / ``Extra alignment tab`` errors and the header
    block is corrupted (this was the root cause of the broken page breaks).
    """
    import re

    m = re.match(r"\s*", body)
    pos = m.end()
    caption_end, label_end = _caption_span(body, pos)
    if caption_end is None:
        return body

    segment = body[label_end:]
    next_hline = segment.find("\\hline")
    if next_hline == -1 or "\\\\" in segment[:next_hline]:
        return body
    return body[:label_end] + "\\\\" + body[label_end:]


def _with_repeated_header(body: str) -> str:
    import re

    m = re.match(r"\s*", body)
    pos = m.end()

    caption = ""
    caption_end, label_end = _caption_span(body, pos)
    if caption_end is not None:
        caption = body[pos:label_end]
        pos = label_end

    # A caption terminated by ``\\`` (normalised by _terminate_caption) is
    # still followed by the header block.
    m = re.match(r"\s*", body[pos:])
    pos += m.end()
    if body.startswith("\\\\", pos):
        pos += 2
        m = re.match(r"\s*", body[pos:])
        pos += m.end()

    m = re.match(r"\s*", body[pos:])
    pos += m.end()
    if not body.startswith("\\hline", pos):
        return body                       # not the expected shape — leave alone

    after_first = body[pos + len("\\hline"):]
    second = after_first.find("\\hline")
    if second < 0:
        return body

    header_rows = after_first[:second]
    tail = after_first[second + len("\\hline"):]

    parts = []
    if caption:
        # The caption is a longtable row and must end with \\\.
        parts.append(caption + "\\\\")
    parts.append("\\hline" + header_rows + "\\hline")
    parts.append("\\endfirsthead")
    if caption:
        parts.append("\\caption[]{%s (continued)}\\\\" % _caption_text(caption))
    parts.append("\\hline" + header_rows + "\\hline")
    parts.append("\\endhead")
    return "\n".join(parts) + "\n" + tail


def _first_head(body: str):
    """Return ``(caption, header_rows)`` from the table's first-page head.

    ``header_rows`` is the text between the first pair of ``\\hline`` rules
    after the (optional) caption; it includes the trailing ``\\\\`` of every
    row.  Returns ``(None, None)`` when the shape is not recognised.
    """
    import re

    pos = re.match(r"\s*", body).end()
    caption = ""
    caption_end, label_end = _caption_span(body, pos)
    if caption_end is not None:
        caption = body[pos:label_end]
        pos = label_end
    # A caption row is terminated by ``\\``.
    m = re.match(r"\s*", body[pos:])
    pos += m.end()
    if body.startswith("\\\\", pos):
        pos += 2
        pos += re.match(r"\s*", body[pos:]).end()
    if not body.startswith("\\hline", pos):
        return None, None
    after = body[pos + len("\\hline"):]
    second = after.find("\\hline")
    if second < 0:
        return None, None
    return caption, after[:second]


def _refresh_continuation_head(body: str) -> str:
    """Ensure the ``\\endhead`` block actually contains the column titles.

    Tables written by hand sometimes carry ``\\endfirsthead`` and ``\\endhead``
    with nothing between them, so a table that spans a page loses its column
    headings on the continuation page.  The block is rebuilt from the
    first-page head, and the caption is repeated with a "(continued)" suffix.
    """
    ef = body.find("\\endfirsthead")
    if ef < 0:
        return body
    eh = body.find("\\endhead", ef)
    if eh < 0:
        return body

    cont = body[ef + len("\\endfirsthead"):eh]
    if "&" in cont:
        return body                       # already carries a header row

    caption, rows = _first_head(body[:ef])
    if rows is None or "&" not in rows:
        return body

    block = ["\n"]
    if caption:
        block.append("\\caption[]{%s (continued)}\\\\\n" % _caption_text(caption))
    block.append("\\hline" + rows + "\\hline\n")
    return (body[:ef + len("\\endfirsthead")]
            + "".join(block)
            + body[eh:])


def _caption_text(caption_tex: str) -> str:
    """Extract the braces argument of ``\\caption{...}`` (drops a short form)."""
    start = caption_tex.find("{")
    if start < 0:
        return ""
    depth = 0
    for k in range(start, len(caption_tex)):
        if caption_tex[k] == "{":
            depth += 1
        elif caption_tex[k] == "}":
            depth -= 1
            if depth == 0:
                return caption_tex[start + 1:k]
    return ""


# ---------------------------------------------------------------------------
# Figure block
# ---------------------------------------------------------------------------

def figure(path: str, caption: str, label: Optional[str] = None,
           width: Optional[str] = None) -> str:
    """Embed an image with a consistent caption style and stay-close rule."""
    w = width or REPORT_STYLE.figures.default_width
    p = path.replace("\\", "/")
    lab = (r"\label{%s}" % label) if label else ""
    return (
        "\\begin{figure}[H]\n"
        "\\centering\n"
        "\\includegraphics[width=" + w + ",keepaspectratio]{" + p + "}\n"
        "\\caption*{" + caption + "}\n"
        + lab + "\n"
        "\\end{figure}\n"
        "\\FloatBarrier\n"
    )


# ---------------------------------------------------------------------------
# matplotlib theme (charts share the document palette)
# ---------------------------------------------------------------------------

def apply_chart_theme():
    """Apply the report palette/typography to matplotlib. Safe to call twice."""
    import matplotlib as mpl

    mpl.use("Agg", force=False)
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": "#" + PALETTE["neutral"],
        "axes.labelcolor": "#" + PALETTE["text"],
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "grid.color": "#" + PALETTE["grid"],
        "grid.linewidth": 0.6,
        "grid.alpha": 0.8,
        "xtick.color": "#" + PALETTE["text"],
        "ytick.color": "#" + PALETTE["text"],
        "figure.dpi": 150,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.08,
    })
