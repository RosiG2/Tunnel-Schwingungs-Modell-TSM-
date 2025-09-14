#!/usr/bin/env python3
"""
rgn_export_v0.2.1 — Join TSM-136D_zonen_recommended.csv + TSM-136D_R_estimates.csv
and emit RGN_state_v0.2.csv + RGN_manifest_v0.2.json + RGN_report_v0.2.md.
Usage:
  python rgn_export_v0.2.1.py --zones TSM-136D_zonen_recommended.csv --rest TSM-136D_R_estimates.csv --baseline TSM-136D_zonen_baseline.csv --outdir .

Notes:
- Tolerant to optional columns (e.g. F_cap, C_cl, dphi_cl, tau_cl). Missing cols are skipped.
- Correlations computed on available subset among [K, varphi, F_res, B, S].
"""
import argparse, json, hashlib, os, sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np

REQUIRED_IN_ZONES = {"zone", "B", "S"}
REQUIRED_IN_REST  = {"R_combo_norm", "dphi", "tau"}

def md5(path, chunk=8192):
    m = hashlib.md5()
    with open(path,'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            m.update(blk)
    return m.hexdigest()

def avail(df, cols):
    return [c for c in cols if c in df.columns]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True)
    ap.add_argument("--rest", required=True)
    ap.add_argument("--baseline", required=False)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    zr = pd.read_csv(args.zones)
    re = pd.read_csv(args.rest)

    missing_z = REQUIRED_IN_ZONES - set(zr.columns)
    missing_r = REQUIRED_IN_REST - set(re.columns)
    if missing_z:
        sys.exit(f"Missing columns in zones CSV: {sorted(missing_z)}")
    if missing_r:
        sys.exit(f"Missing columns in R-estimates CSV: {sorted(missing_r)}")

    n = min(len(zr), len(re))
    df = pd.concat([zr.iloc[:n].reset_index(drop=True),
                    re.iloc[:n].reset_index(drop=True)], axis=1)

    # Core mappings
    df['K'] = pd.to_numeric(df['R_combo_norm'], errors='coerce')
    df['varphi'] = pd.to_numeric(df['dphi'], errors='coerce')
    df['varphi_deg'] = np.degrees(df['varphi'])
    df['tau_rgn'] = pd.to_numeric(df['tau'], errors='coerce')
    df['id'] = np.arange(len(df))

    # Output columns (tolerant)
    core = ['id','K','varphi','varphi_deg','tau_rgn']
    pass_through_required = avail(df, ['F_res','B','S','zone'])
    r_cols = avail(df, ['R_Qeff_raw','R_PLV','R_combo_norm'])
    optional = avail(df, ['F_cap','C','C_cl','dphi_cl','tau_cl'])
    out_cols = core + pass_through_required + r_cols + optional

    os.makedirs(args.outdir, exist_ok=True)
    state_path = os.path.join(args.outdir, "RGN_state_v0.2.csv")
    df[out_cols].to_csv(state_path, index=False)

    # Manifest
    inputs = [
        {"filename": os.path.basename(args.zones), "md5": md5(args.zones), "rows": int(zr.shape[0]), "cols": int(zr.shape[1])},
        {"filename": os.path.basename(args.rest), "md5": md5(args.rest), "rows": int(re.shape[0]), "cols": int(re.shape[1])}
    ]

    agree = None
    n_comp = None
    if args.baseline and os.path.exists(args.baseline):
        zb = pd.read_csv(args.baseline)
        m = min(10000, len(zb), len(zr))
        if m > 0 and 'zone' in zb.columns:
            agree = float((zb['zone'].values[:m] == zr['zone'].values[:m]).mean())
            n_comp = int(m)
        inputs.append({"filename": os.path.basename(args.baseline), "md5": md5(args.baseline), "rows": int(zb.shape[0]), "cols": int(zb.shape[1])})

    zone_shares = df['zone'].value_counts(normalize=True).to_dict() if 'zone' in df.columns else {}

    corr_cols = [c for c in ['K','varphi','F_res','B','S'] if c in df.columns]
    corr = df[corr_cols].corr().round(6).to_dict() if len(corr_cols) >= 2 else {}

    manifest = {
        "rgn_version": "0.2.1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "output": {"filename": "RGN_state_v0.2.csv", "md5": md5(state_path), "rows": int(df.shape[0]), "cols": int(len(out_cols))},
        "mapping": {"K":"R_combo_norm","varphi":"dphi (rad)","varphi_deg":"degrees(varphi)","tau_rgn":"tau"},
        "zone_shares": zone_shares,
        "baseline_vs_recommended_match": {"n_compared": n_comp, "agreement": agree},
        "correlations": corr
    }
    with open(os.path.join(args.outdir,"RGN_manifest_v0.2.json"),'w') as f:
        json.dump(manifest, f, indent=2)

    # Report
    report = []
    report.append(f"# RGN Report v0.2 — Mapping TSM→ART (Data Readiness)\n")
    report.append(f"**Date (UTC):** {manifest['generated_utc']}\n")
    report.append(f"**Inputs:** {', '.join([i['filename'] for i in inputs])}\n")
    report.append(f"**Output:** RGN_state_v0.2.csv\n")
    if zone_shares:
        report.append("\n## 1) Zone Shares\n")
        for k,v in zone_shares.items():
            report.append(f"- {k}: {v:.6f}\n")
    if agree is not None:
        report.append(f"\n## 2) Baseline vs Recommended\nAgreement: **{agree:.4f}** (first {n_comp}).\n")
    if all(c in df.columns for c in ['zone','K','varphi','F_res','B','S']):
        per_zone = df.groupby('zone')[['K','varphi','F_res','B','S']].agg(['mean','std']).reset_index()
        report.append("\n## 3) Per-Zone Summary (mean ± std)\n")
        report.append(per_zone.to_string(index=False))
        report.append("\n")
    if corr:
        report.append("\n## 4) Correlations\n")
        cdf = pd.DataFrame(corr).fillna(0)
        report.append(cdf.to_string())
        report.append("\n")

    with open(os.path.join(args.outdir, "RGN_report_v0.2.md"), 'w') as f:
        f.write('\n'.join(report))

if __name__ == '__main__':
    main()
