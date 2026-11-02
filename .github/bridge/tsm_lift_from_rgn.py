#!/usr/bin/env python3
"""
TSM Lift from RGN (v0.1)
- Reads RGN_state_v0.2.csv and RGN_qc_metrics_v0.1.json (raw GitHub URLs by default)
- Updates/augments bridge_outputs/tsm_pg_facets_lifted.json with linear constraints (Cx <= d)
Usage:
  python tsm_lift_from_rgn.py --repo https://raw.githubusercontent.com/RosiG2/Tunnel-Schwingungs-Modell-TSM-/main
"""
import argparse, json, pandas as pd, numpy as np, sys
from pathlib import Path

def read_state_df(base_url: str):
    url = f"{base_url}/RGN_state_v0.2.csv"
    df = pd.read_csv(url)
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def read_qc(base_url: str):
    url = f"{base_url}/RGN_qc_metrics_v0.1.json"
    try:
        qc = pd.read_json(url, typ="series").to_dict()
    except Exception:
        # fallback for plain json
        import requests
        qc = requests.get(url, timeout=20).json()
    return qc

def load_lifted(outdir: Path):
    p = outdir / "tsm_pg_facets_lifted.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f), p

def save_lifted(obj, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def detect_group_constraints(df, zones):
    """
    Heuristic: look for columns like group, cap/max, min, include/exclude flags; map to sums over zones.
    Expect rows like: group, zone, cap/max, min (optional).
    """
    cols = set(df.columns)
    # find zone-like column
    zone_col = None
    for cand in ["zone", "zone_name", "name"]:
        if cand in cols:
            zone_col = cand
            break
    if zone_col is None:
        return []
    # group column (optional)
    group_col = None
    for cand in ["group", "klasse", "category", "cluster"]:
        if cand in cols:
            group_col = cand
            break
    caps = []
    # per-zone limits
    for _, row in df.iterrows():
        z = str(row[zone_col])
        if z not in zones: 
            continue
        for key in ["cap", "max", "ub", "upper", "upper_bound"]:
            if key in cols and pd.notna(row[key]):
                caps.append(("zone_ub", z, float(row[key])))
        for key in ["min", "lb", "lower", "lower_bound"]:
            if key in cols and pd.notna(row[key]):
                caps.append(("zone_lb", z, float(row[key])))
    # group caps
    if group_col:
        for g, gdf in df.groupby(group_col):
            # group cap keys
            for key in ["cap", "max", "ub", "upper", "upper_bound", "budget", "sum_cap"]:
                if key in gdf.columns and pd.notna(gdf[key]).any():
                    cap_val = float(gdf[key].dropna().iloc[0])
                    zs = [str(z) for z in gdf[zone_col] if str(z) in zones]
                    if zs:
                        caps.append(("group_ub", str(g), cap_val, zs))
            for key in ["min", "lb", "lower", "lower_bound", "sum_min"]:
                if key in gdf.columns and pd.notna(gdf[key]).any():
                    min_val = float(gdf[key].dropna().iloc[0])
                    zs = [str(z) for z in gdf[zone_col] if str(z) in zones]
                    if zs:
                        caps.append(("group_lb", str(g), min_val, zs))
    return caps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="https://raw.githubusercontent.com/RosiG2/Tunnel-Schwingungs-Modell-TSM-/main")
    ap.add_argument("--outdir", default="bridge_outputs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    lifted, lifted_path = load_lifted(outdir)
    zones = list(lifted["names"])
    # Pull RGN state & qc
    try:
        df_state = read_state_df(args.repo)
    except Exception as e:
        print(f"[warn] Could not read RGN_state: {e}", file=sys.stderr)
        df_state = None
    try:
        qc = read_qc(args.repo)
    except Exception as e:
        print(f"[warn] Could not read qc_metrics: {e}", file=sys.stderr)
        qc = None

    # Apply constraints
    new_cons = []
    if df_state is not None:
        caps = detect_group_constraints(df_state, zones)
        for kind, *rest in caps:
            if kind == "zone_ub":
                z, ub = rest
                i = zones.index(z)
                a = [0.0]*len(zones); a[i] = 1.0
                new_cons.append({"type":"ub","scope":"zone","zone":z,"a":a,"c":ub})
            elif kind == "zone_lb":
                z, lb = rest
                i = zones.index(z)
                a = [-1.0]*len(zones); a = [(-1.0 if j==i else 0.0) for j in range(len(zones))]
                new_cons.append({"type":"lb","scope":"zone","zone":z,"a":a,"c":-lb})
            elif kind == "group_ub":
                g, cap, zs = rest
                a = [1.0 if z in zs else 0.0 for z in zones]
                new_cons.append({"type":"ub","scope":"group","group":g,"a":a,"c":cap,"zones":zs})
            elif kind == "group_lb":
                g, m, zs = rest
                a = [-1.0 if z in zs else 0.0 for z in zones]
                new_cons.append({"type":"lb","scope":"group","group":g,"a":a,"c":-m,"zones":zs})
    if qc is not None and isinstance(qc, dict):
        # Common QC-style heuristics
        if "min_share_per_zone" in qc:
            m = float(qc["min_share_per_zone"])
            for i, z in enumerate(zones):
                a = [-1.0 if j==i else 0.0 for j in range(len(zones))]
                new_cons.append({"type":"lb","scope":"zone","zone":z,"a":a,"c":-m})
        if "max_share_per_zone" in qc:
            m = float(qc["max_share_per_zone"])
            for i, z in enumerate(zones):
                a = [1.0 if j==i else 0.0 for j in range(len(zones))]
                new_cons.append({"type":"ub","scope":"zone","zone":z,"a":a,"c":m})
        if "group_caps" in qc and isinstance(qc["group_caps"], dict):
            for g, cap in qc["group_caps"].items():
                zs = [z for z in zones if z.startswith(str(g))]  # heuristic: group prefix
                if not zs: 
                    continue
                a = [1.0 if z in zs else 0.0 for z in zones]
                new_cons.append({"type":"ub","scope":"group","group":g,"a":a,"c":float(cap),"zones":zs})

    # Merge into lifted
    lifted.setdefault("constraints", {}).setdefault("lifts", [])
    lifted["constraints"]["lifts"].extend(new_cons)
    # Update meta
    lifted.setdefault("meta", {}).setdefault("notes", []).append("RGN-based lifts applied.")
    save_lifted(lifted, lifted_path)
    print(f"[ok] Lifted facets updated -> {lifted_path}")

if __name__ == "__main__":
    main()
