#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3★ – Summary:
Liest
  - bridge/tsm_pg_r_projected_p3.csv   (r³)
  - bridge/tsm_pg_r_projected.csv      (r★, optional)
  - bridge/tsm_pg_changes.csv          (b, r)
  - bridge/tsm_pg_bindings_phase3_star.csv (Bindings b/r³)
  - bridge/tsm_pg_facets_lifted.json   (für LIFT-Counts)
Schreibt
  - bridge/phase3_r3_vs_rstar.csv
  - bridge/phase3_r3_vs_b.csv
  - bridge/phase3_counts.md
  - bridge/README_exec_summary_phase3_star.md
"""
from pathlib import Path
import json, csv, math
import pandas as pd
import numpy as np

BR = Path(__file__).resolve().parents[1] / "bridge"
p_r3   = BR/"tsm_pg_r_projected_p3.csv"
p_rS   = BR/"tsm_pg_r_projected.csv"           # optional (r★)
p_chg  = BR/"tsm_pg_changes.csv"
p_bind = BR/"tsm_pg_bindings_phase3_star.csv"
p_js   = BR/"tsm_pg_facets_lifted.json"

out_vs_rS = BR/"phase3_r3_vs_rstar.csv"
out_vs_b  = BR/"phase3_r3_vs_b.csv"
out_counts= BR/"phase3_counts.md"
out_exec  = BR/"README_exec_summary_phase3_star.md"

def load_csv_map(path, key="zone", val="r_projected"):
    if not path.exists(): return {}
    df = pd.read_csv(path)
    if key not in df.columns or val not in df.columns: return {}
    return dict(zip(df[key].astype(str), df[val].astype(float)))

def safe_nan(x):
    try: return float(x)
    except: return float("nan")

# --- 1) Inputs
assert p_r3.exists(), f"missing {p_r3}"
r3_df = pd.read_csv(p_r3)  # zone,r_original,r_projected
r3map = dict(zip(r3_df["zone"].astype(str), r3_df["r_projected"].astype(float)))

rSmap = load_csv_map(p_rS, key="zone", val="r_projected")  # may be empty
chg   = pd.read_csv(p_chg)   # zone,b,r,delta,rel_change,rank_abs,rank_rel
chg["zone"] = chg["zone"].astype(str)

# --- 2) Deltas r³ vs r★ und r³ vs b
df = chg[["zone","b","r"]].copy()
df["r_star"] = df["zone"].map(lambda z: rSmap.get(z, np.nan))
df["r3"]     = df["zone"].map(lambda z: r3map.get(z, np.nan))

vs_rS = df[["zone","r_star","r3"]].copy()
vs_rS["delta_r3_minus_rstar"] = vs_rS["r3"] - vs_rS["r_star"]
vs_rS.sort_values("delta_r3_minus_rstar", ascending=False, inplace=True)
vs_rS.to_csv(out_vs_rS, index=False)

vs_b = df[["zone","b","r3"]].copy()
vs_b["delta_r3_minus_b"] = vs_b["r3"] - vs_b["b"]
vs_b.sort_values("delta_r3_minus_b", ascending=False, inplace=True)
vs_b.to_csv(out_vs_b, index=False)

# --- 3) Counts (Bindings + LIFTs)
b_lb = r_lb = b_ub = r_ub = 0
lift_b = lift_r3 = 0
names = []
try:
    bind = pd.read_csv(p_bind)
    b_lb = int((bind.get("bind_b_lb", pd.Series(dtype=bool))==True).sum())
    r_lb = int((bind.get("bind_r3_lb", pd.Series(dtype=bool))==True).sum())
    b_ub = int((bind.get("bind_b_ub", pd.Series(dtype=bool))==True).sum())
    r_ub = int((bind.get("bind_r3_ub", pd.Series(dtype=bool))==True).sum())
except Exception:
    pass

try:
    jd = json.loads(p_js.read_text(encoding="utf-8"))
    names = list(map(str, jd["names"]))
    b_vec = np.array(jd["b"], dtype=float)
    # r³-Vector in names-Reihenfolge
    r3_vec = np.array([r3map.get(z, 0.0) for z in names], dtype=float)
    lifts = jd.get("constraints",{}).get("lifts",[]) or []
    def slack(a,c,x): return float(c)-float(np.dot(np.array(a,dtype=float), x))
    TOL = 1e-9
    for L in lifts:
        a,c=L.get("a"),L.get("c")
        if a is None or c is None: continue
        if abs(slack(a,c,b_vec))  <= TOL: lift_b  += 1
        if abs(slack(a,c,r3_vec)) <= TOL: lift_r3 += 1
except Exception:
    pass

out_counts.write_text(
    "\n".join([
      "# Phase 3★ – Binding Counts",
      "",
      f"- b@LB={b_lb}, r³@LB={r_lb}, b@UB={b_ub}, r³@UB={r_ub}",
      f"- LIFT(b)={lift_b}, LIFT(r³)={lift_r3}"
    ]),
    encoding="utf-8"
)

# --- 4) Heuristische Tuning-Hinweise (aus Counts)
hints = []
total = len(names) if names else None
if total:
    # Anteil r³@UB hoch?
    if r_ub > max(2, total//4):
        hints.append("Viele r³@UB: UB/Margin oder CORE_UB prüfen; ggf. Δ-Korridor (τ) leicht erhöhen.")
    # Anteil r³@LB hoch?
    if r_lb > max(2, total//5):
        hints.append("Viele r³@LB: min_share_per_zone oder Gruppen-Minima prüfen/erhöhen; τ evtl. senken.")
# Delta-Groessenordnung r³ vs r★
if not vs_rS["delta_r3_minus_rstar"].dropna().empty:
    m = vs_rS["delta_r3_minus_rstar"].abs().median()
    if m > 0.08:
        hints.append("Große Abweichung r³ vs r★: Δ-Korridor (τ) zu streng/locker? CORE_UB anpassen.")
if not hints:
    hints.append("Keine auffälligen Spannungen: aktuelle P3-Caps wirken konsistent.")

# --- 5) Executive Summary schreiben
def fmt_row(prefix, row):
    return f"- {row['zone']}: {prefix}={row.iloc[-1]:+.6f}"

top_up_rS   = vs_rS.head(5)
top_down_rS = vs_rS.tail(5).sort_values("delta_r3_minus_rstar", ascending=True)
top_up_b    = vs_b.head(5)
top_down_b  = vs_b.tail(5).sort_values("delta_r3_minus_b", ascending=True)

lines = []
lines.append("# Executive-Summary — Phase 3★ (b → r³)")
lines.append("")
lines.append("## Facetten- & LIFT-Counts")
lines.append(f"- b@LB={b_lb}, r³@LB={r_lb}, b@UB={b_ub}, r³@UB={r_ub}")
lines.append(f"- LIFT(b)={lift_b}, LIFT(r³)={lift_r3}")
lines.append("")
lines.append("## r³ vs r★ — Top-Anhebungen")
for _,r in top_up_rS.iterrows(): lines.append(f"- {r['zone']}: r★={r['r_star']:.6f} → r³={r['r3']:.6f} | Δ={r['delta_r3_minus_rstar']:.6f}")
lines.append("")
lines.append("## r³ vs r★ — Top-Absenkungen")
for _,r in top_down_rS.iterrows(): lines.append(f"- {r['zone']}: r★={r['r_star']:.6f} → r³={r['r3']:.6f} | Δ={r['delta_r3_minus_rstar']:.6f}")
lines.append("")
lines.append("## r³ vs b — Top-Anhebungen")
for _,r in top_up_b.iterrows(): lines.append(f"- {r['zone']}: b={r['b']:.6f} → r³={r['r3']:.6f} | Δ={r['delta_r3_minus_b']:.6f}")
lines.append("")
lines.append("## r³ vs b — Top-Absenkungen")
for _,r in top_down_b.iterrows(): lines.append(f"- {r['zone']}: b={r['b']:.6f} → r³={r['r3']:.6f} | Δ={r['delta_r3_minus_b']:.6f}")
lines.append("")
lines.append("## Artefakte")
lines.append("- Bindings r³: `bridge/tsm_pg_bindings_phase3_star.csv`")
lines.append("- r³ vs r★: `bridge/phase3_r3_vs_rstar.csv`")
lines.append("- r³ vs b:  `bridge/phase3_r3_vs_b.csv`")
lines.append("")
lines.append("## Hinweise (heuristisch)")
for h in hints: lines.append(f"- {h}")

out_exec.write_text("\n".join(lines), encoding="utf-8")
print("[ok] wrote:", out_vs_rS, out_vs_b, out_counts, out_exec)
