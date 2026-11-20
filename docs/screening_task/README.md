# OsdagBridge LaTeX Report Generator — Refactoring & Enhancements

Screening-task submission for the FOSSEE Winter Internship 2026 (Osdag / OsdagBridge).

## Deliverables in this folder

| File | Contents |
| --- | --- |
| `Report_Before.pdf` | Report produced by the unmodified generator (commit `d74f56d`). 48 pages, 138 LaTeX errors, 61 overfull boxes, 2/49 longtables with repeating headers. |
| `Report_After.pdf` | Report produced by this branch. 47 pages, 0 LaTeX errors, 0 overfull boxes, 51/51 longtables with repeating headers, utilization-ratio chart in §5.5, material charts in Chapter 7, no content in the footer box on any page. |
| `technical_changes.pdf` | Technical Changes Document: what changed, why, before/after metrics, reproduction steps, limitations. |
| `technical_changes.tex` | LaTeX source of the above. |

Both PDFs were generated from **the same 30 m, four-girder dataset**, so every
difference between them is caused by the code changes.

## What changed

1. **Repeating table headers** — `theme.longtable()` emits `\endfirsthead` /
   `\endhead` blocks; `theme.repeat_longtable_headers()` applies the same structure
   to every pre-existing longtable at document level. Continuation pages repeat the
   caption with a "(continued)" suffix. 50/50 tables fixed.
2. **Layout and footer overlap** — geometry, margins, head height and cell padding
   live in `theme.py`; `\needspace` guards stop tables starting in the last three
   lines of a page; `theme.flatten_breakable_multirows()` removes page-break-unsafe
   `\multirow` group labels (the "G4 bleeding into the footer" defect).
3. **Load tables** — Chapter 3 now has separate *Vehicular Live Load* and *Footway
   Live Load* tables with explicit unit columns, driven by the vehicles selected in
   the UI.
4. **Utilization-ratio chart** — four-category UR bar chart (girders, deck slab,
   cross bracing, end diaphragms) with a red dashed limit line at UR = 1.0, embedded
   in §5.5.
5. **Material quantity charts** — steel tonnage by element (girders, cross
   bracing, end diaphragms, shear studs) and deck concrete vs reinforcement
   weight, generated at report time and embedded in Chapter 7. End-diaphragm
   tonnage is now calculated by the BOQ generator instead of being absent.
6. **Centralized styles** — `src/osdagbridge/core/reports/theme.py` is the single
   source of formatting; chapter modules carry content only.

Also fixed while verifying: a crash in `IRC6_2017.cl_211_2_braking_force()` that
made braking force print as `N/A` (and its newton/tonne mix-up), a stale
"Page X of Y" total, a footer-less references page, and the slenderness check
inflating the cross-bracing utilization ratio.

## Reproducing the PDFs

The design engine requires `openseespy`, which has no wheel for Python 3.14, so the
reports are produced headlessly with an inert OpenSees stub.

```bash
# after
python tools/report_demo/generate_demo_report.py --out out --stem Report_After

# before (pristine checkout, same dataset)
git worktree add ../baseline d74f56d
cp -r tools/report_demo ../baseline/tools/
python ../baseline/tools/report_demo/generate_demo_report.py --out out --stem Report_Before
```

A LaTeX installation with `pdflatex` plus `longtable`, `booktabs`, `makecell`,
`fancyhdr`, `titlesec`, `caption`, `float`, `placeins`, `needspace` and
`etoolbox` is required. Both runs write the `.tex` and `.pdf` and report LaTeX
errors found in the log.

## Items the applicant must complete outside the code

- Push this branch and share the repository link.
- Add `Nidhikhare12` as a collaborator on the repository.
- Record the short screen-capture video walking through the changes.
