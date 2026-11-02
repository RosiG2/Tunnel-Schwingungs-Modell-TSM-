#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nimmt die beste τ/core_UB-Kombi aus phase3_sweep_results.csv
-> schreibt Phase-3-Caps ins JSON
-> projiziert r³ neu
-> aktualisiert Wegbericht, Summary, Keypoints und Online-Bundle (v1.22)
"""
from pathlib import Path
import json, csv, copy
import pandas as pd
import numpy as np

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"
RSTAR = BR / "tsm_pg_r_projected.csv"             # optional
CHG   = BR / "tsm_pg_changes.csv"

# ---------- helpers ----------
def upsert_lift(lifts, key, L):
    for i, X in enumerate(lifts):
        if X.get("meta", {}).get("key") == key:
            lifts[i] = L
            break
    else:
        lifts.append(L)

def build_caps(d, CORE_UB, DELTA_TAU, CORE_ZONES=("kohärent","regulativ")):
    d2 = copy.deepcopy(d)
    names = list(map(str, d2["names"]))
    b = [float(v) for v in d2["b"]]
    n = len(names)
    cons = d2.setdefault("constraints", {})
    lifts = cons.setdefault("lifts", [])

    if CORE_UB is not None:
        idx = [names.index(z) for z in CORE_ZONES if z in names]
        a = [0.0]*n
        for i in idx: a[i] = 1.0
        upsert_lift(lifts, "p3_group_core_ub", {
            "type":"ub","scope":"group","group":"core",
            "zones":[names[i] for i in idx],
            "a":a,"c":float(CORE_UB),
            "meta":{"phase":"3","key":"p3_group_core_ub","note":f"core ≤ {CORE_UB:.2f}"}
        })

    if DELTA_TAU is not None:
        for i, z in enumerate(names):
            m_lb = max(0.0, b[i]-DELTA_TAU)
            upsert_lift(lifts, f"p3_zone_lb_{i}", {
                "type":"lb","scope":"zone","zone":z,
                "a":[-1.0 if j==i else 0.0 for j in range(n)], "c":-float(m_lb),
                "meta":{"phase":"3","key":f"p3_zone_lb_{i}","note":f"{z}: x >= {m_lb:.4f} (b-τ)"}
            })
            m_ub = min(1.0, b[i]+DELTA_TAU)
            upsert_lift(lifts, f"p3_zone_ub_{i}", {
                "type":"ub","scope":"zone","zone":z,
                "a":[1.0 if j==i else 0.0 for j in range(n)], "c":float(m_ub),
                "meta":{"phase":"3","key":f"p3_zone_ub_{i}","note":f"{z}: x <= {m_ub:.4f} (b+τ)"}
            })

    d2.setdefault("meta", {}).setdefault("notes", []).append(f"Phase 3 applied: core_UB={CORE_UB:.2f}, tau={DELTA_TAU:.2f}")
    return d2

def clamp(x, lo, hi): return max(lo, min(hi, x))

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
    return names, np.array(r,float), np.array(x,float)

# ---------- main ----------
def main():
    # 1) Beste tau/core_UB lesen
    df = pd.read_csv(BR/"phase3_sweep_results.csv")
    best = df.sort_values(["score","ub_pct","lb_pct"], ascending=[True,True,True]).iloc[0]
    tau = float(best["tau"]); cub = float(best["core_ub"])

    # 2) JSON laden & Caps eintragen
    base = json.loads(J.read_text(encoding="utf-8"))
    d2   = build_caps(base, CORE_UB=cub, DELTA_TAU=tau)
    J.write_text(json.dumps(d2, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) r³ neu projizieren
    names, r, r3 = project_r3(d2)
    (BR/"tsm_pg_r_projected_p3.csv").write_text(
        "zone,r_original,r_projected\n" + "\n".join(f"{z},{ro:.10f},{rp:.10f}" for z,ro,rp in zip(names, r, r3)),
        encoding="utf-8"
    )
    # Mini-Report
    diffs = sorted([(abs(rp-ro), z, ro, rp) for z,ro,rp in zip(names, r, r3)], reverse=True)[:12]
    lines = ["# Phase 3 – r → r³ (Projektion, BEST aus Sweep)", f"- gewählt: τ={tau:.2f}, core_UB={cub:.2f}", "", "## Top-Diffs |r³−r|"]
    for d,z,ro,rp in diffs:
        lines.append(f"- {z}: Δ|r³−r|={d:.6f} | r={ro:.6f} → r³={rp:.6f}")
    (BR/"tsm_pg_r_projected_p3.md").write_text("\n".join(lines), encoding="utf-8")

    # 4) Wegbericht & Summary & Keypoints & Bundle refreshen
    import subprocess, sys
    def run_py(rel):
        cmd=[sys.executable, str(BR/rel)]
        subprocess.check_call(cmd, cwd=str(BR.parents[1]))

    run_py("make_wegbericht_phase3_star_min.py")
    run_py("make_phase3_summary.py")
    run_py("make_phase3_keypoints.py")

    # Online-Bundle v1.22
    import time  # <-- NUR time importieren, pandas kommt von oben (pd)
    d = json.loads(J.read_text(encoding="utf-8"))  # frisch aktualisiert
    names = list(map(str, d["names"]))
    b_vec = list(map(float, d["b"]))
    chg = pd.read_csv(BR/"tsm_pg_changes.csv")
    chg["zone"]=chg["zone"].astype(str)
    r_changes = {z: float(v) for z, v in zip(chg["zone"], chg["r"])}
    rS={}
    if (BR/"tsm_pg_r_projected.csv").exists():
        dfS=pd.read_csv(BR/"tsm_pg_r_projected.csv"); rS={str(z): float(v) for z,v in zip(dfS["zone"], dfS["r_projected"])}
    r3m={str(z): float(v) for z,v in zip(pd.read_csv(BR/"tsm_pg_r_projected_p3.csv")["zone"], pd.read_csv(BR/"tsm_pg_r_projected_p3.csv")["r_projected"])}
    bundle={
        "version":"1.22","timestamp":int(time.time()),
        "names":names,"b":[float(x) for x in b_vec],
        "r":[float(r_changes.get(z,0.0)) for z in names],
        "r_star":[float(rS.get(z,0.0)) for z in names] if rS else None,
        "r3":[float(r3m.get(z,0.0)) for z in names],
        "constraints": d.get("constraints",{}),
        "meta": d.get("meta",{})
    }
    (BR/"tsm-online-bundle_v1.22.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] applied best caps τ={tau:.2f}, core_UB={cub:.2f}")
    print("[ok] refreshed: r³, Wegbericht, Summary, Keypoints, Bundle v1.22")

if __name__ == "__main__":
    main()
