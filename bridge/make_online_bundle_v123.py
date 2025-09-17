#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baut ein Online-Bundle v1.23 (b, r, r★, r3, constraints, symbolic_bridge).
"""
import json, time, pandas as pd
from pathlib import Path

BR   = Path(__file__).resolve().parents[1] / "bridge"
JTSM = BR / "tsm_pg_facets_lifted.json"
CHG  = BR / "tsm_pg_changes.csv"
RSTAR= BR / "tsm_pg_r_projected.csv"
R3   = BR / "tsm_pg_r_projected_p3.csv"
SBR  = BR / "tsm_symbolic_bridge_v0.1.json"
OUT  = BR / "tsm-online-bundle_v1.23.json"

d = json.loads(JTSM.read_text(encoding="utf-8"))
names = list(map(str, d["names"]))
b_vec = list(map(float, d["b"]))

chg = pd.read_csv(CHG); chg["zone"]=chg["zone"].astype(str)
r_changes = dict(zip(chg["zone"], chg["r"]))

rstar = {}
if RSTAR.exists():
    df = pd.read_csv(RSTAR)
    rstar = dict(zip(df["zone"].astype(str), df["r_projected"].astype(float)))

r3 = {}
if R3.exists():
    df = pd.read_csv(R3)
    r3 = dict(zip(df["zone"].astype(str), df["r_projected"].astype(float)))

symb = json.loads(SBR.read_text(encoding="utf-8")) if SBR.exists() else None

bundle = {
    "version": "1.23",
    "timestamp": int(time.time()),
    "names": names,
    "b": [float(x) for x in b_vec],
    "r": [float(r_changes.get(z,0.0)) for z in names],
    "r_star": [float(rstar.get(z,0.0)) for z in names] if rstar else None,
    "r3": [float(r3.get(z,0.0)) for z in names] if r3 else None,
    "constraints": d.get("constraints", {}),
    "meta": d.get("meta", {}),
    "symbolic_bridge": symb
}

OUT.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
print("[ok] wrote:", OUT)
