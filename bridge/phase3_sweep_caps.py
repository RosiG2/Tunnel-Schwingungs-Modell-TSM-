# bridge/phase3_sweep_caps.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sweep für Phase-3-Caps: τ (Delta-Korridor) × core_UB.
- Liest:  bridge/tsm_pg_facets_lifted.json, tsm_pg_changes.csv, (optional) tsm_pg_r_projected.csv
- Schreibt: bridge/phase3_sweep_results.csv, bridge/phase3_sweep_summary.md
Hinweis: JSON wird am Ende auf den Ursprungszustand zurückgesetzt.
"""
from pathlib import Path
import json, copy
import pandas as pd
import numpy as np

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"
CHG = BR / "tsm_pg_changes.csv"
RSTAR = BR / "tsm_pg_r_projected.csv"  # optional

# === GRID (gerne anpassen) ===
TAU_GRID     = [0.06, 0.08, 0.10]
CORE_UB_GRID = [0.56, 0.58, 0.60]

def clamp(x, lo, hi): return max(lo, min(hi, x))

def build_caps(d, CORE_UB, DELTA_TAU, CORE_ZONES=("kohärent","regulativ")):
    """liefert NEUE Kopie von d mit Phase-3-Caps (ersetzt p3_* Lifts idempotent)"""
    d2 = copy.deepcopy(d)
    names = list(map(str, d2["names"]))
    b = [float(v) for v in d2["b"]]
    n = len(names)
    cons = d2.setdefault("constraints", {})
    lifts = cons.setdefault("lifts", [])
    # Helper: upsert by meta.key
    def upsert(key, L):
        for i,X in enumerate(lifts):
            if X.get("meta",{}).get("key")==key:
                lifts[i]=L; break
        else:
            lifts.append(L)

    # group core UB
    if CORE_UB is not None:
        idx = [names.index(z) for z in CORE_ZONES if z in names]
        a = [0.0]*n
        for i in idx: a[i]=1.0
        upsert("p3_group_core_ub", {
            "type":"ub","scope":"group","group":"core",
            "zones":[names[i] for i in idx],
            "a":a,"c":float(CORE_UB),
            "meta":{"phase":"3","key":"p3_group_core_ub","note":f"core ≤ {CORE_UB:.2f}"}
        })
    # per-zone corridor
    if DELTA_TAU is not None:
        for i,z in enumerate(names):
            m_lb=max(0.0, b[i]-DELTA_TAU)
            upsert(f"p3_zone_lb_{i}", {
                "type":"lb","scope":"zone","zone":z,
                "a":[-1.0 if j==i else 0.0 for j in range(n)], "c":-float(m_lb),
                "meta":{"phase":"3","key":f"p3_zone_lb_{i}","note":f"{z}: x >= {m_lb:.4f} (b-τ)"}
            })
            m_ub=min(1.0, b[i]+DELTA_TAU)
            upsert(f"p3_zone_ub_{i}", {
                "type":"ub","scope":"zone","zone":z,
                "a":[1.0 if j==i else 0.0 for j in range(n)], "c":float(m_ub),
                "meta":{"phase":"3","key":f"p3_zone_ub_{i}","note":f"{z}: x <= {m_ub:.4f} (b+τ)"}
            })
    cons["lifts"]=lifts
    return d2

def load_bounds_from_lifts(d):
    names = list(map(str, d["names"])); n=len(names)
    ub = [1.0]*n
    for ubent in d.get("constraints",{}).get("upper_bounds",[]) or []:
        ub[ubent["i"]] = float(ubent["c"])
    lb = [0.0]*n
    groups_lb = {}; groups_ub = {}
    for L in d.get("constraints",{}).get("lifts",[]) or []:
        a,c=L.get("a"),L.get("c")
        if a is None or c is None: continue
        typ=L.get("type"); scope=L.get("scope")
        if scope=="zone" and L.get("zone") in names:
            i = names.index(L["zone"])
            if typ=="lb": lb[i] = max(lb[i], -float(c))
            elif typ=="ub": ub[i] = min(ub[i], float(c))
        elif scope=="group":
            zs = L.get("zones") or [names[j] for j,v in enumerate(a or []) if abs(float(v))>0]
            idx=[names.index(z) for z in zs if z in names]
            if not idx: continue
            if typ=="lb": groups_lb[L.get("group") or "group"]=(idx, -float(c))
            elif typ=="ub": groups_ub[L.get("group") or "group"]=(idx, float(c))
    return names, lb, ub, groups_lb, groups_ub

def project_simplex_with_bounds(x, lb, ub):
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

def enforce_group(x, idx, bound, lb, ub, is_lb=True):
    s=sum(x[i] for i in idx)
    if (is_lb and s+1e-12>=bound) or ((not is_lb) and s-1e-12<=bound): return x
    if is_lb:
        need=max(0.0, bound-s); per=need/max(1,len(idx))
        for i in idx: x[i]=clamp(x[i]+per, lb[i], ub[i])
    else:
        exc=max(0.0, s-bound); per=exc/max(1,len(idx))
        for i in idx: x[i]=clamp(x[i]-per, lb[i], ub[i])
    return project_simplex_with_bounds(x, lb, ub)

def project_r(d):
    names = list(map(str, d["names"]))
    r = [float(v) for v in d["r"]]
    lb_ub = load_bounds_from_lifts(d)
    names2, lb, ub, glb, gub = lb_ub
    assert names2==names
    x = project_simplex_with_bounds(r, lb, ub)
    for _,(idx,m) in glb.items(): x=enforce_group(x, idx, m, lb, ub, True)
    for _,(idx,M) in gub.items(): x=enforce_group(x, idx, M, lb, ub, False)
    x = project_simplex_with_bounds(x, lb, ub)
    return names, np.array(r, float), np.array(x, float), np.array(lb,float), np.array(ub,float)

def compute_counts_and_scores(d, r3_vec, rS_map, b_vec):
    names = list(map(str, d["names"]))
    ub = [1.0]*len(names)
    for ubent in d.get("constraints",{}).get("upper_bounds",[]) or []:
        ub[ubent["i"]] = float(ubent["c"])
    TOL=1e-9
    r3_lb = int((r3_vec <= TOL).sum())
    r3_ub = int((r3_vec >= np.array(ub)-1e-9).sum())
    # LIFT counts
    lifts = d.get("constraints",{}).get("lifts",[]) or []
    def slack(a,c,x): return float(c)-float(np.dot(np.array(a,float), x))
    b_arr = np.array(b_vec, float)
    lift_b=lift_r3=0
    for L in lifts:
        a,c=L.get("a"),L.get("c"); 
        if a is None or c is None: continue
        if abs(slack(a,c,b_arr))<=TOL: lift_b+=1
        if abs(slack(a,c,r3_vec))<=TOL: lift_r3+=1
    # deltas
    rS_arr = np.array([rS_map.get(z, np.nan) for z in names], float) if rS_map else np.array([], float)
    med_r3_rS = float(np.nanmedian(np.abs(r3_vec - rS_arr))) if rS_map else np.nan
    med_r3_b  = float(np.nanmedian(np.abs(r3_vec - np.array(b_vec,float))))
    return dict(r3_lb=r3_lb, r3_ub=r3_ub, lift_b=lift_b, lift_r3=lift_r3,
                med_r3_rS=med_r3_rS, med_r3_b=med_r3_b, n=len(names))

def main():
    base = json.loads(J.read_text(encoding="utf-8"))
    names = list(map(str, base["names"]))
    b_vec = list(map(float, base["b"]))
    # r★ map optional
    rS_map={}
    if RSTAR.exists():
        df=pd.read_csv(RSTAR)
        rS_map = dict(zip(df["zone"].astype(str), df["r_projected"].astype(float)))
    results=[]
    for tau in TAU_GRID:
        for cub in CORE_UB_GRID:
            d2 = build_caps(base, CORE_UB=cub, DELTA_TAU=tau)
            names2, r, r3, lb, ub = project_r(d2)
            assert names2==names
            metrics = compute_counts_and_scores(d2, r3, rS_map, b_vec)
            n=metrics["n"]
            ub_pct = metrics["r3_ub"]/n
            lb_pct = metrics["r3_lb"]/n
            # Ziel: kleine Median-Abweichung + wenig UB/LB-Bindungen
            med = metrics["med_r3_rS"] if not np.isnan(metrics["med_r3_rS"]) else metrics["med_r3_b"]
            score = 0.6*med + 0.2*ub_pct + 0.2*lb_pct
            results.append({
                "tau": tau, "core_ub": cub,
                "med_r3_vs_rstar": metrics["med_r3_rS"],
                "med_r3_vs_b": metrics["med_r3_b"],
                "r3_at_ub": metrics["r3_ub"], "r3_at_lb": metrics["r3_lb"],
                "lift_b": metrics["lift_b"], "lift_r3": metrics["lift_r3"],
                "ub_pct": ub_pct, "lb_pct": lb_pct,
                "score": score
            })
    df = pd.DataFrame(results)
    df.sort_values(["score","ub_pct","lb_pct"], ascending=[True, True, True], inplace=True)
    df.to_csv(BR/"phase3_sweep_results.csv", index=False)

    # Summary
    top = df.head(5).copy()
    lines = ["# Phase 3★ – Sweep-Ergebnis", ""]
    if "med_r3_vs_rstar" in top.columns and not top["med_r3_vs_rstar"].isna().all():
        lines.append("**Score = 0.6·Median|r³−r★| + 0.2·(r³@UB %) + 0.2·(r³@LB %)**")
    else:
        lines.append("**Score = 0.6·Median|r³−b| + 0.2·(r³@UB %) + 0.2·(r³@LB %)**")
    lines.append("")
    for _,r in top.iterrows():
        med = r["med_r3_vs_rstar"] if not np.isnan(r["med_r3_vs_rstar"]) else r["med_r3_vs_b"]
        lines.append(f"- τ={r['tau']:.2f}, core_UB={r['core_ub']:.2f} | score={r['score']:.4f} | "
                     f"medianΔ={med:.4f} | r³@UB={int(r['r3_at_ub'])} ({r['ub_pct']*100:.1f}%) | r³@LB={int(r['r3_at_lb'])} ({r['lb_pct']*100:.1f}%)")
    (BR/"phase3_sweep_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("[ok] wrote:", BR/"phase3_sweep_results.csv", BR/"phase3_sweep_summary.md")

if __name__ == "__main__":
    main()
