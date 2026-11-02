#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, csv
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
S  = BR / "tsm_symbolic_bridge_v0.1.json"
OUT= BR / "pg_crosswalk.csv"

b = json.loads(S.read_text(encoding="utf-8"))
rows = []
for z in b.get("zones", []):
    rows.append({
        "zone": z["id"],
        "pg_facet": z.get("pg_facet") or "",
        "orientation": z.get("orientation", "")
    })
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["zone","pg_facet","orientation"])
    w.writeheader(); w.writerows(rows)
print("[ok] wrote:", OUT)
