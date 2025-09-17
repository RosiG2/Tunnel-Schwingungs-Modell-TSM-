#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 5 — Apply Scenario:
- liest: bridge/phase5_experiments_results.csv
- wählt bestes Szenario (oder --scenario NAME)
- schreibt Caps (tau, core_ub, core_members) in tsm_pg_facets_lifted.json
- projiziert r³ neu
- refresht Wegbericht, Summary, Keypoints
- baut Online-Bundle v1.25 (inkl. symbolic_bridge)
"""
from pathlib import Path
import json, copy, argparse, subprocess, sys, time
import numpy as np
import pandas as pd

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"
RSTAR = BR / "tsm_pg_r_projected.csv"            # optional

# ---------- helpers ----------
def clamp(x, lo, hi): return max(lo, min(hi, x))

def upsert_lift(lifts, key, L):
    for i,X in enumerate(lifts):
        if X.get("meta", {}).get("key") == key:
            lifts[i] = L
            break
    else:
        lifts.append(L)

def build_caps(d, tau, core_ub, core_members):
    d2 = copy.deepcopy(d)
    names = list(map(str, d2["names"]))
    b = [float(v) for v in d2["b"]]
    n = len(names)
    cons = d2.setdefault("constraints", {})
    lifts = cons.setdefault("lifts", [])

    # group core UB
    idx = [names.index(z) for z in core_members if z in names]
    a = [0.0]*n
    for i in idx: a[i]=1.0
    upsert_lift(lifts, "p5_group_core_ub", {
        "type":"ub","scope":"group","group":"core","zones":[names[i] for i in idx],
        "a":a,"c":float(core_ub),
        "meta":{"phase":"5","key":"p5_group_core_ub","note":f"core({','.join(core_members)}) ≤ {core_ub:.2f}"}
    })

    # per-zone corridor ±tau um b
    for i,z in enumerate(names):
        lb = max(0.0, b[i]-tau)
        ub = min(1.0, b[i]+tau)
        upsert_lift(lifts, f"p5_zone_lb_{i}", {
            "type":"lb","scope":"zone","zone":z,
            "a":[-1.0 if j==i else 0.0 for j in range(n)], "c":-float(lb),
            "meta":{"phase":"5","key":f"p5_zone_lb_{i}","note":f"{z}: x >= {lb:.4f} (b-τ)"}
        })
        upsert_lift(lifts, f"p5_zone_ub_{i}", {
            "type":"ub","scope":"zone","zone":z,
            "a":[ 1.0 if j==i else 0.0 for j in range(n)], "c": float(ub),
            "meta":{"phase":"5","key":f"p5_zone_ub_{i}","note":f"{z}: x <= {ub:.4f} (b+τ)"}
        })

    d2.setdefault("meta", {}).setdefault("notes", []).append(
        f"Phase 5 applied: core_UB={core_ub:.2f}, tau={tau:.2f}, core={core_members}"
    )
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
    names2, lb, ub, g_lb, g_ub = bounds_from_json(d)
    assert names2==names
    x = project_simplex(r, lb, ub)
    for _,(idx,m) in g_lb.items(): x = enforce_group(x, idx, m, lb, ub, True)
    for _,(idx,M) in g_ub.items(): x = enforce_group(x, idx, M, lb, ub, False)
    x = project_simplex(x, lb, ub)
    return names, np.array(r,float), np.array(x,float)

def run_py(rel):
    cmd=[sys.executable, str(BR/rel)]
    subprocess.check_call(cmd, cwd=str(BR.parents[1]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", help="Szenario-ID (falls leer: bestes laut score)")
    args = ap.parse_args()

    df = pd.read_csv(BR/"phase5_experiments_results.csv")
    if args.scenario:
        row = df.loc[df["scenario"]==args.scenario]
        if row.empty:
            raise SystemExit(f"[err] scenario '{args.scenario}' nicht gefunden.")
        best = row.iloc[0]
    else:
        best = df.sort_values(["score","r3_at_ub","r3_at_lb"], ascending=[True,True,True]).iloc[0]

    tau      = float(best["tau"])
    core_ub  = float(best["core_ub"])
    core_members = str(best["core_members"]).split(",")

    base = json.loads(J.read_text(encoding="utf-8"))
    d2   = build_caps(base, tau, core_ub, core_members)
    J.write_text(json.dumps(d2, ensure_ascii=False, indent=2), encoding="utf-8")

    # r³ neu
    names, r, r3 = project_r3(d2)
    (BR/"tsm_pg_r_projected_p3.csv").write_text(
        "zone,r_original,r_projected\n" + "\n".join(f"{z},{ro:.10f},{rp:.10f}" for z,ro,rp in zip(names, r, r3)),
        encoding="utf-8"
    )
    diffs = sorted([(abs(rp-ro), z, ro, rp) for z,ro,rp in zip(names, r, r3)], reverse=True)[:12]
    lines = [
        "# Phase 5 — Apply Scenario",
        f"- gewählt: scenario={best['scenario']} | τ={tau:.2f}, core_UB={core_ub:.2f}, core={[*core_members]}",
        "", "## Top-Diffs |r³−r|"
    ]
    for dlt,z,ro,rp in diffs:
        lines.append(f"- {z}: Δ|r³−r|={dlt:.6f} | r={ro:.6f} → r³={rp:.6f}")
    (BR/"tsm_pg_r_projected_p3.md").write_text("\n".join(lines), encoding="utf-8")

    # refresh Reports
    run_py("make_wegbericht_phase3_star_min.py")
    run_py("make_phase3_summary.py")
    run_py("make_phase3_keypoints.py")

    # Bundle v1.25
    d = json.loads(J.read_text(encoding="utf-8"))
    names = list(map(str, d["names"]))
    b_vec = list(map(float, d["b"]))
    chg = pd.read_csv(BR/"tsm_pg_changes.csv"); chg["zone"]=chg["zone"].astype(str)
    r_changes = dict(zip(chg["zone"], chg["r"]))
    rS={}
    if RSTAR.exists():
        dfS=pd.read_csv(RSTAR); rS={str(z): float(v) for z,v in zip(dfS["zone"], dfS["r_projected"])}
    r3m = pd.read_csv(BR/"tsm_pg_r_projected_p3.csv")
    r3m = {str(z): float(v) for z,v in zip(r3m["zone"], r3m["r_projected"])}

    symb = None
    SBR = BR/"tsm_symbolic_bridge_v0.1.json"
    if SBR.exists():
        symb = json.loads(SBR.read_text(encoding="utf-8"))

    bundle={
        "version":"1.25","timestamp":int(time.time()),
        "names":names,"b":[float(x) for x in b_vec],
        "r":[float(r_changes.get(z,0.0)) for z in names],
        "r_star":[float(rS.get(z,0.0)) for z in names] if rS else None,
        "r3":[float(r3m.get(z,0.0)) for z in names],
        "constraints": d.get("constraints",{}),
        "meta": d.get("meta",{}),
        "symbolic_bridge": symb
    }
    (BR/"tsm-online-bundle_v1.25.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[ok] applied scenario={best['scenario']} → τ={tau:.2f}, core_UB={core_ub:.2f}, core={core_members}")
    print("[ok] refreshed: r³, Wegbericht, Summary, Keypoints, Bundle v1.25")

if __name__ == "__main__":
    main()
