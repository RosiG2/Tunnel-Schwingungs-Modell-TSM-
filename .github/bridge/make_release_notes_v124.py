#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, csv, time
from pathlib import Path
import pandas as pd
import numpy as np

BR=Path(__file__).resolve().parents[1]/"bridge"
BUNDLE=BR/"tsm-online-bundle_v1.24.json"
KEYS  = BR/"KEYPOINTS_phase3.md"
BRIDGE=BR/"README_symbolic_bridge.md"
OUT   = BR/"RELEASE_NOTES_v1.24.md"

d=json.loads(BUNDLE.read_text(encoding="utf-8"))
names=d["names"]; b=d["b"]; r=d["r"]; rS=d.get("r_star"); r3=d.get("r3")

def top_deltas(a, b, k=3):
    arr = [(abs(b[i]-a[i]), names[i], a[i], b[i]) for i in range(len(names))]
    arr.sort(reverse=True)
    return arr[:k]

lines=["# Release Notes — v1.24","","## Highlights",
       "- Vollständige Symbolische Brücke (4/4 Zonen).",
       f"- Fixierte Caps: τ=0.10, core_UB=0.60.",
       "- Aktualisierte Artefakte (r³, Wegbericht, Summary, Keypoints, Bundle).",""]

# Deltas
if rS:
    top = top_deltas(rS, r3, k=3)
    lines += ["## Top-Änderungen r³ vs r★"]
    for dlt,z,a,bv in top:
        lines.append(f"- {z}: r★={a:.6f} → r³={bv:.6f} | Δ={bv-a:+.6f}")
    lines.append("")
top = top_deltas(b, r3, k=3)
lines += ["## Top-Änderungen r³ vs b"]
for dlt,z,a,bv in top:
    lines.append(f"- {z}: b={a:.6f} → r³={bv:.6f} | Δ={bv-a:+.6f}")
lines += ["", "## Bridge (TSM ↔ PG)", f"- siehe `{BRIDGE.name}`", "", "## Keypoints", f"- siehe `{KEYS.name}`"]

OUT.write_text("\n".join(lines), encoding="utf-8")
print("[ok] wrote:", OUT)
