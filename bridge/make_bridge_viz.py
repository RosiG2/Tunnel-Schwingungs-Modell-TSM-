#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BR   = Path(__file__).resolve().parents[1] / "bridge"
JTSM = BR / "tsm_pg_facets_lifted.json"
CHG  = BR / "tsm_pg_changes.csv"
RSTAR= BR / "tsm_pg_r_projected.csv"
R3   = BR / "tsm_pg_r_projected_p3.csv"
OUT  = BR / "bridge_viz_b_r_rstar_r3.png"

d = json.loads(JTSM.read_text(encoding="utf-8"))
names = list(map(str, d["names"]))
b_vec = list(map(float, d["b"]))

chg = pd.read_csv(CHG); chg["zone"]=chg["zone"].astype(str)
r_changes = dict(zip(chg["zone"], chg["r"]))

r_star = {}
if RSTAR.exists():
    df = pd.read_csv(RSTAR)
    r_star = dict(zip(df["zone"].astype(str), df["r_projected"].astype(float)))

r3 = {}
if R3.exists():
    df = pd.read_csv(R3)
    r3 = dict(zip(df["zone"].astype(str), df["r_projected"].astype(float)))

df = pd.DataFrame({
    "zone": names,
    "b": [b for b in b_vec],
    "r": [r_changes.get(z, 0.0) for z in names],
    "r_star": [r_star.get(z, float("nan")) if r_star else float("nan") for z in names],
    "r3": [r3.get(z, float("nan")) if r3 else float("nan") for z in names],
})
df.set_index("zone", inplace=True)

# Plot
fig, ax = plt.subplots(figsize=(8,4.5), dpi=160)
cols = ["b","r","r_star","r3"]
x = np.arange(len(df.index))
w = 0.2
for i,c in enumerate(cols):
    ax.bar(x + (i-1.5)*w, df[c].values, width=w, label=c)
ax.set_xticks(x); ax.set_xticklabels(df.index, rotation=0)
ax.set_ylim(0, 1.0)
ax.set_ylabel("share")
ax.set_title("TSM shares: b / r / r★ / r³")
ax.legend(ncol=4, frameon=False, fontsize=8, loc="upper center")
fig.tight_layout()
fig.savefig(OUT)
print("[ok] wrote:", OUT)
