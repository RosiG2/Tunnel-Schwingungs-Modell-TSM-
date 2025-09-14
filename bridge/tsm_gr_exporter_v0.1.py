#!/usr/bin/env python3
"""
TSM GR Exporter v0.1 — erzeugt K_field.csv und wahlweise T_eff.csv oder metric_stub.csv


Beispiel:
python tsm_gr_exporter_v0.1.py --in computed.csv --out-prefix export/exp --mode matter --rho0 1.0 --w 0.0
"""
import argparse, csv, os


def read_rows(path):
with open(path, newline="") as f:
r = csv.DictReader(f)
rows = [row for row in r]
return rows, r.fieldnames


def write_rows(path, fieldnames, rows):
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=fieldnames)
w.writeheader()
for row in rows:
w.writerow({k: row.get(k, "") for k in fieldnames})


def build_K(B, S, k_mode="B", lam=0.0):
Bf = float(B); Sf = float(S)
if k_mode == "B":
return Bf
if k_mode == "blend":
lam = max(0.0, min(1.0, float(lam)))
return (1.0 - lam) * Bf + lam * (1.0 - Bf)
return Bf


def export_matter(rows, out_prefix, rho0=1.0, w=0.0, k_mode="B", lam=0.0):
k_rows = []
t_rows = []
for i, row in enumerate(rows):
B = row.get("B", "0"); S = row.get("S", "0")
K = build_K(B, S, k_mode, lam)
k_rows.append({"i": i, "B": B, "S": S, "K": f"{K:.6f}"})
rho = rho0 * K
p = w * rho
t_rows.append({
"i": i,
"T00": f"{rho:.6f}",
"T11": f"{p:.6f}",
"T22": f"{p:.6f}",
"T33": f"{p:.6f}"
})
write_rows(f"{out_prefix}_K_field.csv", ["i", "B", "S", "K"], k_rows)
write_rows(f"{out_prefix}_T_eff.csv", ["i", "T00", "T11", "T22", "T33"], t_rows)


def export_metric(rows, out_prefix, a1=1.0, a2=0.0, a3=0.0, k_mode="B", lam=0.0):
k_rows = []
g_rows = []
for i, row in enumerate(rows):
B = row.get("B", "0"); S = row.get("S", "0")
K = build_K(B, S, k_mode, lam)
k_rows.append({"i": i, "B": B, "S": S, "K": f"{K:.6f}"})
# Symbolische delta_g-Komponente (Skalar-Stub)
dg = a1 * K
g_rows.append({"i": i, "delta_g_scalar": f"{dg:.6f}"})
write_rows(f"{out_prefix}_K_field.csv", ["i", "B", "S", "K"], k_rows)
write_rows(f"{out_prefix}_metric_stub.csv", ["i", "delta_g_scalar"], g_rows)


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out-prefix", required=True)
ap.add_argument("--mode", choices=["matter", "metric"], default="matter")
ap.add_argument("--K-mode", choices=["B", "blend"], default="B")
ap.add_argument("--lambda", dest="lam", type=float, default=0.0)
ap.add_argument("--rho0", type=float, default=1.0)
ap.add_argument("--w", type=float, default=0.0)
ap.add_argument("--metric-a1", type=float, default=1.0)
ap.add_argument("--metric-a2", type=float, default=0.0)
ap.add_argument("--metric-a3", type=float, default=0.0)
args = ap.parse_args()


rows, _ = read_rows(args.inp)
if args.mode == "matter":
export_matter(rows, args.out_prefix, args.rho0, args.w, args.K_mode, args.lam)
else:
export_metric(rows, args.out_prefix, args.metric_a1, args.metric_a2, args.metric_a3, args.K_mode, args.lam)


if __name__ == "__main__":
main()