#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt eine Balkengrafik mit den Counts der Bindings:
- b@LB, r@LB, b@UB, r@UB aus tsm_pg_bindings_phase1.csv
- LIFT(b), LIFT(r) aus facet_activations_phase1.json
Schreibt:
  - bridge/phase1_binding_counts.png
  - bridge/phase1_binding_counts.md
"""
import json, pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
csv_path  = BR / "tsm_pg_bindings_phase1.csv"
acts_path = BR / "facet_activations_phase1.json"

df = pd.read_csv(csv_path)
acts = json.loads(acts_path.read_text(encoding="utf-8"))

b_lb = int((df["bind_b_lb"]==True).sum())
r_lb = int((df["bind_r_lb"]==True).sum())
b_ub = int((df["bind_b_ub"]==True).sum())
r_ub = int((df["bind_r_ub"]==True).sum())

lift_b = sum(1 for a in acts if bool(a.get("bind_b")))
lift_r = sum(1 for a in acts if bool(a.get("bind_r")))

labels = ["b@LB","r@LB","b@UB","r@UB","LIFT(b)","LIFT(r)"]
values = [b_lb, r_lb, b_ub, r_ub, lift_b, lift_r]

plt.figure(figsize=(7,4.5))
plt.bar(labels, values)
plt.title("Phase 1 – Facetten- & LIFT-Bindings (Counts)")
plt.xlabel("Binding-Typ")
plt.ylabel("Anzahl")
plt.tight_layout()
out_png = BR / "phase1_binding_counts.png"
plt.savefig(out_png, dpi=150)
plt.close()

md = [
  "# Phase 1 – Binding Counts",
  "",
  f"- b@LB={b_lb}, r@LB={r_lb}, b@UB={b_ub}, r@UB={r_ub}",
  f"- LIFT(b)={lift_b}, LIFT(r)={lift_r}",
  "",
  "![Binding Counts](phase1_binding_counts.png)"
]
(BR / "phase1_binding_counts.md").write_text("\n".join(md), encoding="utf-8")
print(f"[ok] wrote {out_png} and phase1_binding_counts.md")
