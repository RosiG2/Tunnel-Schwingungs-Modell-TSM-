#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Residuum-Score (heuristisch) je Zone aus Phase-1-Daten.
Liest:  bridge/tsm_pg_bindings_phase1.csv  (enthält lift_bind_b/lift_bind_r)
Schreibt:
  - bridge/phase1_residuum_scores.csv
  - bridge/phase1_residuum_scores.md
  - bridge/phase1_residuum_scores.png
"""
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
df = pd.read_csv(BR/"tsm_pg_bindings_phase1.csv")

# Basis: Normalisierte |Δ|-Stärke (0..1)
df["abs_delta"] = df["delta"].abs()
maxd = df["abs_delta"].max() if (df["abs_delta"].max()>0) else 1.0
base = df["abs_delta"] / maxd

# Flags
bLB = df["bind_b_lb"].fillna(False)
rLB = df["bind_r_lb"].fillna(False)
bUB = df["bind_b_ub"].fillna(False)
rUB = df["bind_r_ub"].fillna(False)
L_b = df["lift_bind_b"].fillna("").astype(str).str.len() > 0
L_r = df["lift_bind_r"].fillna("").astype(str).str.len() > 0

# Heuristik-Gewichte (konservativ, 0..1 clamp)
score = base
score += rLB.astype(float)*0.35 + bLB.astype(float)*0.20
score += rUB.astype(float)*0.25 + bUB.astype(float)*0.15
score += L_r.astype(float)*0.30 + L_b.astype(float)*0.15
score = score.clip(0.0, 1.0)

out = df[["zone","b_x","r_x","delta","rel_change","rank_abs","rank_rel"]].copy()
out["score"] = score
out.sort_values(["score","abs_delta","rank_rel"], ascending=[False, False, True], inplace=True)

# CSV + MD
out.to_csv(BR/"phase1_residuum_scores.csv", index=False)

lines = ["# Phase 1 – Residuum-Score (heuristisch)", ""]
for _, row in out.head(20).iterrows():
    lines.append(f"- {row['zone']}: score={row['score']:.3f} | Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b_x']:.6f} → r={row['r_x']:.6f}")
(BR/"phase1_residuum_scores.md").write_text("\n".join(lines), encoding="utf-8")

# PNG Ranking (Top 15)
top = out.head(15)
plt.figure(figsize=(8.2,5))
plt.barh(list(top["zone"][::-1]), list(top["score"][::-1]))
plt.xlabel("Residuum-Score (0..1)")
plt.ylabel("Zone")
plt.title("Phase 1 – Top 15 Residuum-Score")
plt.tight_layout()
plt.savefig(BR/"phase1_residuum_scores.png", dpi=150)
plt.close()

print("[ok] wrote: phase1_residuum_scores.(csv|md|png)")
