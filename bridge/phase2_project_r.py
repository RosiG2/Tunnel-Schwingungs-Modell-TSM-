#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: Projektions-Schritt von r -> r* unter Nebenbedingungen
Liest:  bridge/tsm_pg_facets_lifted.json  (names, b, r, constraints.upper_bounds, constraints.lifts)
Erzwingt:
  - Simplex: x >= 0, sum x = 1
  - Per-Zone: LB (z.B. min_share_per_zone), UB (aus upper_bounds)
  - Gruppen-LB (z.B. core >= 0.45)
Schreibt:
  - bridge/tsm_pg_r_projected.csv  (zone, r_original, r_projected)
  - bridge/tsm_pg_r_projected.md   (Kurzbericht)
"""
import json
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"

TOL = 1e-12

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def load_problem():
    d = json.loads(J.read_text(encoding="utf-8"))
    names = d["names"]
    r = [float(v) for v in d["r"]]
    n = len(names)

    # Per-zone UBs
    ub = [1.0]*n
    for ubent in d.get("constraints", {}).get("upper_bounds", []):
        i = ubent["i"]; ub[i] = float(ubent["c"])

    # Per-zone LBs (from lifts; e.g. min_share_per_zone)
    lb = [0.0]*n
    groups_lb = {}  # group -> (indices, m)
    for L in d.get("constraints", {}).get("lifts", []):
        a, c = L.get("a"), L.get("c")
        scope, typ = L.get("scope"), L.get("type")
        if a is None or c is None: 
            continue
        # zone lb: a = [-1 at i], c = -m  ->  -x_i <= -m  ->  x_i >= m
        if typ == "lb" and scope == "zone" and L.get("zone") in names:
            i = names.index(L["zone"])
            m = -float(c)
            if m > lb[i]: 
                lb[i] = m
        # group lb: a = [-1 on group], c = -m -> sum_group(x) >= m
        if typ == "lb" and scope == "group":
            zs = L.get("zones") or []
            if not zs:
                # Fallback: aus a rekonstruieren
                zs = [names[j] for j, v in enumerate(a or []) if abs(float(v)) > 0]
            idx = [names.index(z) for z in zs if z in names]
            m = -float(c)
            if idx:
                gname = L.get("group") or "group"
                groups_lb[gname] = (idx, m)
    return names, r, lb, ub, groups_lb

def project_simplex_with_bounds(x, lb, ub):
    """
    Projektion auf {x | sum x = 1, lb_i <= x_i <= ub_i}.
    Simple Iteration: zuerst clippen, dann re-verteilen, bis sum=1 und Bounds eingehalten sind.
    """
    n = len(x)
    # initial clip
    x = [clamp(x[i], lb[i], ub[i]) for i in range(n)]
    total = sum(x)
    if abs(total - 1.0) <= 1e-15:
        return x
    # Wenn zu groß: ziehe von Komponenten mit Spielraum nach unten ab
    # Wenn zu klein: fülle in Komponenten mit Spielraum nach oben auf
    for _ in range(10000):
        total = sum(x)
        if abs(total - 1.0) <= 1e-12:
            break
        if total > 1.0:
            room = [x[i]-lb[i] for i in range(n)]
            S = sum(room)
            if S <= TOL:
                break
            factor = (total - 1.0)/S
            for i in range(n):
                dec = factor*room[i]
                x[i] = clamp(x[i]-dec, lb[i], ub[i])
        else:
            room = [ub[i]-x[i] for i in range(n)]
            S = sum(room)
            if S <= TOL:
                break
            factor = (1.0 - total)/S
            for i in range(n):
                inc = factor*room[i]
                x[i] = clamp(x[i]+inc, lb[i], ub[i])
    return [clamp(x[i], lb[i], ub[i]) for i in range(n)]

def enforce_group_lb(x, idx, m, lb, ub):
    """
    Erzwinge sum(x[idx]) >= m, durch Massetransfer von außerhalb idx.
    Greedy + anschließende Simplex-Projektion auf Bounds.
    """
    s = sum(x[i] for i in idx)
    if s + 1e-12 >= m:
        return x
    # einfache Strategie: minimal erhöhen, dann neu projizieren
    need = m - s
    per = need / max(1, len(idx))
    for i in idx:
        x[i] = clamp(x[i] + per, lb[i], ub[i])
    x = project_simplex_with_bounds(x, lb, ub)
    return x

def main():
    names, r, lb, ub, groups_lb = load_problem()
    # Schritt 1: per-Zone Bounds erzwingen
    x = project_simplex_with_bounds(r, lb, ub)
    # Schritt 2: Gruppen-LBs erzwingen
    for g, (idx, m) in groups_lb.items():
        x = enforce_group_lb(x, idx, m, lb, ub)
    # Abschluss: saubere Projektion
    x = project_simplex_with_bounds(x, lb, ub)

    # Export
    out_csv = BR / "tsm_pg_r_projected.csv"
    with out_csv.open("w", encoding="utf-8") as f:
        f.write("zone,r_original,r_projected\n")
        for z, ro, rp in zip(names, r, x):
            f.write(f"{z},{ro:.10f},{rp:.10f}\n")

    # Mini-Report
    md = [ "# Phase 2 – r → r* (Projektion)", "" ]
    md.append(f"- Zonen: **{len(names)}** | erzwinge per-Zone LB/UB + Gruppen-LBs; Simplex Σx=1.")
    if groups_lb:
        md.append("- Gruppen-LBs: " + ", ".join([f"{g}≥{m:.2f}" for g, (_, m) in groups_lb.items()]))
    md.append("")
    md.append("## Top-Diffs |r*−r|")
    diffs = sorted([(abs(rp-ro), z, ro, rp) for z, ro, rp in zip(names, r, x)], reverse=True)[:12]
    for d, z, ro, rp in diffs:
        md.append(f"- {z}: Δ|r*−r|={d:.6f} | r={ro:.6f} → r*={rp:.6f}")
    (BR/"tsm_pg_r_projected.md").write_text("\n".join(md), encoding="utf-8")

    print("[ok] wrote:", out_csv, "and tsm_pg_r_projected.md")

if __name__ == "__main__":
    main()
