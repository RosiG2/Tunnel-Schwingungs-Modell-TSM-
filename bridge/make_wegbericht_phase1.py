#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt Wegbericht (Phase 1) mit RGN-Lifts:
- liest: bridge/tsm_pg_changes.csv  (b,r,Δ,rel,rank_abs/rank_rel)
- liest: bridge/tsm_pg_facets_lifted.json (mit constraints.lifts vom Skript)
- schreibt: bridge/wegbericht_b_to_r_phase1.md
           bridge/tsm_pg_bindings_phase1.csv
           bridge/facet_activations_phase1.json
"""
import json, pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BR   = ROOT / "bridge"
changes_csv = BR / "tsm_pg_changes.csv"
lifted_json = BR / "tsm_pg_facets_lifted.json"

df = pd.read_csv(changes_csv)
with open(lifted_json, "r", encoding="utf-8") as f:
    lifted = json.load(f)

names = lifted["names"]
b = np.array(lifted["b"], dtype=float)
r = np.array(lifted["r"], dtype=float)
n = len(names)

# Helper: evaluate linear constraint a^T x <= c (or equality a^T x == c)
def eval_ineq(a, c, x):
    return float(c) - float(np.dot(np.array(a, dtype=float), x))  # slack >= 0 means satisfied

TOL = 1e-9
# Base UBs from Phase-0 (optional reading)
UBS = { ub["i"]: float(ub["c"]) for ub in lifted.get("constraints",{}).get("upper_bounds",[]) }

# Collect lift constraints
lifts = lifted.get("constraints",{}).get("lifts", [])
act_rows = []
for i, L in enumerate(lifts):
    a = L.get("a"); c = L.get("c")
    if a is None or c is None: 
        continue
    sb = eval_ineq(a, c, b)
    sr = eval_ineq(a, c, r)
    act_rows.append({
        "idx": i,
        "type": L.get("type","ub/lb?"),
        "scope": L.get("scope"),
        "zone": L.get("zone"),
        "group": L.get("group"),
        "zones": ",".join(L.get("zones",[])) if L.get("zones") else None,
        "slack_b": sb,
        "slack_r": sr,
        "bind_b": abs(sb) <= TOL,
        "bind_r": abs(sr) <= TOL
    })
df_act = pd.DataFrame(act_rows)

# Bindings pro Zone bestimmen (inkl. base LB/UB Flags)
# Merke: df enthält b/r (simplex) pro Zone aus changes.csv
# Ergänze Bindings aus UBs (Phase-0) und Lift-Constraints (Phase-1)
bind = df.copy()
bind.rename(columns={"b":"b_x","r":"r_x"}, inplace=True)
bind["bind_b_lb"] = bind["b_x"] <= TOL
bind["bind_r_lb"] = bind["r_x"] <= TOL
bind["ub"]        = bind["zone"].map(lambda z: UBS.get(names.index(z), 1.0) if z in names else 1.0)
bind["bind_b_ub"] = (bind["ub"] - bind["b_x"]) <= 1e-9
bind["bind_r_ub"] = (bind["ub"] - bind["r_x"]) <= 1e-9

# Phase-1: Prüfe für jede Lift-Ungleichung, welche Zonen beteiligt/gebunden sind
def involved_zones(L):
    if L.get("scope") == "zone" and L.get("zone") in names:
        return [L["zone"]]
    if L.get("zones"):
        return [z for z in L["zones"] if z in names]
    # Fallback: alle mit a_j != 0
    a = L.get("a") or []
    return [names[j] for j,v in enumerate(a) if abs(float(v)) > 0]

zone2lifts_b = {z:[] for z in names}
zone2lifts_r = {z:[] for z in names}
for i, L in enumerate(lifts):
    a, c = L.get("a"), L.get("c")
    if a is None or c is None: 
        continue
    inv = involved_zones(L)
    sb = eval_ineq(a, c, b); rb = abs(sb) <= TOL
    sr = eval_ineq(a, c, r); rr = abs(sr) <= TOL
    tag = f"{L.get('type','?')}/{L.get('scope','?')}:{L.get('group') or L.get('zone') or i}"
    for z in inv:
        if rb: zone2lifts_b[z].append(tag)
        if rr: zone2lifts_r[z].append(tag)

bind["lift_bind_b"] = bind["zone"].map(lambda z: ";".join(zone2lifts_b.get(z,[])))
bind["lift_bind_r"] = bind["zone"].map(lambda z: ";".join(zone2lifts_r.get(z,[])))

# Sortierung und Export
bind["abs_delta"] = bind["delta"].abs()
bind.sort_values(["abs_delta","rank_rel"], ascending=[False, True], inplace=True)

out_csv = BR / "tsm_pg_bindings_phase1.csv"
bind_out = bind[["zone","b_x","r_x","delta","rel_change","ub",
                 "bind_b_lb","bind_r_lb","bind_b_ub","bind_r_ub",
                 "lift_bind_b","lift_bind_r","rank_abs","rank_rel","abs_delta"]]
bind_out.to_csv(out_csv, index=False)

# Markdown-Wegbericht
lines = []
lines.append("# Wegbericht b → r (Phase 1: RGN-Lifts aktiv)")
lines.append("")
lines.append(f"- Zonen: **{len(names)}**")
lines.append(f"- Lifts eingezogen: **{len(lifts)}** (aus RGN-Daten abgeleitet).")
lines.append("- Facetten: 0 ≤ x_i, Σx_i=1; per-Zone UB = max(b_i,r_i)+0.05; zzgl. RGN-Gruppen-/Zonen-Lifts.")
lines.append("")
lines.append("## Top-Änderungen (mit Facetten-/Lift-Status)")
for _, row in bind_out.head(20).iterrows():
    flags = []
    if row["bind_b_lb"]: flags.append("b@LB")
    if row["bind_r_lb"]: flags.append("r@LB")
    if row["bind_b_ub"]: flags.append("b@UB")
    if row["bind_r_ub"]: flags.append("r@UB")
    if row["lift_bind_b"]: flags.append(f"b@LIFT[{row['lift_bind_b']}]")
    if row["lift_bind_r"]: flags.append(f"r@LIFT[{row['lift_bind_r']}]")
    flag_str = (" [" + ", ".join(flags) + "]") if flags else ""
    lines.append(f"- {row['zone']}: Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b_x']:.6f} → r={row['r_x']:.6f}{flag_str}")
lines.append("")
lines.append("## Lift-Aktivierungen (gesamt)")
lines.append(df_act.to_string(index=False))
lines.append("")
lines.append("## Hinweise")
lines.append("- LB = untere Facette (x_i=0); UB = obere Zonenkappe.")
lines.append("- LIFT-Tags geben gebundene RGN-Ungleichungen an (zone/gruppenbasiert).")
out_md = BR / "wegbericht_b_to_r_phase1.md"
out_md.write_text("\n".join(lines), encoding="utf-8")

# JSON mit aktivierten Lifts (für weitere Auswertung)
(BR / "facet_activations_phase1.json").write_text(df_act.to_json(orient="records", indent=2), encoding="utf-8")

print(f"[ok] geschrieben:\n - {out_md}\n - {out_csv}\n - {BR/'facet_activations_phase1.json'}")
