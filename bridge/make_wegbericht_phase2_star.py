#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2★: Wegbericht + Bindings + Scores für b -> r* (projektiert, constraints-feasible)

Liest:
  - bridge/tsm_pg_changes.csv           (enthält b, r, delta, rel_change, ranks)
  - bridge/tsm_pg_r_projected.csv       (zone, r_original, r_projected)
  - bridge/tsm_pg_facets_lifted.json    (names, b, r, constraints.upper_bounds, constraints.lifts)

Schreibt:
  - bridge/wegbericht_b_to_r_star.md
  - bridge/tsm_pg_bindings_phase2_star.csv
  - bridge/phase2_star_residuum_scores.(csv|md|png)
"""
import json, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
chg_csv   = BR / "tsm_pg_changes.csv"
rstar_csv = BR / "tsm_pg_r_projected.csv"
lifted_js = BR / "tsm_pg_facets_lifted.json"

TOL = 1e-9
def eval_ineq(a,c,x): return float(c) - float(np.dot(np.array(a, dtype=float), x))

# --- Load
chg   = pd.read_csv(chg_csv)                         # zone,b,r,delta,rel_change,rank_abs,rank_rel
rproj = pd.read_csv(rstar_csv)                       # zone,r_original,r_projected
lifted = json.loads(lifted_js.read_text(encoding="utf-8"))

names = lifted["names"]
b_vec = np.array(lifted["b"], dtype=float)
# ersetze r durch r* NUR für Bindings/Facetten
rstar_map = dict(zip(rproj["zone"].astype(str), rproj["r_projected"].astype(float)))
rstar_vec = np.array([rstar_map.get(z, 0.0) for z in names], dtype=float)

# UB-Map
ub_map = {}
for ub in lifted.get("constraints", {}).get("upper_bounds", []):
    ub_map[names[ub["i"]]] = float(ub["c"])

# Bindings (LB/UB mit r*)
rows = []
for i, z in enumerate(names):
    bi = float(b_vec[i]); ri = float(rstar_vec[i]); ub = ub_map.get(z, 1.0)
    rows.append(dict(zone=z, b_x=bi, rstar_x=ri,
                     bind_b_lb=(bi<=TOL), bind_rstar_lb=(ri<=TOL),
                     ub=ub, bind_b_ub=((ub-bi)<=1e-9), bind_rstar_ub=((ub-ri)<=1e-9)))
bind = pd.DataFrame(rows)

# Lifts b/r* (welche Ungleichungen binden an b bzw. r*?)
lifts = lifted.get("constraints", {}).get("lifts", [])
def involved_zones(L, names):
    if L.get("scope")=="zone" and L.get("zone") in names: return [L["zone"]]
    if L.get("zones"): return [z for z in L["zones"] if z in names]
    a=L.get("a") or []; return [names[j] for j,v in enumerate(a) if abs(float(v))>0]

act_rows=[]
for i,L in enumerate(lifts):
