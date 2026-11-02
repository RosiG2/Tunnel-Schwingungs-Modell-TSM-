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
src = BR / "tsm_pg_bindings_phase1.csv"

df = pd.read_csv(src)

# Basis: Normalisierte |Δ|-Stärke (0..1)
df["abs_delta"] = df["delta"].abs()
maxd = float(df["abs_delta"].max()) if (pd.notna(df["abs_delta"]).any() and df["abs_delta"].max() > 0) else 1.0
base = df["abs_delta"] / maxd

# Flags (NaNs → False / leere Strings)
bLB = df.get("bind_b_lb", False).fillna(False)
rLB = df.get("bind_r_lb", False).fillna(False)
bUB = df.get("bind_b_ub", False).fillna(False)
rUB = df.get("bind_r_ub", False).fillna(False)
L_b = df.get("lift_bind_b", "").fillna("").astype(str).str.len() > 0
L_r = df.get("lift_bind_r", "").fillna("").astype(str).str.len() > 0

# Heuristik-Gewichte (konservativ, 0..1 clamp)
score = base.copy()
score += rLB.astype(float)*0.35 + bLB.astype(float)*0.20
score += rUB.astype(float)*0.25 + bUB.astype(float)*0.15
score += L_r.astype(float)*0.30 + L_b.astype(float)*0.15
score = score.clip(0.0, 1.0)

# Output-Frame inkl. abs_delta für Sortierung
out = df[["zone","b_x","r_x","delta","rel_change","rank_abs","rank_rel","abs_delta"]].copy()
out["score"] = score

# Sortierung: score desc, abs_delta desc, rank_rel asc (NaNs ans Ende)
out["rank_rel"] = pd.to_numeric(out["rank_rel"], errors="coerce")
out.sort_values(["score","abs_delta","rank_rel"], ascending=[False, False, True], inplace=True, na_position="last")

# CSV + MD
out.to_csv(BR/"phase1_residuum_scores.csv", index=False)

lines = ["# Phase 1 – Residuum-Score (heuristisch)", ""]
for _, row in out.head(20).iterrows():
    lines.append(f"- {row['zone']}: score={row['score']:.3f} | Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b_x']:.6f} → r={row['r_x']:.6f}")
(BR/"phase1_residuum_scores.md").write_text("\n".join(lines), encoding="utf-8")

# PNG Ranking (Top 15)
top = out.head(15)
plt.figure(figsize=(8.2,5))
plt.barh(list(top["zone"][::-1].astype(str)), list(top["score"][::-1]))
plt.xlabel("Residuum-Score (0..1)")
plt.ylabel("Zone")
plt.title("Phase 1 – Top 15 Residuum-Score")
plt.tight_layout()
plt.savefig(BR/"phase1_residuum_scores.png", dpi=150)
plt.close()

print("[ok] wrote: phase1_residuum_scores.(csv|md|png)")
