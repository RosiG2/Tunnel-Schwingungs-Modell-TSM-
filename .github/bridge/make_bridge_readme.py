#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

BR=Path(__file__).resolve().parents[1]/"bridge"
S=BR/"tsm_symbolic_bridge_v0.1.json"
OUT=BR/"README_symbolic_bridge.md"

b=json.loads(S.read_text(encoding="utf-8"))
rows=[]
for z in b.get("zones",[]):
    rows.append((z["id"], z.get("pg_facet") or "—", {1:"+1",-1:"-1"}.get(z.get("orientation"), "—")))
lines=["# Symbolic Bridge (TSM ↔ PG)","","| Zone | PG-Facet | Orientation |","|---|---|---|"]
for z,f,o in rows: lines.append(f"| {z} | {f} | {o} |")
OUT.write_text("\n".join(lines), encoding="utf-8")
print("[ok] wrote:", OUT)
