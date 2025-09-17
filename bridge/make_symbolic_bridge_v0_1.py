# bridge/make_symbolic_bridge_v0_1.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, time
from pathlib import Path

BR=Path(__file__).resolve().parents[1]/"bridge"
J =BR/"tsm_pg_facets_lifted.json"
OUT=BR/"tsm_symbolic_bridge_v0.1.json"

d=json.loads(J.read_text(encoding="utf-8"))
names=list(map(str,d["names"]))
# tau & core_ub aus Lifts lesen (falls vorhanden)
tau=None; core_ub=None; core_members=[]
for L in d.get("constraints",{}).get("lifts",[]) or []:
    meta=(L.get("meta") or {})
    key = meta.get("key","")
    if key.startswith("p3_zone_lb_") and "note" in meta and "(b-τ)" in meta["note"]:
        # τ rekonstruieren aus note nicht trivial; überspringen
        pass
    if key=="p3_group_core_ub":
        core_ub=float(L.get("c",None))
        core_members=L.get("zones") or []
# Fallback: wir wissen aus Phase 3 die Werte
if core_ub is None: core_ub=0.60
tau = 0.10  # fest aus Phase 3

bridge={
  "version":"0.1",
  "timestamp":int(time.time()),
  "zones":[{"id":z,"aliases":[], "pg_facet": None, "orientation": None} for z in names],
  "groups":[
    {"name":"core","members": core_members or ["kohärent","regulativ"], "lb":0.45, "ub": core_ub}
  ],
  "caps":{
    "per_zone_corridor_tau": tau,
    "min_share_per_zone": d.get("constraints",{}).get("min_share_per_zone", 0.02),
    "upper_bounds": d.get("constraints",{}).get("upper_bounds", [])
  },
  "maps":{
    "tsm_to_pg":[  # Platzhalter zum späteren Füllen
      # {"zone":"kohärent","facet":"<pg_facet_id>","orientation":"+1"}
    ]
  },
  "notes":[
    "Startschema für die gemeinsame symbolische Sprache TSM ↔ Positive Geometry.",
    "Fülle 'pg_facet' & 'orientation' je Zone, sobald die PG-Zuordnung steht."
  ]
}
OUT.write_text(json.dumps(bridge, ensure_ascii=False, indent=2), encoding="utf-8")
print("[ok] wrote:", OUT)
