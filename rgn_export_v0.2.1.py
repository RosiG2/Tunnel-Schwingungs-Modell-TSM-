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
REQUIRED_IN_REST = {"R_combo_norm", "dphi", "tau"}




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
main()