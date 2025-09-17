#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 – Facetten-Experimente (What-ifs):
Testet Szenarien (tau, core_ub, core_members), projiziert r³ und misst:
- median|r³−r★| (falls r★ vorhanden, sonst median|r³−b|)
- median|r³−b|
- r³@UB und r³@LB (Anzahl und %)
- LIFT(b), LIFT(r³)
- core_share = Summe r³ über Core-Mitglieder
- l2_to_baseline = ||r³(szen) − r³(baseline)||₂
Schreibt:
- bridge/phase5_experiments_results.csv
- bridge/phase5_experiments_summary.md
- bridge/phase5_experiments_score.png
"""
from pathlib import Path
import json, copy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"
CHG = BR / "tsm_pg_changes.csv"
RSTAR = BR / "tsm_pg_r_projected.csv"            # optional

# -------- Szenarien definieren (gern anpassen) --------
SCENARIOS = [
    # id,         tau, core_ub,            core_members
    ("baseline",  0.10, 0.60,               ["kohärent","regulativ"]),
    ("tau-0.09",  0.09, 0.60,               ["kohärent","regulativ"]),
    ("tau-0.11",  0.11, 0.60,               ["kohärent","regulativ"]),
    ("core+F",    0.10, 0.60,               ["kohärent","regulativ","fragmentiert"]),
    ("core-onlyK",0.10, 0.60,               ["kohärent"]),
    ("coreUB-0.58",0.10, 0.58,              ["kohärent","regulativ"]),
    ("coreUB-0.62",0.10, 0.62,              ["kohärent","regulativ"]),
]

def clamp(x, lo, hi): return max(lo, min(hi, x))

def build_caps(d, tau, core_ub, core_members):
    d2 = copy.deepcopy(d)
    names = list(map(str, d2["names"]))
    b = [float(v) for v in d2["b"]]
    n = len(names)
    cons = d2.setdefault("constraints", {})
    lifts = cons.setdefault("lifts", [])

    def upsert(key, L):
        for i,X in enumerate(lifts):
            if X.get("meta",{}).get("key")==key:
                lifts[i]=L; break
        else:
            lifts.append(L)

    # group core UB
    idx = [names.index(z) for z in core_members if z in names]
    a = [0.0]*n
    for i in idx: a[i]=1.0
    upsert("p3_group_core_ub", {
        "type":"ub","scope":"group","group":"core","zones":[names[i] for i in idx],
        "a":a,"c":float(core_ub),
        "meta":{"phase":"3","key":"p3_group_core_ub","note":f"core({','.join(core_members)}) ≤ {core_ub:.2f}"}
    })
    # per-zone corridor ±tau um b
    for i,z in enumerate(names):
        lb = max(0.0, b[i]-tau)
        ub = min(1.0, b[i]+tau)
        upsert(f"p3_zone_lb_{i}", {
            "type":"lb","scope":"zone","zone":z,
            "a":[-1.0 if j==i else 0.0 for j in range(n)], "c":-float(lb),
            "meta":{"phase":"3","key":f"p3_zone_lb_{i}","note":f"{z}: x >= {lb:.4f} (b-τ)"}
        })
        upsert(f"p3_zone_ub_{i}", {
            "type":"ub","scope":"zone","zone":z,
            "a":[ 1.0 if j==i else 0.0 for j in range(n)], "c": float(ub),
            "meta":{"phase":"3","key":f"p3_zone_ub_{i}","note":f"{z}: x <= {ub:.4f} (b+τ)"}
        })
    return d2

def bounds_from_json(d):
    names = list(map(str, d["names"])); n=len(names)
    ub = [1.0]*n
    for u in d.get("constraints",{}).get("upper_bounds",[]) or []:
        ub[u["i"]] = float(u["c"])
    lb = [0.0]*n
    g_lb = {}; g_ub = {}
    for L in d.get("constraints",{}).get("lifts",[]) or []:
        a,c=L.get("a"),L.get("c")
        if a is None or c is None: continue
        typ=L.get("type"); scope=L.get("scope")
        if scope=="zone" and L.get("zone") in names:
            i = names.index(L["zone"])
            if typ=="lb": lb[i] = max(lb[i], -float(c))
            elif typ=="ub": ub[i] = min(ub[i],  float(c))
        elif scope=="group":
            zs = L.get("zones") or [names[j] for j,v in enumerate(a or []) if abs(float(v))>0]
            idx=[names.index(z) for z in zs if z in names]
            if not idx: continue
            if typ=="lb": g_lb[L.get("group") or "group"]=(idx, -float(c))
            elif typ=="ub": g_ub[L.get("group") or "group"]=(idx,  float(c))
    return names, lb, ub, g_lb, g_ub

def project_simplex(x, lb, ub):
    n=len(x); x=[clamp(x[i], lb[i], ub[i]) for i in range(n)]
    for _ in range(10000):
        s=sum(x)
        if abs(s-1.0)<=1e-12: break
        if s>1.0:
            room=[x[i]-lb[i] for i in range(n)]; R=sum(room)
            if R<=1e-15: break
            f=(s-1.0)/R
            for i in range(n): x[i]=clamp(x[i]-f*room[i], lb[i], ub[i])
        else:
            room=[ub[i]-x[i] for i in range(n)]; R=sum(room)
            if R<=1e-15: break
            f=(1.0-s)/R
            for i in range(n): x[i]=clamp(x[i]+f*room[i], lb[i], ub[i])
    return [clamp(x[i], lb[i], ub[i]) for i in range(n)]

def enforce_group(x, idx, bnd, lb, ub, is_lb=True):
    s=sum(x[i] for i in idx)
    if (is_lb and s+1e-12>=bnd) or ((not is_lb) and s-1e-12<=bnd): return x
    if is_lb:
        need=max(0.0, bnd-s); per=need/max(1,len(idx))
        for i in idx: x[i]=clamp(x[i]+per, lb[i], ub[i])
    else:
        exc=max(0.0, s-bnd); per=exc/max(1,len(idx))
        for i in idx: x[i]=clamp(x[i]-per, lb[i], ub[i])
    return project_simplex(x, lb, ub)

def project_r3(d):
    names = list(map(str, d["names"]))
    r = [float(v) for v in d["r"]]
    names2, lb, ub, glb, gub = bounds_from_json(d)
    assert names2==names
    x = project_simplex(r, lb, ub)
    for _,(idx,m) in glb.items(): x = enforce_group(x, idx, m, lb, ub, True)
    for _,(idx,M) in gub.items(): x = enforce_group(x, idx, M, lb, ub, False)
    x = project_simplex(x, lb, ub)
    return names, np.array(r,float), np.array(x,float), np.array(lb,float), np.array(ub,float), g_lb, g_ub

def lift_counts(d, vec):
    TOL=1e-9
    lifts=d.get("constraints",{}).get("lifts",[]) or []
    v=np.array(vec, float)
    def slack(a,c,x): return float(c)-float(np.dot(np.array(a,float), x))
    cnt=0
    for L in lifts:
        a,c=L.get("a"),L.get("c")
        if a is None or c is None: continue
        if abs(slack(a,c,v))<=TOL: cnt+=1
    return cnt

# --- Load base
base = json.loads(J.read_text(encoding="utf-8"))
names = list(map(str, base["names"]))
b_vec = np.array(list(map(float, base["b"])), float)
rS_map = {}
if RSTAR.exists():
    dfS=pd.read_csv(RSTAR)
    rS_map = dict(zip(dfS["zone"].astype(str), dfS["r_projected"].astype(float)))

# Baseline r3 (für L2)
_, _, r3_baseline, *_ = project_r3(build_caps(base, 0.10, 0.60, ["kohärent","regulativ"]))

rows=[]
for sid, tau, core_ub, core_members in SCENARIOS:
    d2 = build_caps(base, tau, core_ub, core_members)
    names2, r, r3, lb, ub, g_lb, g_ub = project_r3(d2)
    assert names2==names
    # counts
    ub_hits=int((r3 >= ub-1e-9).sum()); lb_hits=int((r3 <= lb+1e-9).sum()); n=len(names)
    lift_b = lift_counts(d2, b_vec); lift_r3 = lift_counts(d2, r3)
    # deltas
    med_r3_b  = float(np.median(np.abs(r3 - b_vec)))
    if rS_map:
        rS = np.array([rS_map.get(z, np.nan) for z in names], float)
        med_r3_rS = float(np.nanmedian(np.abs(r3 - rS)))
    else:
        med_r3_rS = np.nan
    # core share
    core_idx=[names.index(z) for z in core_members if z in names]
    core_share=float(np.sum(r3[core_idx])) if core_idx else float("nan")
    # distance to baseline
    l2=float(np.linalg.norm(r3 - r3_baseline))
    # score (kleiner ist besser)
    proxy_med = med_r3_rS if not np.isnan(med_r3_rS) else med_r3_b
    score = 0.6*proxy_med + 0.2*(ub_hits/n) + 0.2*(lb_hits/n)

    rows.append({
        "scenario": sid, "tau": tau, "core_ub": core_ub, "core_members": ",".join(core_members),
        "med_r3_vs_rstar": med_r3_rS, "med_r3_vs_b": med_r3_b,
        "r3_at_ub": ub_hits, "r3_at_lb": lb_hits,
        "lift_b": lift_b, "lift_r3": lift_r3,
        "core_share": core_share,
        "l2_to_baseline": l2,
        "score": score
    })

df=pd.DataFrame(rows).sort_values(["score","r3_at_ub","r3_at_lb"], ascending=[True,True,True])
df.to_csv(BR/"phase5_experiments_results.csv", index=False)

# Summary MD
lines=["# Phase 5 — Facetten-Experimente (Ranking)","",
       "**Score** = 0.6·MedianΔ (r³ vs r★ bzw. b) + 0.2·(r³@UB %) + 0.2·(r³@LB %)", ""]
for _,r in df.head(6).iterrows():
    med = r["med_r3_vs_rstar"] if not np.isnan(r["med_r3_vs_rstar"]) else r["med_r3_vs_b"]
    lines.append(f"- {r['scenario']}: τ={r['tau']:.2f}, core_UB={r['core_ub']:.2f}, core=[{r['core_members']}] | "
                 f"score={r['score']:.4f} | medianΔ={med:.4f} | r³@UB={int(r['r3_at_ub'])} | r³@LB={int(r['r3_at_lb'])} | core_share={r['core_share']:.3f}")
(BR/"phase5_experiments_summary.md").write_text("\n".join(lines), encoding="utf-8")

# Score-Plot
fig, ax = plt.subplots(figsize=(7.5,4), dpi=160)
ax.barh(df["scenario"], df["score"])
ax.invert_yaxis()
ax.set_xlabel("score (kleiner ist besser)")
ax.set_title("Phase 5 — Szenario-Score")
fig.tight_layout()
fig.savefig(BR/"phase5_experiments_score.png")
print("[ok] wrote:", BR/"phase5_experiments_results.csv", BR/"phase5_experiments_summary.md", BR/"phase5_experiments_score.png")
