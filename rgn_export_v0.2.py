#!/usr/bin/env python3
"""
rgn_export_v0.2 — Join TSM-136D_zonen_recommended.csv + TSM-136D_R_estimates.csv
and emit RGN_state_v0.2.csv + RGN_manifest_v0.2.json + RGN_report_v0.2.md.
Usage:
python rgn_export_v0.2.py --zones TSM-136D_zonen_recommended.csv --rest TSM-136D_R_estimates.csv --baseline TSM-136D_zonen_baseline.csv --outdir .
"""
import argparse, json, hashlib, os
from datetime import datetime, timezone
import pandas as pd
import numpy as np


def md5(path, chunk=8192):
m = hashlib.md5()
with open(path,'rb') as f:
for blk in iter(lambda: f.read(chunk), b''):
m.update(blk)
return m.hexdigest()


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--zones", required=True)
ap.add_argument("--rest", required=True)
ap.add_argument("--baseline", required=False)
ap.add_argument("--outdir", default=".")
args = ap.parse_args()


zr = pd.read_csv(args.zones)
re = pd.read_csv(args.rest)
n = min(len(zr), len(re))
df = pd.concat([zr.iloc[:n].reset_index(drop=True),
re.iloc[:n].reset_index(drop=True)], axis=1)


df['K'] = df['R_combo_norm']
df['varphi'] = df['dphi']
df['varphi_deg'] = np.degrees(df['varphi'])
df['tau_rgn'] = df['tau']
df['id'] = np.arange(len(df))


out_cols = ['id','K','varphi','varphi_deg','tau_rgn','C','F_res','F_cap','B','S','zone',
'R_Qeff_raw','R_PLV','R_combo_norm','C_cl','dphi_cl','tau_cl']
rgn = df[out_cols].copy()


os.makedirs(args.outdir, exist_ok=True)
state_path = os.path.join(args.outdir, "RGN_state_v0.2.csv")
rgn.to_csv(state_path, index=False)


# Manifest
inputs = [
{"filename": os.path.basename(args.zones), "md5": md5(args.zones), "rows": int(zr.shape[0]), "cols": int(zr.shape[1])},
{"filename": os.path.basename(args.rest), "md5": md5(args.rest), "rows": int(re.shape[0]), "cols": int(re.shape[1])}
]
if args.baseline and os.path.exists(args.baseline):
zb = pd.read_csv(args.baseline)
zr10k = zr.iloc[:min(10000,len(zr),len(zb))]
agree = float((zb['zone'].values[:len(zr10k)] == zr10k['zone'].values).mean())
else:
zb = None
agree = None


zone_shares = rgn['zone'].value_counts(normalize=True).to_dict()
corr = rgn[['K','varphi','F_res','B','S']].corr()


manifest = {
"rgn_version": "0.2",
"generated_utc": datetime.now(timezone.utc).isoformat(),
"inputs": inputs + ([{"filename": os.path.basename(args.baseline), "md5": md5(args.baseline), "rows": int(zb.shape[0]), "cols": int(zb.shape[1])}] if zb is not None else []),
"output": {"filename": "RGN_state_v0.2.csv", "md5": md5(state_path), "rows": int(rgn.shape[0]), "cols": int(rgn.shape[1])},
"mapping": {"K":"R_combo_norm","varphi":"dphi (rad)","varphi_deg":"degrees(varphi)","tau_rgn":"tau","zone":"zone","F_res":"F_res","B":"B","S":"S"},
"zone_shares": zone_shares,
"baseline_vs_recommended_match": {"n_compared": int(len(zr10k)) if args.baseline and os.path.exists(args.baseline) else None, "agreement": agree},
"correlations": corr.round(6).to_dict()
}
with open(os.path.join(args.outdir,"RGN_manifest_v0.2.json"),'w') as f:
json.dump(manifest, f, indent=2)


# Report
main()