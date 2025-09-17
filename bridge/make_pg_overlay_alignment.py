#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TSM ↔ PG Overlay & Alignment
- liest:  tsm-online-bundle_v1.25.json (Fallback: v1.24, v1.23, latest)
          tsm_symbolic_bridge_v0.1.json
- baut PG-Overlays (unsigned + signed) für b, r, r★(falls da), r³
- normalisiert (unsigned: Summe=1; signed: zusätzlich abs-normalisiert)
- Metriken: L1-Delta & Kosinus-Ähnlichkeit (r³ vs r★ / b)
- schreibt: pg_overlay.csv, pg_overlay_signed.csv, pg_overlay_summary.md, pg_overlay.png
"""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1] / "bridge"
BUNDLE_CANDIDATES = ["tsm-online-bundle_v1.25.json",
                     "tsm-online-bundle_v1.24.json",
                     "tsm-online-bundle_v1.23.json",
                     "tsm-online-bundle_latest.json"]
SBR = BR / "tsm_symbolic_bridge_v0.1.json"

def pick_bundle():
    for fn in BUNDLE_CANDIDATES:
        p = BR / fn
        if p.exists():
            return p
    raise FileNotFoundError("Kein Online-Bundle gefunden (v1.25/v1.24/v1.23/latest).")

def safe_vec(x): 
    return [float(v) if v is not None else float("nan") for v in x]

def cosine(a, b):
    a = np.array(a, float); b = np.array(b, float)
    if np.all(~np.isfinite(a)) or np.all(~np.isfinite(b)): return float("nan")
    a = np.nan_to_num(a, nan=0.0); b = np.nan_to_num(b, nan=0.0)
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na==0 or nb==0: return float("nan")
    return float(np.dot(a,b)/(na*nb))

def l1(a, b):
    a = np.array(a, float); b = np.array(b, float)
    a = np.nan_to_num(a, nan=0.0); b = np.nan_to_num(b, nan=0.0)
    return float(np.sum(np.abs(a-b)))

def main():
    B = pick_bundle()
    bundle = json.loads(B.read_text(encoding="utf-8"))
    bridge = json.loads(SBR.read_text(encoding="utf-8"))

    names = list(map(str, bundle["names"]))
    b  = safe_vec(bundle["b"])
    r  = safe_vec(bundle["r"])
    rS = bundle.get("r_star")
    r3 = bundle.get("r3")
    if rS is not None: rS = safe_vec(rS)
    if r3 is not None: r3 = safe_vec(r3)

    # Mapping Zone -> (pg_facet, orientation)
    z2pg = {}
    facets_order = []
    for z in bridge.get("zones", []):
        zid = str(z["id"])
        pgf = z.get("pg_facet")
        ori = z.get("orientation", None)
        if ori is None: ori = +1  # Default
        z2pg[zid] = (pgf, int(ori) if ori in (-1,1) else +1)
        if pgf and pgf not in facets_order:
            facets_order.append(pgf)
    # Fallback, falls Facet fehlt
    for z in names:
        if z not in z2pg:
            z2pg[z] = (None, +1)

    if not facets_order:
        raise SystemExit("[err] Keine PG-Facetten in der Bridge gesetzt.")

    # Helper: Overlays
    def overlay(vec, signed=False):
        # aggregiert pro Facet
        agg = {f:0.0 for f in facets_order}
        for z, val in zip(names, vec):
            pgf, sgn = z2pg.get(z, (None, +1))
            if pgf is None: continue
            v = float(val)
            if not math.isfinite(v): v = 0.0
            agg[pgf] += (sgn*v) if signed else v
        return [agg[f] for f in facets_order]

    # Roh-Overlays
    O_b_u  = overlay(b,  signed=False)
    O_r_u  = overlay(r,  signed=False)
    O_rS_u = overlay(rS, signed=False) if rS else None
    O_r3_u = overlay(r3, signed=False) if r3 else None

    O_b_s  = overlay(b,  signed=True)
    O_r_s  = overlay(r,  signed=True)
    O_rS_s = overlay(rS, signed=True) if rS else None
    O_r3_s = overlay(r3, signed=True) if r3 else None

    # Normalisierung
    def norm1(v):
        s = sum(abs(x) for x in v)
        if s<=0: return v[:]
        return [x/s for x in v]
    O_b_u_n  = norm1(O_b_u)
    O_r_u_n  = norm1(O_r_u)
    O_rS_u_n = norm1(O_rS_u) if O_rS_u else None
    O_r3_u_n = norm1(O_r3_u) if O_r3_u else None

    O_b_s_absn  = norm1([abs(x) for x in O_b_s])
    O_r_s_absn  = norm1([abs(x) for x in O_r_s])
    O_rS_s_absn = norm1([abs(x) for x in O_rS_s]) if O_rS_s else None
    O_r3_s_absn = norm1([abs(x) for x in O_r3_s]) if O_r3_s else None

    # CSVs
    df_u = pd.DataFrame({
        "pg_facet": facets_order,
        "b":  O_b_u_n,
        "r":  O_r_u_n,
        **({"r_star": O_rS_u_n} if O_rS_u_n else {}),
        **({"r3": O_r3_u_n} if O_r3_u_n else {}),
    })
    df_u.to_csv(BR/"pg_overlay.csv", index=False)

    df_s = pd.DataFrame({
        "pg_facet": facets_order,
        "b_signed":  O_b_s,
        "r_signed":  O_r_s,
        **({"r_star_signed": O_rS_s} if O_rS_s else {}),
        **({"r3_signed": O_r3_s} if O_r3_s else {}),
        "b_absnorm":  O_b_s_absn,
        "r_absnorm":  O_r_s_absn,
        **({"r_star_absnorm": O_rS_s_absn} if O_rS_s_absn else {}),
        **({"r3_absnorm": O_r3_s_absn} if O_r3_s_absn else {}),
    })
    df_s.to_csv(BR/"pg_overlay_signed.csv", index=False)

    # Metriken (unsigned, normalisiert)
    lines = ["# PG-Overlay — Alignment Report", f"- bundle: `{B.name}`", ""]
    if O_rS_u_n and O_r3_u_n:
        lines += ["## r³ vs r★ (PG, unsigned+norm)"]
        lines += [f"- L1-Delta: {l1(O_r3_u_n, O_rS_u_n):.6f}",
                  f"- Kosinus:  {cosine(O_r3_u_n, O_rS_u_n):.6f}", ""]
    lines += ["## r³ vs b (PG, unsigned+norm)"]
    lines += [f"- L1-Delta: {l1(O_r3_u_n, O_b_u_n) if O_r3_u_n else float('nan'):.6f}",
              f"- Kosinus:  {cosine(O_r3_u_n, O_b_u_n) if O_r3_u_n else float('nan'):.6f}", ""]

    # Plot (unsigned normalized)
    if O_r3_u_n:
        X = np.arange(len(facets_order))
        W = 0.22
        fig, ax = plt.subplots(figsize=(8,4.5), dpi=160)
        ax.bar(X-1.5*W, O_b_u_n,  width=W, label="b")
        ax.bar(X-0.5*W, O_r_u_n,  width=W, label="r")
        if O_rS_u_n: ax.bar(X+0.5*W, O_rS_u_n, width=W, label="r★")
        ax.bar(X+1.5*W, O_r3_u_n, width=W, label="r³")
        ax.set_xticks(X); ax.set_xticklabels(facets_order, rotation=0)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("PG share (unsigned, normalized)")
        ax.set_title("TSM → PG Overlay")
        ax.legend(ncol=4, frameon=False, fontsize=8, loc="upper center")
        fig.tight_layout()
        fig.savefig(BR/"pg_overlay.png")

    (BR/"pg_overlay_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("[ok] wrote:", BR/"pg_overlay.csv", BR/"pg_overlay_signed.csv", BR/"pg_overlay_summary.md", BR/"pg_overlay.png")

if __name__ == "__main__":
    main()
