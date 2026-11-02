#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: Projektion r -> r³ (feasible unter: Simplex, per-Zone LB/UB inkl. Lifts, Gruppen-LB/UB)
Liest:  bridge/tsm_pg_facets_lifted.json
Schreibt: bridge/tsm_pg_r_projected_p3.csv + bridge/tsm_pg_r_projected_p3.md
"""
import json
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"
TOL = 1e-12

def clamp(x, lo, hi): return max(lo, min(hi, x))

def load_problem():
    d = json.loads(J.read_text(encoding="utf-8"))
    names = list(map(str, d["names"]))
    r = [float(v) for v in d["r"]]
    n = len(names)
    # Basis-UBs
    ub = [1.0]*n
    for ubent in d.get("constraints", {}).get("upper_bounds", []):
        i = ubent["i"]; ub[i] = float(ubent["c"])
    # Lifts -> LB/UB je Zone + Gruppen-LBs/UBs
    lb = [0.0]*n
    groups_lb = {}  # name -> (idx, m)
    groups_ub = {}  # name -> (idx, M)
    for L in d.get("constraints", {}).get("lifts", []) or []:
        a, c = L.get("a"), L.get("c")
        if a is None or c is None: continue
        typ = L.get("type"); scope = L.get("scope")
        # ZONE LBs/UBs
        if scope == "zone" and L.get("zone") in names:
            i = names.index(L["zone"])
            if typ == "lb":  # -x_i <= -m -> x_i >= m
                m = -float(c)
                if m > lb[i]: lb[i] = m
            elif typ == "ub":  # +x_i <= M -> x_i <= M
                M = float(c)
                if M < ub[i]: ub[i] = M
        # GROUP LBs/UBs
        if scope == "group":
            zs = L.get("zones") or [names[j] for j, v in enumerate(a or []) if abs(float(v))>0]
            idx = [names.index(z) for z in zs if z in names]
            if not idx: continue
            if typ == "lb":
                m = -float(c)
                groups_lb[L.get("group") or "group"] = (idx, m)
            elif typ == "ub":
                M = float(c)
                groups_ub[L.get("group") or "group"] = (idx, M)
    return names, r, lb, ub, groups_lb, groups_ub

def project_simplex_with_bounds(x, lb, ub):
    n = len(x)
    x = [clamp(x[i], lb[i], ub[i]) for i in range(n)]
    for _ in range(10000):
        s = sum(x)
        if abs(s-1.0) <= 1e-12: break
        if s > 1.0:
            room = [x[i]-lb[i] for i in range(n)]; R=sum(room)
            if R <= TOL: break
            f = (s-1.0)/R
            for i in range(n):
                x[i] = clamp(x[i]-f*room[i], lb[i], ub[i])
        else:
            room = [ub[i]-x[i] for i in range(n)]; R=sum(room)
            if R <= TOL: break
            f = (1.0-s)/R
            for i in range(n):
                x[i] = clamp(x[i]+f*room[i], lb[i], ub[i])
    return [clamp(x[i], lb[i], ub[i]) for i in range(n)]

def enforce_group_bound(x, idx, bound, lb, ub, is_lb=True):
    s = sum(x[i] for i in idx)
    if (is_lb and s+1e-12 >= bound) or ((not is_lb) and s-1e-12 <= bound):
        return x
    if is_lb:
        need = max(0.0, bound - s)
        # fülle gleichmäßig in Gruppe, dann neu projizieren
        per = need / max(1, len(idx))
        for i in idx: x[i] = clamp(x[i]+per, lb[i], ub[i])
    else:
        # zu viel Masse in Gruppe: gleichmäßig reduzieren
        excess = max(0.0, s - bound)
        per = excess / max(1, len(idx))
        for i in idx: x[i] = clamp(x[i]-per, lb[i], ub[i])
    return project_simplex_with_bounds(x, lb, ub)

def main():
    names, r, lb, ub, glb, gub = load_problem()
    x = project_simplex_with_bounds(r, lb, ub)
    for g,(idx,m) in glb.items(): x = enforce_group_bound(x, idx, m, lb, ub, is_lb=True)
    for g,(idx,M) in gub.items(): x = enforce_group_bound(x, idx, M, lb, ub, is_lb=False)
    x = project_simplex_with_bounds(x, lb, ub)
    # Export
    (BR/"tsm_pg_r_projected_p3.csv").write_text(
        "zone,r_original,r_projected\n" + "\n".join(f"{z},{ro:.10f},{rp:.10f}" for z,ro,rp in zip(names, r, x)),
        encoding="utf-8"
    )
    # Mini-Report
    diffs = sorted([(abs(rp-ro), z, ro, rp) for z,ro,rp in zip(names, r, x)], reverse=True)[:12]
    lines = ["# Phase 3 – r → r³ (Projektion)", "", f"- Zonen: **{len(names)}** | Caps aktiv (Δ-Korridor & ggf. core≤UB).", "", "## Top-Diffs |r³−r|"]
    for d,z,ro,rp in diffs:
        lines.append(f"- {z}: Δ|r³−r|={d:.6f} | r={ro:.6f} → r³={rp:.6f}")
    (BR/"tsm_pg_r_projected_p3.md").write_text("\n".join(lines), encoding="utf-8")
    print("[ok] wrote: tsm_pg_r_projected_p3.(csv|md)")

if __name__ == "__main__":
    main()
