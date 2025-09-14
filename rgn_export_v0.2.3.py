#!/usr/bin/env python3
"""
rgn_export_v0.2.3 — robust CSV reader + auto/override column mapping + manifest/report.

Fixes:
- Auto-detects delimiter (',' ';' or '\t') and encoding ('utf-8'/'utf-8-sig').
- Auto-detects columns for K (R_combo_norm...), varphi (dphi...), tau (tau...).
- Optional manual overrides via CLI flags or mapping JSON.
"""

import argparse, json, hashlib, os, sys, re
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# ---------- utils ----------
def md5(path, chunk=8192):
    m = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            m.update(blk)
    return m.hexdigest()

def read_csv_smart(path):
    """Try reading CSV with common delimiters/encodings; fallback to sniff header."""
    tried = []
    for enc in ("utf-8", "utf-8-sig"):
        for sep in (None, ",", ";", "\t"):
            try:
                df = pd.read_csv(path, encoding=enc, sep=sep)
                tried.append((enc, sep, df.shape))
                # If only one column AND header seems glued -> try other sep
                if df.shape[1] == 1:
                    name0 = str(df.columns[0])
                    sample = ",".join([name0] + [str(df.iloc[i,0]) for i in range(min(len(df), 3))])
                    if any(d in sample for d in (";", "\t", ",")):
                        continue
                return df, (enc, sep, "ok")
            except Exception as e:
                tried.append((enc, sep, f"err:{e}"))
    # last resort: read first line and retry based on detected char
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        first = f.readline()
    sep = ";" if first.count(";") >= max(first.count(","), first.count("\t")) else ("," if first.count(",") >= first.count("\t") else "\t")
    df = pd.read_csv(path, sep=sep, encoding="utf-8", engine="python")
    return df, ("fallback", sep, "ok")

def norm(s: str) -> str:
    return re.sub(r'[^0-9a-z]+', '', s.lower())

def find_col(df, keys, prefer_substr=None):
    nmap = {norm(c): c for c in df.columns}
    for k in keys:
        if k in nmap:
            return nmap[k], k
    for nc, orig in nmap.items():
        if any(k in nc for k in keys):
            if prefer_substr and prefer_substr in nc:
                return orig, nc
    for nc, orig in nmap.items():
        if any(k in nc for k in keys):
            return orig, nc
    return None, None

def detect_fields(zr, re_df):
    K_keys = ["rcombonorm","rcombo","rnorm","r","rqeffrawnorm","rcombined","rplvnorm","r_plv","r_qeff_raw","r_combo_norm"]
    phi_keys_deg = ["dphideg","delta_phideg","phideg","phasedeg"]
    phi_keys_rad = ["dphi","delta_phi","d_phirad","phirad","phase","phi","d_phi"]
    tau_keys = ["tau","taurgn","taucl","resonancetau","t_rgn"]

    K_col, _   = find_col(re_df, K_keys)
    phi_col, t = find_col(re_df, phi_keys_rad + phi_keys_deg)
    tau_col, _ = find_col(re_df, tau_keys, prefer_substr="tau")

    zone_col, _ = find_col(zr, ["zone","zonelabel"])
    B_col, _    = find_col(zr, ["b","bind","bindung"])
    S_col, _    = find_col(zr, ["s","split","spaltung"])

    missing = []
    if not K_col:   missing.append("K (e.g. R_combo_norm)")
    if not phi_col: missing.append("varphi (e.g. dphi)")
    if not tau_col: missing.append("tau (e.g. tau)")
    if not zone_col: missing.append("zone")
    if not B_col:    missing.append("B")
    if not S_col:    missing.append("S")
    return (K_col, phi_col, tau_col, zone_col, B_col, S_col, t, missing)

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True)
    ap.add_argument("--rest", required=True)
    ap.add_argument("--baseline", required=False)
    ap.add_argument("--outdir", default=".")
    # manual overrides
    ap.add_argument("--k-col")
    ap.add_argument("--phi-col")
    ap.add_argument("--tau-col")
    ap.add_argument("--zone-col")
    ap.add_argument("--b-col")
    ap.add_argument("--s-col")
    ap.add_argument("--mapping-json", help="optional JSON with {k_col, phi_col, tau_col, zone_col, b_col, s_col}")
    args = ap.parse_args()

    zr, zr_info   = read_csv_smart(args.zones)
    re_df, re_info= read_csv_smart(args.rest)
    zb = None
    if args.baseline and os.path.exists(args.baseline):
        try:
            zb, _ = read_csv_smart(args.baseline)
        except Exception as e:
            print(f"[warn] could not read baseline '{args.baseline}': {e}", file=sys.stderr)

    print("[info] zones read:", zr_info, "shape=", zr.shape)
    print("[info] rest  read:", re_info, "shape=", re_df.shape)
    if zb is not None:
        print("[info] base  read:", "shape=", zb.shape)
    print("[info] zones columns:", list(zr.columns))
    print("[info] rest  columns:", list(re_df.columns))
    if zb is not None:
        print("[info] base  columns:", list(zb.columns))

    # mapping via JSON overrides?
    jmap = {}
    if args.mapping_json and os.path.exists(args.mapping_json):
        try:
            with open(args.mapping_json, "r", encoding="utf-8") as f:
                jmap = json.load(f)
        except Exception as e:
            print(f"[warn] mapping-json read failed: {e}", file=sys.stderr)

    # auto detect
    K_col, phi_col, tau_col, zone_col, B_col, S_col, phi_tag, missing = detect_fields(zr, re_df)

    # apply overrides (CLI > JSON > auto)
    K_col    = args.k_col    or jmap.get("k_col")    or K_col
    phi_col  = args.phi_col  or jmap.get("phi_col")  or phi_col
    tau_col  = args.tau_col  or jmap.get("tau_col")  or tau_col
    zone_col = args.zone_col or jmap.get("zone_col") or zone_col
    B_col    = args.b_col    or jmap.get("b_col")    or B_col
    S_col    = args.s_col    or jmap.get("s_col")    or S_col

    # check presence after overrides
    missing = []
    if not K_col or K_col not in re_df.columns:   missing.append(f"K (found='{K_col}')")
    if not phi_col or phi_col not in re_df.columns: missing.append(f"varphi (found='{phi_col}')")
    if not tau_col or tau_col not in re_df.columns: missing.append(f"tau (found='{tau_col}')")
    if not zone_col or zone_col not in zr.columns:  missing.append(f"zone (found='{zone_col}')")
    if not B_col or B_col not in zr.columns:        missing.append(f"B (found='{B_col}')")
    if not S_col or S_col not in zr.columns:        missing.append(f"S (found='{S_col}')")

    if missing:
        print("::error:: Column detection failed.", file=sys.stderr)
        print("  Missing/invalid:", *missing, sep="\n  ", file=sys.stderr)
        print("  zones columns:", list(zr.columns), file=sys.stderr)
        print("  rest  columns:", list(re_df.columns), file=sys.stderr)
        print("  Tip: provide --mapping-json mapping like:", file=sys.stderr)
        print('       {"k_col":"R_combo_norm","phi_col":"dphi","tau_col":"tau","zone_col":"zone","b_col":"B","s_col":"S"}', file=sys.stderr)
        sys.exit(1)

    # align & merge
    n = min(len(zr), len(re_df))
    zr = zr.iloc[:n].reset_index(drop=True)
    re_df = re_df.iloc[:n].reset_index(drop=True)
    df = pd.concat([zr, re_df], axis=1)

    # map core
    df['K'] = pd.to_numeric(df[K_col], errors='coerce')
    # varphi unit
    phi_norm = norm(phi_col)
    if ("deg" in phi_norm) or (re.search(r"(deg|grad)", phi_col, re.I) is not None):
        df['varphi'] = np.radians(pd.to_numeric(df[phi_col], errors='coerce'))
    else:
        df['varphi'] = pd.to_numeric(df[phi_col], errors='coerce')
    df['varphi_deg'] = np.degrees(df['varphi'])
    df['tau_rgn'] = pd.to_numeric(df[tau_col], errors='coerce')
    df['id'] = np.arange(len(df))

    # passthrough + optional
    def avail(cols): return [c for c in cols if c in df.columns]
    # rename B,S,zone to canonical
    if B_col != "B":    df.rename(columns={B_col:"B"}, inplace=True)
    if S_col != "S":    df.rename(columns={S_col:"S"}, inplace=True)
    if zone_col != "zone": df.rename(columns={zone_col:"zone"}, inplace=True)

    core = ['id','K','varphi','varphi_deg','tau_rgn','B','S','zone']
    r_cols = avail(['R_Qeff_raw','R_PLV','R_combo_norm'])
    optional = avail(['F_res','F_cap','C','C_cl','dphi_cl','tau_cl'])
    out_cols = core + r_cols + optional

    os.makedirs(args.outdir, exist_ok=True)
    state_path = os.path.join(args.outdir, "RGN_state_v0.2.csv")
    df[out_cols].to_csv(state_path, index=False)

    # manifest
    inputs = [
        {"filename": os.path.basename(args.zones), "md5": md5(args.zones), "rows": int(len(zr)), "cols": int(zr.shape[1])},
        {"filename": os.path.basename(args.rest),  "md5": md5(args.rest),  "rows": int(len(re_df)), "cols": int(re_df.shape[1])},
    ]
    if args.baseline and os.path.exists(args.baseline) and zb is not None:
        inputs.append({"filename": os.path.basename(args.baseline), "md5": md5(args.baseline), "rows": int(len(zb)), "cols": int(zb.shape[1])})

    agree = None; n_comp = None
    if zb is not None and 'zone' in zb.columns and 'zone' in zr.columns:
        m = min(10000, len(zb), len(zr))
        agree = float((zb['zone'].values[:m] == zr['zone'].values[:m]).mean())
        n_comp = int(m)

    corr_cols = [c for c in ['K','varphi','F_res','B','S'] if c in df.columns]
    corr = df[corr_cols].corr().round(6).to_dict() if len(corr_cols) >= 2 else {}

    manifest = {
        "rgn_version": "0.2.3",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "output": {"filename": "RGN_state_v0.2.csv", "md5": md5(state_path), "rows": int(df.shape[0]), "cols": int(len(out_cols))},
        "mapping": {"K": K_col, "varphi": phi_col, "tau_rgn": tau_col, "zone": "zone", "B":"B", "S":"S"},
        "zone_shares": df['zone'].value_counts(normalize=True).to_dict() if 'zone' in df.columns else {},
        "baseline_vs_recommended_match": {"n_compared": n_comp, "agreement": agree},
        "correlations": corr
    }
    with open(os.path.join(args.outdir, "RGN_manifest_v0.2.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # report
    rep = []
    rep.append("# RGN Report v0.2 — Mapping TSM→ART (Data Readiness)\n")
    rep.append(f"**Date (UTC):** {manifest['generated_utc']}\n")
    rep.append(f"**zones sep/enc:** {zr_info}\n**rest sep/enc:** {re_info}\n")
    rep.append(f"**Detected/used columns:** K='{K_col}', varphi='{phi_col}', tau='{tau_col}', zone='zone', B='B', S='S'\n")
    if 'zone' in df.columns:
        rep.append("\n## Zone shares\n" + df['zone'].value_counts(normalize=True).to_string() + "\n")
    if 'zone' in df.columns and all(c in df.columns for c in ['K','varphi']):
        perz = df.groupby('zone')[['K','varphi']].agg(['mean','std']).reset_index()
        rep.append("\n## Per-zone (mean ± std): K, varphi\n" + perz.to_string(index=False) + "\n")
    if corr:
        rep.append("\n## Correlations (K,varphi,F_res,B,S)\n" + pd.DataFrame(corr).fillna(0).to_string() + "\n")
    with open(os.path.join(args.outdir, "RGN_report_v0.2.md"), "w", encoding="utf-8") as f:
        f.write("".join(rep))

if __name__ == "__main__":
    main()
