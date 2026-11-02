#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, pandas as pd, numpy as np
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
chg   = pd.read_csv(BR/"tsm_pg_changes.csv")                   # zone,b,r,delta,rel_change,rank_abs,rank_rel
rproj = pd.read_csv(BR/"tsm_pg_r_projected_p3.csv")            # zone,r_original,r_projected
lifted= json.loads((BR/"tsm_pg_facets_lifted.json").read_text(encoding="utf-8"))

names = list(map(str, lifted["names"]))
b_vec = np.array(lifted["b"], dtype=float)
r3map = dict(zip(rproj["zone"].astype(str), rproj["r_projected"].astype(float)))
r3vec = np.array([r3map.get(z, 0.0) for z in names], dtype=float)

# UB-Map
ub_map = { names[ub["i"]]: float(ub["c"]) for ub in lifted.get("constraints",{}).get("upper_bounds",[]) }
TOL=1e-9

# Bindings b/r³
rows=[]
for i,z in enumerate(names):
    bi=float(b_vec[i]); ri=float(r3vec[i]); ub=ub_map.get(z,1.0)
    rows.append(dict(zone=z,b_x=bi,r3_x=ri,
                     bind_b_lb=(bi<=TOL), bind_r3_lb=(ri<=TOL),
                     ub=ub, bind_b_ub=((ub-bi)<=1e-9), bind_r3_ub=((ub-ri)<=1e-9)))
bind=pd.DataFrame(rows)

# Lifts → Tags
def involved_zones(L):
    if L.get("scope")=="zone" and L.get("zone") in names: return [L["zone"]]
    if L.get("zones"): return [z for z in L["zones"] if z in names]
    a=L.get("a") or []; return [names[j] for j,v in enumerate(a) if abs(float(v))>0]
def slack(a,c,x): return float(c)-float(np.dot(np.array(a,dtype=float),x))

lifts = lifted.get("constraints",{}).get("lifts",[]) or []
z2b={z:[] for z in names}; z2r={z:[] for z in names}
for i,L in enumerate(lifts):
    a,c=L.get("a"),L.get("c")
    if a is None or c is None: continue
    rb=abs(slack(a,c,np.array(lifted["b"],float)))<=TOL
    rr=abs(slack(a,c,r3vec))<=TOL
    tag=f"{L.get('type','?')}/{L.get('scope','?')}:{L.get('group') or L.get('zone') or i}"
    for z in involved_zones(L):
        if rb: z2b[z].append(tag)
        if rr: z2r[z].append(tag)

# b→r³ Deltas neu
chg2=chg.copy(); chg2["zone"]=chg2["zone"].astype(str)
chg2["r3"]=chg2["zone"].map(lambda z: r3map.get(z,np.nan))
chg2["delta3"]=chg2["r3"]-chg2["b"]
chg2["rel3"]=np.where(chg2["b"].abs()>0, chg2["delta3"]/chg2["b"].replace(0,np.nan), np.nan)
chg2["abs_delta3"]=chg2["delta3"].abs()

df = chg2.merge(bind, on="zone", how="left")
df["lift_bind_b"]    = df["zone"].map(lambda z: ";".join(z2b.get(z,[])))
df["lift_bind_r3"]   = df["zone"].map(lambda z: ";".join(z2r.get(z,[])))
df.sort_values(["abs_delta3","rank_rel"], ascending=[False,True], inplace=True)

# Exporte
df.to_csv(BR/"tsm_pg_bindings_phase3_star.csv", index=False)

lines=["# Wegbericht b → r³ (Phase 3★: r³ projektiert)","",
       f"- Zonen: **{len(names)}** | Lifts: **{len(lifts)}** | r³ = projiziert (feasible; P3-Caps aktiv).",
       "- Facetten: 0 ≤ x_i, Σx_i=1; UBs re-margined; P3-Caps (Delta-Korridor, core-UB).","",
       "## Top-Änderungen (b → r³) – mit Facetten-/Lift-Status"]
for _,row in df.head(20).iterrows():
    flags=[]
    if row["bind_b_lb"]: flags.append("b@LB")
    if row["bind_r3_lb"]: flags.append("r³@LB")
    if row["bind_b_ub"]: flags.append("b@UB")
    if row["bind_r3_ub"]: flags.append("r³@UB")
    if row["lift_bind_b"]: flags.append(f"b@LIFT[{row['lift_bind_b']}]")
    if row["lift_bind_r3"]: flags.append(f"r³@LIFT[{row['lift_bind_r3']}]")
    flag_str=(" ["+", ".join(flags)+"]") if flags else ""
    lines.append(f"- {row['zone']}: Δ³={row['delta3']:.6f} | rel³={row['rel3']:.3f} | b={row['b']:.6f} → r³={row['r3']:.6f}{flag_str}")
(BR/"wegbericht_b_to_r3_star.md").write_text("\n".join(lines), encoding="utf-8")

print("[ok] wrote: bindings_phase3_star.csv, wegbericht_b_to_r3_star.md")
