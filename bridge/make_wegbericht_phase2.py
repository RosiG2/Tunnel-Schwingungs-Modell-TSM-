#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: Wegbericht + Bindings + Plots unter strikteren Nebenbedingungen
Liest:
  - bridge/tsm_pg_changes.csv
  - bridge/tsm_pg_facets_lifted.json (inkl. RGN-Lifts, re-margined UBs)
Schreibt:
  - bridge/wegbericht_b_to_r_phase2.md
  - bridge/tsm_pg_bindings_phase2.csv
  - bridge/phase2_binding_counts.png
  - bridge/phase2_residuum_scores.(csv|md|png)
"""
import json, pandas as pd, numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
changes_csv = BR / "tsm_pg_changes.csv"
lifted_json = BR / "tsm_pg_facets_lifted.json"

TOL = 1e-9

def eval_ineq(a, c, x):
    """Slack = c - a^T x  (>=0 erfüllt; |slack|<=TOL -> bindend)"""
    return float(c) - float(np.dot(np.array(a, dtype=float), x))

def involved_zones(L, names):
    if L.get("scope") == "zone" and L.get("zone") in names:
        return [L["zone"]]
    if L.get("zones"):
        return [z for z in L["zones"] if z in names]
    a = L.get("a") or []
    return [names[j] for j, v in enumerate(a) if abs(float(v)) > 0]

def main():
    if not changes_csv.exists():
        raise FileNotFoundError(f"{changes_csv} nicht gefunden.")
    if not lifted_json.exists():
        raise FileNotFoundError(f"{lifted_json} nicht gefunden.")

    # Load
    chg = pd.read_csv(changes_csv)  # erwartet: zone,b,r,delta,rel_change,rank_abs,rank_rel
    with open(lifted_json, "r", encoding="utf-8") as f:
        lifted = json.load(f)

    names = lifted["names"]
    b_vec = np.array(lifted["b"], dtype=float)
    r_vec = np.array(lifted["r"], dtype=float)

    # UB map
    ub_map = {}
    for ub in lifted.get("constraints", {}).get("upper_bounds", []):
        i = ub["i"]
        ub_map[names[i]] = float(ub["c"])

    # Bindings Grundfacetten
    rows = []
    for i, z in enumerate(names):
        bi, ri = float(b_vec[i]), float(r_vec[i])
        ub = ub_map.get(z, 1.0)
        rows.append(dict(
            zone=z, b_x=bi, r_x=ri,
            bind_b_lb=(bi <= TOL),
            bind_r_lb=(ri <= TOL),
            ub=ub,
            bind_b_ub=((ub - bi) <= 1e-9),
            bind_r_ub=((ub - ri) <= 1e-9),
        ))
    bind = pd.DataFrame(rows)

    # Join mit Änderungen (nutze chg.b/chg.r als Referenzwerte im Report)
    chg_ren = chg.rename(columns={"b": "b_chg", "r": "r_chg"})
    df2 = chg_ren.merge(bind, on="zone", how="left")
    df2["abs_delta"] = df2["delta"].abs()

    # Lifts verarbeiten
    lifts = lifted.get("constraints", {}).get("lifts", [])
    act_rows = []
    for i, L in enumerate(lifts):
        a, c = L.get("a"), L.get("c")
        if a is None or c is None:
            continue
        sb = eval_ineq(a, c, b_vec); rb = abs(sb) <= TOL
        sr = eval_ineq(a, c, r_vec); rr = abs(sr) <= TOL
        inv = involved_zones(L, names)
        act_rows.append(dict(
            idx=i, type=L.get("type", "?"), scope=L.get("scope"),
            zone=L.get("zone"), group=L.get("group"),
            zones=",".join(inv),
            bind_b=bool(rb), bind_r=bool(rr)
        ))
    df_act = pd.DataFrame(act_rows)

    # Lift-Bindings pro Zone
    zone2b = {z: [] for z in names}; zone2r = {z: [] for z in names}
    for _, row in df_act.iterrows():
        tag = f"{row.get('type','?')}/{row.get('scope','?')}:{row.get('group') or row.get('zone') or row.get('idx')}"
        inv = row.get("zones") or ""
        for z in [s for s in inv.split(",") if s]:
            if row.get("bind_b"): zone2b[z].append(tag)
            if row.get("bind_r"): zone2r[z].append(tag)

    df2["lift_bind_b"] = df2["zone"].map(lambda z: ";".join(zone2b.get(z, [])))
    df2["lift_bind_r"] = df2["zone"].map(lambda z: ";".join(zone2r.get(z, [])))

    # Export CSV (Phase 2)
    out_csv = BR / "tsm_pg_bindings_phase2.csv"
    df2.sort_values(["abs_delta", "rank_rel"], ascending=[False, True], inplace=True)
    df2.to_csv(out_csv, index=False)

    # Wegbericht
    lines = []
    lines.append("# Wegbericht b → r (Phase 2: striktere UBs + RGN-Lifts)")
    lines.append("")
    lines.append(f"- Zonen: **{len(names)}** | Lifts: **{len(lifts)}** | Margin: **0.02**")
    lines.append("- Facetten: 0 ≤ x_i, Σx_i=1; pro-Zone UB = max(b_i,r_i)+0.02; RGN-Lifts aus state/qc.")
    lines.append("")
    lines.append("## Top-Änderungen (mit Facetten-/Lift-Status)")
    for _, row in df2.head(20).iterrows():
        flags = []
        if row["bind_b_lb"]: flags.append("b@LB")
        if row["bind_r_lb"]: flags.append("r@LB")
        if row["bind_b_ub"]: flags.append("b@UB")
        if row["bind_r_ub"]: flags.append("r@UB")
        if row["lift_bind_b"]: flags.append(f"b@LIFT[{row['lift_bind_b']}]")
        if row["lift_bind_r"]: flags.append(f"r@LIFT[{row['lift_bind_r']}]")
        flag_str = (" [" + ", ".join(flags) + "]") if flags else ""
        lines.append(f"- {row['zone']}: Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b_chg']:.6f} → r={row['r_chg']:.6f}{flag_str}")

    (BR / "wegbericht_b_to_r_phase2.md").write_text("\n".join(lines), encoding="utf-8")

    # Binding-Counts Plot
    b_lb = int((df2["bind_b_lb"] == True).sum()); r_lb = int((df2["bind_r_lb"] == True).sum())
    b_ub = int((df2["bind_b_ub"] == True).sum()); r_ub = int((df2["bind_r_ub"] == True).sum())
    lift_b = int((df_act["bind_b"] == True).sum()) if not df_act.empty else 0
    lift_r = int((df_act["bind_r"] == True).sum()) if not df_act.empty else 0

    labels = ["b@LB", "r@LB", "b@UB", "r@UB", "LIFT(b)", "LIFT(r)"]
    values = [b_lb, r_lb, b_ub, r_ub, lift_b, lift_r]
    plt.figure(figsize=(7, 4.5))
    plt.bar(labels, values)
    plt.title("Phase 2 – Facetten- & LIFT-Bindings (Counts)")
    plt.xlabel("Binding-Typ"); plt.ylabel("Anzahl")
    plt.tight_layout(); plt.savefig(BR / "phase2_binding_counts.png", dpi=150); plt.close()

    # Residuum-Score (wie Phase 1, aber mit Phase-2-Flags)
    df2["rank_rel"] = pd.to_numeric(df2["rank_rel"], errors="coerce")
    base = df2["abs_delta"] / (df2["abs_delta"].max() or 1.0)
    score = base.copy()
    score += df2["bind_r_lb"].astype(float)*0.35 + df2["bind_b_lb"].astype(float)*0.20
    score += df2["bind_r_ub"].astype(float)*0.25 + df2["bind_b_ub"].astype(float)*0.15
    score += df2["lift_bind_r"].astype(str).str.len().gt(0).astype(float)*0.30
    score += df2["lift_bind_b"].astype(str).str.len().gt(0).astype(float)*0.15
    score = score.clip(0.0, 1.0)

    rs = df2[["zone", "b_chg", "r_chg", "delta", "rel_change", "rank_abs", "rank_rel", "abs_delta"]].copy()
    rs.rename(columns={"b_chg":"b", "r_chg":"r"}, inplace=True)
    rs["score"] = score
    rs.sort_values(["score", "abs_delta", "rank_rel"], ascending=[False, False, True], inplace=True, na_position="last")
    rs.to_csv(BR / "phase2_residuum_scores.csv", index=False)

    lines = ["# Phase 2 – Residuum-Score (heuristisch)", ""]
    for _, row in rs.head(20).iterrows():
        lines.append(f"- {row['zone']}: score={row['score']:.3f} | Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b']:.6f} → r={row['r']:.6f}")
    (BR / "phase2_residuum_scores.md").write_text("\n".join(lines), encoding="utf-8")

    plt.figure(figsize=(8.2, 5))
    plt.barh(list(rs.head(15)["zone"][::-1].astype(str)), list(rs.head(15)["score"][::-1]))
    plt.xlabel("Residuum-Score (0..1)"); plt.ylabel("Zone")
    plt.title("Phase 2 – Top 15 Residuum-Score")
    plt.tight_layout(); plt.savefig(BR / "phase2_residuum_scores.png", dpi=150); plt.close()

    print("[ok] Wrote Phase 2 outputs in bridge/…")

if __name__ == "__main__":
    main()
