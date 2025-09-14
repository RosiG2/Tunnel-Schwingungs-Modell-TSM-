#!/usr/bin/env python3
"""
rgn_qc_v0.1 — Quick checks & plots for RGN_state_v0.2.csv
Outputs:
  - RGN_qc_metrics_v0.1.json
  - RGN_qc_report_v0.1.md
  - RGN_qc_plots_v0.1/ (histograms & scatter)
Notes:
  - Works even if F_res is missing.
  - Reads baseline-vs-recommended info from RGN_manifest_v0.2.json if present.
"""
import json, os, sys, math
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

STATE = "RGN_state_v0.2.csv"
MANIF = "RGN_manifest_v0.2.json"
PLOTD = "RGN_qc_plots_v0.1"

def safe_mean(a): return float(np.nanmean(a)) if len(a) else float("nan")
def safe_std(a):  return float(np.nanstd(a, ddof=1)) if len(a) > 1 else float("nan")

def main():
    if not os.path.exists(STATE):
        print(f"::error::{STATE} not found", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(STATE)

    # Basic columns (tolerant)
    have = set(df.columns)
    cols = {
        "K":      "K" if "K" in have else None,
        "phi":    "varphi" if "varphi" in have else None,
        "phi_deg":"varphi_deg" if "varphi_deg" in have else None,
        "tau":    "tau_rgn" if "tau_rgn" in have else None,
        "zone":   "zone" if "zone" in have else None,
        "F":      "F_res" if "F_res" in have else None,
        "B":      "B" if "B" in have else None,
        "S":      "S" if "S" in have else None,
    }
    # QC metrics
    metrics = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(df)),
        "cols": list(df.columns),
        "columns_present": {k: (v is not None) for k,v in cols.items()}
    }

    # Zone shares
    if cols["zone"]:
        shares = df[cols["zone"]].value_counts(normalize=True).to_dict()
        metrics["zone_shares"] = shares
    else:
        shares = {}

    # Per-zone stats
    pz = {}
    if cols["zone"]:
        groups = df.groupby(cols["zone"])
        for z, g in groups:
            pz[z] = {}
            if cols["K"]:
                pz[z]["K_mean"]  = safe_mean(g[cols["K"]].values)
                pz[z]["K_std"]   = safe_std(g[cols["K"]].values)
            if cols["phi"]:
                pz[z]["phi_mean"]= safe_mean(g[cols["phi"]].values)
                pz[z]["phi_std"] = safe_std(g[cols["phi"]].values)
            if cols["F"]:
                pz[z]["F_mean"]  = safe_mean(g[cols["F"]].values)
                pz[z]["F_std"]   = safe_std(g[cols["F"]].values)
            if cols["B"]:
                pz[z]["B_mean"]  = safe_mean(g[cols["B"]].values)
            if cols["S"]:
                pz[z]["S_mean"]  = safe_mean(g[cols["S"]].values)
    metrics["per_zone"] = pz

    # Correlations (robust to missing)
    corr_cols = [c for c in [cols["K"], cols["phi"], cols["F"], cols["B"], cols["S"]] if c]
    if len(corr_cols) >= 2:
        cmat = df[corr_cols].corr().round(6).to_dict()
        metrics["correlations"] = cmat

    # φ "Plateau" indicator (very simple): look for density peaks in varphi histogram
    plateaus = {}
    if cols["phi"]:
        phi = df[cols["phi"]].dropna().values
        if len(phi):
            bins = np.linspace(np.nanmin(phi), np.nanmax(phi), 31)
            H, edges = np.histogram(phi, bins=bins)
            # peaks: simple local maxima
            peaks = []
            for i in range(1, len(H)-1):
                if H[i] >= H[i-1] and H[i] >= H[i+1]:
                    peaks.append({
                        "bin_center": float(0.5*(edges[i]+edges[i+1])),
                        "count": int(H[i])
                    })
            peaks = sorted(peaks, key=lambda x: -x["count"])[:3]
            plateaus = {"top_peaks": peaks, "bin_edges_sample": [float(edges[0]), float(edges[-1])]}
    metrics["phi_plateau"] = plateaus

    # Read baseline agreement (if manifest exists)
    if os.path.exists(MANIF):
        try:
            with open(MANIF, "r", encoding="utf-8") as f:
                mani = json.load(f)
            metrics["baseline_vs_recommended"] = mani.get("baseline_vs_recommended_match")
        except Exception as e:
            metrics["manifest_read_error"] = str(e)

    # Save metrics JSON
    with open("RGN_qc_metrics_v0.1.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Plots
    os.makedirs(PLOTD, exist_ok=True)
    plt.figure()
    if cols["K"]:
        plt.hist(df[cols["K"]].dropna().values, bins=30)
        plt.title("Histogram K")
        plt.xlabel("K"); plt.ylabel("count")
        plt.savefig(os.path.join(PLOTD, "hist_K.png"), bbox_inches="tight")
    plt.close()

    plt.figure()
    if cols["phi"]:
        plt.hist(df[cols["phi"]].dropna().values, bins=30)
        plt.title("Histogram varphi")
        plt.xlabel("varphi [rad]"); plt.ylabel("count")
        plt.savefig(os.path.join(PLOTD, "hist_varphi.png"), bbox_inches="tight")
    plt.close()

    if cols["K"] and cols["phi"]:
        plt.figure()
        plt.scatter(df[cols["phi"]], df[cols["K"]], s=6)
        plt.title("K vs varphi"); plt.xlabel("varphi [rad]"); plt.ylabel("K")
        plt.savefig(os.path.join(PLOTD, "scatter_K_vs_varphi.png"), bbox_inches="tight")
        plt.close()

    if cols["F"] and cols["K"]:
        plt.figure()
        plt.scatter(df[cols["K"]], df[cols["F"]], s=6)
        plt.title("F_res vs K"); plt.xlabel("K"); plt.ylabel("F_res")
        plt.savefig(os.path.join(PLOTD, "scatter_F_vs_K.png"), bbox_inches="tight")
        plt.close()

    # Report
    lines = []
    lines.append("# RGN QC Report v0.1\n")
    lines.append(f"**Generated (UTC):** {metrics['generated_utc']}\n\n")
    lines.append(f"**Rows:** {metrics['rows']}  \n")
    if "zone_shares" in metrics:
        lines.append("**Zone shares:**\n")
        for k,v in metrics["zone_shares"].items():
            lines.append(f"- {k}: {v:.6f}\n")
        lines.append("\n")
    if pz:
        lines.append("## Per-zone (mean ± std)\n")
        hdr = ["zone","K_mean","K_std","phi_mean","phi_std","F_mean","F_std","B_mean","S_mean"]
        lines.append("| " + " | ".join(hdr) + " |\n")
        lines.append("|" + " --- |"*len(hdr) + "\n")
        for z,dd in pz.items():
            def fmt(k): 
                return (f"{dd[k]:.6f}" if k in dd and isinstance(dd[k], (float,int)) and not math.isnan(dd[k]) else "–")
            row = [str(z), fmt("K_mean"), fmt("K_std"), fmt("phi_mean"), fmt("phi_std"),
                   fmt("F_mean"), fmt("F_std"), fmt("B_mean"), fmt("S_mean")]
            lines.append("| " + " | ".join(row) + " |\n")
        lines.append("\n")
    if "correlations" in metrics:
        lines.append("## Correlations (subset)\n")
        lines.append("```json\n" + json.dumps(metrics["correlations"], indent=2) + "\n```\n")
    if plateaus:
        lines.append("## φ plateau indicator (top histogram peaks)\n")
        lines.append("```json\n" + json.dumps(plateaus, indent=2) + "\n```\n")
    if "baseline_vs_recommended" in metrics:
        lines.append("## Baseline vs Recommended\n")
        lines.append("```json\n" + json.dumps(metrics["baseline_vs_recommended"], indent=2) + "\n```\n")
    lines.append("\n## Plots\n")
    for fn in ["hist_K.png","hist_varphi.png","scatter_K_vs_varphi.png","scatter_F_vs_K.png"]:
        p = os.path.join(PLOTD, fn)
        if os.path.exists(p):
            lines.append(f"- {p}\n")

    with open("RGN_qc_report_v0.1.md", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    main()
