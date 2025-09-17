#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validiert tsm_symbolic_bridge_v0.1.json gegen TSM-Namen
und schreibt einen kurzen Report: tsm_symbolic_bridge_report.md
Checks:
- Zonenmenge == TSM names
- orientation ∈ {+1,-1,None}
- (Warnung) doppelte pg_facet-Zuordnung
"""
from pathlib import Path
import json
from collections import Counter

BR = Path(__file__).resolve().parents[1] / "bridge"
J_BRIDGE = BR / "tsm_symbolic_bridge_v0.1.json"
J_TSM    = BR / "tsm_pg_facets_lifted.json"
OUT_MD   = BR / "tsm_symbolic_bridge_report.md"

def main():
    b = json.loads(J_BRIDGE.read_text(encoding="utf-8"))
    t = json.loads(J_TSM.read_text(encoding="utf-8"))
    zones = [z["id"] for z in b.get("zones",[])]
    names = list(map(str, t["names"]))
    ok_set = set(zones) == set(names)

    missing = sorted(set(names) - set(zones))
    extra   = sorted(set(zones) - set(names))

    # orientations & facets
    bad_orient = []
    facets = []
    for z in b.get("zones", []):
        ori = z.get("orientation")
        if ori not in (None, -1, 1):
            bad_orient.append((z["id"], ori))
        if z.get("pg_facet"):
            facets.append(z["pg_facet"])
    dup_facets = [f for f,c in Counter(facets).items() if c>1]

    lines = ["# Symbolic Bridge — Validation Report", ""]
    lines.append(f"- Zones match TSM names: **{ok_set}**")
    if missing: lines.append(f"- Missing in bridge: {', '.join(missing)}")
    if extra:   lines.append(f"- Extra in bridge:   {', '.join(extra)}")
    lines.append("")
    lines.append(f"- Invalid orientations: {len(bad_orient)}")
    for z,ori in bad_orient[:10]:
        lines.append(f"  - {z}: got {ori} (erwartet +1/-1/None)")
    lines.append("")
    # Coverage
    assigned = sum(1 for z in b.get("zones",[]) if z.get("pg_facet"))
    total    = len(b.get("zones",[]))
    lines.append(f"- Coverage: {assigned}/{total} zones have pg_facet")
    if dup_facets:
        lines.append(f"- WARN: duplicate pg_facet IDs: {', '.join(dup_facets)}")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("[ok] wrote:", OUT_MD)

if __name__ == "__main__":
    main()
