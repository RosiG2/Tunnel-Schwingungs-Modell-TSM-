cat > bridge/make_exec_summary_phase2_star.py <<'PY'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt eine kompakte Executive-Summary für Phase 2★:
- liest:  bridge/phase2_star_counts.md
          bridge/tsm_pg_rstar_vs_r.csv
          bridge/wegbericht_b_to_r_star.md  (optional, wenn vorhanden)
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
        # sicherstellen, dass Felder da sind
        for row in rows:
            for k in ["r_projected","r_changes","delta_rstar_minus_r"]:
                row[k] = float(row.get(k, "nan") or "nan")
        # sortiert war schon absteigend; wir bilden explizit top5±
        ups   = [r for r in rows if r["delta_rstar_minus_r"] >= 0]
        downs = [r for r in rows if r["delta_rstar_minus_r"] <  0]
        ups.sort(key=lambda r: r["delta_rstar_minus_r"], reverse=True)
        downs.sort(key=lambda r: r["delta_rstar_minus_r"])
        top_up   = ups[:5]
        top_down = downs[:5]

def fmt_delta(row):
    z = row.get("zone","?")
    d = row["delta_rstar_minus_r"]
    ro = row["r_changes"]
    rp = row["r_projected"]
    return f"- {z}: r={ro:.6f} → r★={rp:.6f} | Δ={d:.6f}"

# --- Wegbericht-Hinweis (optional)
weg_hint = ""
if weg_md.exists():
    # Nur als Verlinkungshinweis im Text nennen
    weg_hint = "- Wegbericht b→r★: `bridge/wegbericht_b_to_r_star.md`"

# --- Output schreiben
lines = []
lines.append("# Executive-Summary — Phase 2★ (b → r★)")
lines.append("")
if None not in (b_lb, r_lb, b_ub, r_ub, lift_b, lift_r):
    lines.append("## Facetten- & LIFT-Counts")
    lines.append(f"- b@LB={b_lb}, r★@LB={r_lb}, b@UB={b_ub}, r★@UB={r_ub}")
    lines.append(f"- LIFT(b)={lift_b}, LIFT(r★)={lift_r}")
    lines.append("")
else:
    lines.append("_Hinweis: Counts nicht gefunden (phase2_star_counts.md fehlt?)._")
    lines.append("")

lines.append("## r★ vs r — Top-Anhebungen")
lines += [fmt_delta(r) for r in top_up]
if not top_up: lines.append("- (keine Daten)")
lines.append("")
lines.append("## r★ vs r — Top-Absenkungen")
lines += [fmt_delta(r) for r in top_down]
if not top_down: lines.append("- (keine Daten)")
lines.append("")
lines.append("## Artefakte")
lines.append("- Bindings r★: `bridge/tsm_pg_bindings_phase2_star.csv`")
lines.append("- r★ vs r (voll): `bridge/tsm_pg_rstar_vs_r.csv`")
lines.append("- Residuum r★: `bridge/phase2_star_residuum_scores.(csv|md)`")
if weg_hint: lines.append(weg_hint)

out_md.write_text("\\n".join(lines), encoding="utf-8")
print("[ok] wrote:", out_md)
PY
chmod +x bridge/make_exec_summary_phase2_star.py
