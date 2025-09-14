#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Stats for Phase 1 (RGN-Lifts)
- liest: bridge/tsm_pg_bindings_phase1.csv, bridge/facet_activations_phase1.json
- schreibt: bridge/phase1_stats.md, bridge/phase1_stats.json
"""
import json, pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BR   = ROOT / "bridge"

csv_path  = BR / "tsm_pg_bindings_phase1.csv"
json_path = BR / "facet_activations_phase1.json"

df = pd.read_csv(csv_path)
acts = json.loads(json_path.read_text(encoding="utf-8"))

n_zones = len(df)
n_lb_b  = int((df["bind_b_lb"]==True).sum())
n_lb_r  = int((df["bind_r_lb"]==True).sum())
n_ub_b  = int((df["bind_b_ub"]==True).sum())
n_ub_r  = int((df["bind_r_ub"]==True).sum())

# Lifts
n_lifts_total = len(acts)
n_lifts_bind_b = sum(1 for a in acts if bool(a.get("bind_b")))
n_lifts_bind_r = sum(1 for a in acts if bool(a.get("bind_r")))

# Top deltas
df["abs_delta"] = df["delta"].abs()
top = df.sort_values(["abs_delta","rank_rel"], ascending=[False, True]).head(10)
top_rows = [
    dict(zone=row.zone, b=float(row.b_x), r=float(row.r_x), delta=float(row.delta), rel_change=float(row.rel_change))
    for _, row in top.iterrows()
]

# JSON
stats = dict(
    zones=n_zones,
    binds=dict(lb_b=n_lb_b, lb_r=n_lb_r, ub_b=n_ub_b, ub_r=n_ub_r),
    lifts=dict(total=n_lifts_total, bind_b=n_lifts_bind_b, bind_r=n_lifts_bind_r),
    top10=top_rows
)
(BR / "phase1_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

# MD
lines = []
lines.append("# Phase 1 – Quick Stats")
lines.append("")
lines.append(f"- Zonen: **{n_zones}**")
lines.append(f"- Facettenkontakte (LB/UB): b@LB={n_lb_b}, r@LB={n_lb_r}, b@UB={n_ub_b}, r@UB={n_ub_r}")
lines.append(f"- Lifts: total={n_lifts_total}, b-gebunden={n_lifts_bind_b}, r-gebunden={n_lifts_bind_r}")
lines.append("")
lines.append("## Top-10 |Δ| (b → r)")
for t in top_rows:
    lines.append(f"- {t['zone']}: Δ={t['delta']:.6f} | rel={t['rel_change']:.3f} | b={t['b']:.6f} → r={t['r']:.6f}")
(BR / "phase1_stats.md").write_text("\n".join(lines), encoding="utf-8")

print("[ok] Wrote: bridge/phase1_stats.md + bridge/phase1_stats.json")
