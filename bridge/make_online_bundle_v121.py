#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut ein Online-Bundle (v1.21) mit b, r (aus changes), r★ (falls vorhanden), r³ (Phase 3),
inkl. Constraints & kleinen Tops-Listen.
Schreibt: bridge/tsm-online-bundle_v1.21.json
"""
import json, csv, time
from pathlib import Path
import pandas as pd

BR = Path(__file__).resolve().parents[1] / "bridge"
J   = BR / "tsm_pg_facets_lifted.json"
CHG = BR / "tsm_pg_changes.csv"
RSTAR = BR / "tsm_pg_r_projected.csv"          # optional
R3    = BR / "tsm_pg_r_projected_p3.csv"
VS_RS = BR / "phase3_r3_vs_rstar.csv"          # optional
VS_B  = BR / "phase3_r3_vs_b.csv"              # optional
OUT   = BR / "tsm-online-bundle_v1.21.json"

d = json.loads(J.read_text(encoding="utf-8"))
names = list(map(str, d["names"]))
b_vec = list(map(float, d["b"]))

chg = pd.read_csv(CHG)  # zone,b,r,...
chg["zone"] = chg["zone"].astype(str)
r_changes = {z: float(v) for z, v in zip(chg["zone"], chg["r"])}

rstar = {}
if RSTAR.exists():
    df = pd.read_csv(RSTAR)
    rstar = {str(z): float(v) for z, v in zip(df["zone"], df["r_projected"])}

r3 = {}
if R3.exists():
    df = pd.read_csv(R3)
    r3 = {str(z): float(v) for z, v in zip(df["zone"], df["r_projected"])}

# Tops (optional)
def read_top(path, key, k=10, reverse=True, cols=None):
    if not path.exists(): return []
    df = pd.read_csv(path)
    if key not in df.columns: return []
    df = df.copy()
    df = df.sort_values(key, ascending=not reverse).head(k)
    out = []
    for _,row in df.iterrows():
        item = {"zone": str(row["zone"])}
        for c in (cols or []):
            if c in df.columns:
                try: item[c] = float(row[c])
                except: item[c] = None
        out.append(item)
    return out

top_r3_vs_rS_up   = read_top(VS_RS, "delta_r3_minus_rstar", k=10, reverse=True,  cols=["r_star","r3","delta_r3_minus_rstar"])
top_r3_vs_rS_down = read_top(VS_RS, "delta_r3_minus_rstar", k=10, reverse=False, cols=["r_star","r3","delta_r3_minus_rstar"])
top_r3_vs_b_up    = read_top(VS_B,  "delta_r3_minus_b",     k=10, reverse=True,  cols=["b","r3","delta_r3_minus_b"])
top_r3_vs_b_down  = read_top(VS_B,  "delta_r3_minus_b",     k=10, reverse=False, cols=["b","r3","delta_r3_minus_b"])

bundle = {
    "version": "1.21",
    "timestamp": int(time.time()),
    "names": names,
    "b": [float(b) for b in b_vec],
    "r": [float(r_changes.get(z, 0.0)) for z in names],
    "r_star": [float(rstar.get(z, 0.0)) for z in names] if rstar else None,
    "r3": [float(r3.get(z, 0.0)) for z in names] if r3 else None,
    "constraints": d.get("constraints", {}),
    "meta": {
        "source": "TSM <-> Positive Geometry (Phase 3★)",
        "notes": d.get("meta", {}).get("notes", []),
        "margin": d.get("meta", {}).get("margin", None)
    },
    "tops": {
        "r3_vs_rstar_up":   top_r3_vs_rS_up,
        "r3_vs_rstar_down": top_r3_vs_rS_down,
        "r3_vs_b_up":       top_r3_vs_b_up,
        "r3_vs_b_down":     top_r3_vs_b_down
    }
}

OUT.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
print("[ok] wrote:", OUT)
