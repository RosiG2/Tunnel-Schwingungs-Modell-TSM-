#!/usr/bin/env python3
"""
tsm_bridge_compute.py — berechnet F_res, F_cap, B, S, zone aus C,dphi,tau.


Nutzung:
python tsm_bridge_compute.py --in INPUT.csv --out OUTPUT.csv \
--eps-deg 1.0 --cap-quantile 0.99 --B-lo 0.2 --B-hi 0.8
"""
import argparse, csv, math, statistics
from typing import List, Dict


def ecdf(values: List[float]):
xs = sorted(values)
n = len(xs)
def F(x: float) -> float:
# Anteil <= x
# +1e-9 numerische robustheit
lo, hi = 0, n
while lo < hi:
mid = (lo + hi) // 2
if xs[mid] <= x:
lo = mid + 1
else:
hi = mid
return lo / n
return F


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", dest="out", required=True)
ap.add_argument("--eps-deg", type=float, default=1.0)
ap.add_argument("--cap-quantile", type=float, default=0.99)
ap.add_argument("--B-lo", type=float, default=0.2)
ap.add_argument("--B-hi", type=float, default=0.8)
args = ap.parse_args()


# Einlesen
rows = []
with open(args.inp, newline="") as f:
r = csv.DictReader(f)
for row in r:
rows.append(row)


# Basismengen
eps_rad = args.eps_deg * math.pi / 180.0
F_res = []
for row in rows:
C = float(row.get("C") or row.get("C_cl") or row.get("C0") or 0.0)
dphi = float(row.get("dphi") or row.get("Delta_phi") or 0.0)
tau = float(row.get("tau") or row.get("tau_eff") or row.get("tau0") or 0.0)
fres = C / max(dphi, eps_rad) * tau
row["_F_res"] = fres
F_res.append(fres)


# Cap
q = max(0.5, min(1.0, args.cap_quantile))
# robustes Quantil
Fc_sorted = sorted(F_res)
idx = int(q * (len(Fc_sorted)-1))
cap = Fc_sorted[idx]


for row in rows:
row["_F_cap"] = min(row["_F_res"], cap)


# B/S via ECDF
F = ecdf([row["_F_cap"] for row in rows])
for row in rows:
B = F(row["_F_cap"])
S = 1.0 - B
if B <= args.B_lo:
zone = "fragmentiert"
elif B <= args.B_hi:
zone = "regulativ"
else:
zone = "kohärent"
row["F_res"] = f"{row['_F_res']:.6f}"
row["F_cap"] = f"{row['_F_cap']:.6f}"
row["B"] = f"{B:.5f}"
row["S"] = f"{S:.5f}"
row["zone"] = zone


# Schreiben
fieldnames = list(rows[0].keys())
# Entferne interne Spalten
fieldnames = [fn for fn in fieldnames if not fn.startswith("_")]
with open(args.out, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=fieldnames)
w.writeheader()
for row in rows:
w.writerow({k: row.get(k, "") for k in fieldnames})


if __name__ == "__main__":
main()