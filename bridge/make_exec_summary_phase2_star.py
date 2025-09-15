python - <<'PY'
from pathlib import Path
content = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Executive-Summary für Phase 2★:
- liest:  bridge/phase2_star_counts.md
          bridge/tsm_pg_rstar_vs_r.csv
          bridge/wegbericht_b_to_r_star.md (optional)
- schreibt: bridge/README_exec_summary_phase2_star.md
"""
from pathlib import Path
import re, csv

BR = Path(__file__).resolve().parents[1] / "bridge"
counts_md = BR / "phase2_star_counts.md"
delta_csv  = BR / "tsm_pg_rstar_vs_r.csv"
weg_md     = BR / "wegbericht_b_to_r_star.md"
out_md     = BR / "README_exec_summary_phase2_star.md"

# --- Counts parsen
b_lb = r_lb = b_ub = r_ub = lift_b = lift_r = None
if counts_md.exists():
    txt = counts_md.read_text(encoding="utf-8")
    m1 = re.search(r"b@LB=(\\d+),\\s*r★@LB=(\\d+),\\s*b@UB=(\\d+),\\s*r★@UB=(\\d+)", txt)
    m2 = re.search(r"LIFT\\(b\\)=(\\d+),\\s*LIFT\\(r★\\)=(\\d+)", txt)
    if m1: b_lb, r_lb, b_ub, r_ub = map(int, m1.groups())
    if m2: lift_b, lift_r = map(int, m2.groups())

# --- r★ vs r Top-Deltas
top_up, top_down = [], []
if delta_csv.exists():
    with delta_csv.open("r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        rows = list(rdr)
        for row in rows:
            for k in ("r_projected","r_changes","delta_rstar_minus_r"):
                try:
                    row[k] = float(row.get(k) or "nan")
                except Exception:
                    row[k] = float("nan")
        ups   = [r for r in rows if r["delta_rstar_minus_r"] >= 0]
        downs = [r for r in rows if r["delta_rstar_minus_r"] <  0]
        ups.sort(key=lambda r: r["delta_rstar_minus_r"], reverse=True)
        downs.sort(key=lambda r: r["delta_rstar_minus_r"])
        top_up, top_down = ups[:5], downs[:5]

def fmt_delta(row):
    return f"- {row.get('zone','?')}: r={row['r_changes']:.6f} → r★={row['r_projected']:.6f} | Δ={row['delta_rstar_minus_r']:.6f}"

# --- Wegbericht-Hinweis (optional)
weg_hint = "- Wegbericht b→r★: `bridge/wegbericht_b_to_r_star.md`" if weg_md.exists() else ""

# --- Output schreiben
lines = ["# Executive-Summary — Phase 2★ (b → r★)", ""]

if None not in (b_lb, r_lb, b_ub, r_ub, lift_b, lift_r):
    lines += [
        "## Facetten- & LIFT-Counts",
        f"- b@LB={b_lb}, r★@LB={r_lb}, b@UB={b_ub}, r★@UB={r_ub}",
        f"- LIFT(b)={lift_b}, LIFT(r★)={lift_r}",
        ""
    ]
else:
    lines += ["_Hinweis: Counts nicht gefunden (phase2_star_counts.md fehlt?)._", ""]

lines.append("## r★ vs r — Top-Anhebungen")
lines += [fmt_delta(r) for r in top_up] or ["- (keine Daten)"]
lines.append("")
lines.append("## r★ vs r — Top-Absenkungen")
lines += [fmt_delta(r) for r in top_down] or ["- (keine Daten)"]
lines += [
    "",
    "## Artefakte",
    "- Bindings r★: `bridge/tsm_pg_bindings_phase2_star.csv`",
    "- r★ vs r (voll): `bridge/tsm_pg_rstar_vs_r.csv`",
    "- Residuum r★: `bridge/phase2_star_residuum_scores.(csv|md)`"
]
if weg_hint: lines.append(weg_hint)

out_md.write_text("\\n".join(lines), encoding="utf-8")
print("[ok] wrote:", out_md)
'''
Path('bridge/make_exec_summary_phase2_star.py').write_text(content, encoding='utf-8')
print("[ok] wrote clean file bridge/make_exec_summary_phase2_star.py")
PY
