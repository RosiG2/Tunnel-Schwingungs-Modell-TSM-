#!/usr/bin/env python3
"""
rgn_export_v0.2.2 — Robust join + manifest/report.
- Auto-detects columns for K (R_combo_norm etc.), varphi (dphi etc.), tau (tau/tau_cl/...).
- Tolerant to case/underscores/spaces; converts degrees->radians when detected.
- Prints helpful diagnostics on failure.
"""
import argparse, json, hashlib, os, sys, re
from datetime import datetime, timezone
import pandas as pd
import numpy as np

def md5(path, chunk=8192):
    import hashlib
    m = hashlib.md5()
    with open(path,'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            m.update(blk)
    return m.hexdigest()

def norm(s: str) -> str:
    # normalize column name: lowercase + keep alnum only
    return re.sub(r'[^0-9a-z]+', '', s.lower())

def find_col(df, keys, prefer_substr=None):
    """
    keys: list of canonical tokens to look for in normalized colnames (any match)
    prefer_substr: if provided, prefer names containing this substring (already normalized)
    returns (column_name, normalized_name)
    """
    nmap = {norm(c): c for c in df.columns}
    # direct hits
    for k in keys:
        if k in nmap: 
            return nmap[k], k
    # substring hits
    for nc, orig in nmap.items():
        if any(k in nc for k in keys):
            if prefer_substr and prefer_substr in nc:
                return orig, nc
    for nc, orig in nmap.items():
        if any(k in nc for k in keys):
            return orig, nc
    return None, None

def detect_fields(zr, re_df):
    # candidates (normalized)
    K_keys = ["rcombonorm","rcombo","rnorm","r","rqeffrawnorm","rcombined","r_plvnorm"]
    phi_keys_deg = ["dphideg","delta_phideg","phideg","phasedeg"]
    phi_keys_rad = ["dphi","delta_phi","d_phirad","phirad","phase","phi"]
    tau_keys = ["tau","taurgn","taucl","resonancetau","t_rgn"]

    K_col, _ = find_col(re_df, K_keys)
    phi_col, phi_tag = find_col(re_df, phi_keys_rad + phi_keys_deg)
    tau_col, _ = find_col(re_df, tau_keys, prefer_substr="tau")

    missing = []
    if not K_col: missing.append("K (e.g. R_combo_norm)")
    if not phi_col: missing.append("varphi (e.g. dphi)")
    if not tau_col: missing.append("tau (e.g. tau)")
    return (K_col, phi_col, tau_col, phi_tag, missing)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True)
    ap.add_argument("--rest", required=True)
    ap.add_argument("--baseline", required=False)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    # Load CSVs
    zr = pd.read_csv(args.zones)
    re_df = pd.read_csv(args.rest)
    zb = None
    if args.baseline and os.path.exists(args.baseline):
        try:
            zb = pd.read_csv(args.baseline)
        except Exception as e:
            print(f"[warn] could not read baseline '{args.baseline}': {e}", file=sys.stderr)

    print("[info] zones columns:", list(zr.columns))
    print("[info] rest  columns:", list(re_df.columns))
    if zb is not None:
        print("[info] baseline columns:", list(zb.columns))

    # Detect essential fields
    K_col, phi_col, tau_col, phi_tag, missing = detect_fields(zr, re_df)
    # zones essentials
    zone_col, _ = find_col(zr, ["zone"])
    B_col, _    = find_col(zr, ["b"])
    S_col, _    = find_col(zr, ["s"])

    if missing or not zone_col or not B_col or not S_col:
        print("::error:: Column detection failed.", file=sys.stderr)
        print("  needed in zones: zone, B, S", file=sys.stderr)
        print("  needed in rest : K (R_combo_norm), varphi (dphi), tau (tau)", file=sys.stderr)
        print("  detected:", file=sys.stderr)
        print(f"    zones: zone={zone_col}, B={B_col}, S={S_col}", file=sys.stderr)
        print(f"    rest : K={K_col}, varphi={phi_col}, tau={tau_col}", file=sys.stderr)
        print("  all zones cols:", list(zr.columns), file=sys.stderr)
        print("  all rest  cols:", list(re_df.columns), file=sys.stderr)
        sys.exit(1)

    # Align lengths
    n = min(len(zr), len(re_df))
    zr = zr.iloc[:n].reset_index(drop=True)
    re_df = re_df.iloc[:n].reset_index(drop=True)
    df = pd.concat([zr, re_df], axis=1)

    # Map core
    df['K'] = pd.to_numeric(df[K_col], errors='coerce')

    # varphi: auto degrees->radians if 'deg' in normalized name
    if phi_tag and "deg" in phi_tag:
        df['varphi'] = np.radians(pd.to_numeric(df[phi_col], errors='coerce'))
    else:
        df['varphi'] = pd.to_numeric(df[phi_col], errors='coerce')
    df['varphi_deg'] = np.degrees(df['varphi'])

    df['tau_rgn'] = pd.to_numeric(df[tau_col], errors='coerce')
    df['id'] = np.arange(len(df))

    # Collect outputs gracefully
    def avail(cols):
        return [c for c in cols if c in df.columns]

    core = ['id','K','varphi','varphi_deg','tau_rgn']
    pass_through = avail([zone_col, B_col, S_col])
    pass_through_ren = []
    for c in pass_through:
        if norm(c) == 'b': df.rename(columns={c:'B'}, inplace=True); pass_through_ren.append('B')
        elif norm(c) == 's': df.rename(columns={c:'S'}, inplace=True); pass_through_ren.append('S')
        elif norm(c) == 'zone': df.rename(columns={c:'zone'}, inplace=True); pass_through_ren.append('zone')
        else: pass_through_ren.append(c)

    r_cols = avail(['R_Qeff_raw','R_PLV','R_combo_norm'])
    optional = avail(['F_res','F_cap','C','C_cl','dphi_cl','tau_cl'])

    out_cols = core + pass_through_ren + r_cols + optional
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)
    state_path = os.path.join(outdir, "RGN_state_v0.2.csv")
    df[out_cols].to_csv(state_path, index=False)

    # Manifest
    inputs = [
        {"filename": os.path.basename(args.zones), "md5": md5(args.zones), "rows": int(len(zr)), "cols": int(zr.shape[1])},
        {"filename": os.path.basename(args.rest), "md5": md5(args.rest), "rows": int(len(re_df)), "cols": int(re_df.shape[1])},
    ]
    agree = None; n_comp = None
    if zb is not None and 'zone' in zb.columns and 'zone' in zr.columns:
        m = min(10000, len(zb), len(zr))
        agree = float((zb['zone'].values[:m] == zr['zone'].values[:m]).mean())
        n_comp = int(m)

    corr_cols = [c for c in ['K','varphi','F_res','B','S'] if c in df.columns]
    corr = df[corr_cols].corr().round(6).to_dict() if len(corr_cols) >= 2 else {}

    manifest = {
        "rgn_version": "0.2.2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs + ([{"filename": os.path.basename(args.baseline), "md5": md5(args.baseline), "rows": int(len(zb)), "cols": int(zb.shape[1])}] if zb is not None else []),
        "output": {"filename": "RGN_state_v0.2.csv", "md5": md5(state_path), "rows": int(df.shape[0]), "cols": int(len(out_cols))},
        "mapping": {"K": K_col, "varphi": phi_col, "tau_rgn": tau_col},
        "zone_shares": df['zone'].value_counts(normalize=True).to_dict() if 'zone' in df.columns else {},
        "baseline_vs_recommended_match": {"n_compared": n_comp, "agreement": agree},
        "correlations": corr
    }
    with open(os.path.join(outdir,"RGN_manifest_v0.2.json"),'w') as f:
        json.dump(manifest, f, indent=2)

    # Report (compact)
    report = []
    report.append("# RGN Report v0.2 — Mapping TSM→ART (Data Readiness)\n")
    report.append(f"**Date (UTC):** {manifest['generated_utc']}\n")
    report.append(f"**Detected columns:** K='{K_col}', varphi='{phi_col}' ({'deg->rad' if (phi_tag and 'deg' in phi_tag) else 'rad'}), tau='{tau_col}'\n")
    if 'zone' in df.columns: 
        shares = df['zone'].value_counts(normalize=True)
        report.append("\n## Zone shares\n" + shares.to_string() + "\n")
    if 'zone' in df.columns and all(c in df.columns for c in ['K','varphi']):
        per_zone = df.groupby('zone')[['K','varphi']].agg(['mean','std']).reset_index()
        report.append("\n## Per-zone (mean ± std) for K, varphi\n")
        report.append(per_zone.to_string(index=False) + "\n")
    if corr:
        report.append("\n## Correlations (K,varphi,F_res,B,S)\n")
        report.append(pd.DataFrame(corr).fillna(0).to_string() + "\n")
    with open(os.path.join(outdir, "RGN_report_v0.2.md"), 'w') as f:
        f.write(''.join(report))

if __name__ == '__main__':
    main()
