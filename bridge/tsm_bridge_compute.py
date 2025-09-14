#!/usr/bin/env python3
"""
TSM Bridge Compute v0.2 — robust, ohne verschachtelte Funktionen
Berechnet F_res, F_cap, B, S, zone aus C,dphi,tau.
"""
import argparse
import csv
import math
from bisect import bisect_right


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", dest="out", required=True)
ap.add_argument("--eps-deg", type=float, default=1.0)
ap.add_argument("--cap-quantile", type=float, default=0.99)
ap.add_argument("--B-lo", type=float, default=0.2)
ap.add_argument("--B-hi", type=float, default=0.8)
args = ap.parse_args()


# Eingabe lesen
with open(args.inp, newline="") as f:
r = csv.DictReader(f)
rows = [row for row in r]


if not rows:
with open(args.out, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=["C","dphi","tau","F_res","F_cap","B","S","zone"])
w.writeheader()
return


# Grundgrößen
eps_rad = args.eps_deg * math.pi / 180.0
fres_list = []
for row in rows:
C = float(row.get("C", 0.0) or 0.0)
dphi = float(row.get("dphi", 0.0) or 0.0)
tau = float(row.get("tau", 0.0) or 0.0)
fres = C / max(dphi, eps_rad) * tau
row["_F_res"] = fres
fres_list.append(fres)


# Cap-Quantil
xs = sorted(fres_list)
q = max(0.5, min(1.0, args.cap_quantile))
idx = int(q * (len(xs) - 1))
cap = xs[idx]


# F_cap und B/S via Rang (ECDF)
fcap_list = [min(fr, cap) for fr in fres_list]
fcap_sorted = sorted(fcap_list)


out_rows = []
n = len(fcap_sorted)
for row, fcap in zip(rows, fcap_list):
B = bisect_right(fcap_sorted, fcap) / n
S = 1.0 - B
if B <= args.B_lo:
zone = "fragmentiert"
elif B <= args.B_hi:
zone = "regulativ"
else:
zone = "kohärent"
out_rows.append({
"C": f"{float(row.get('C',0.0)):.6f}",
"dphi": f"{float(row.get('dphi',0.0)):.6f}",
"tau": f"{float(row.get('tau',0.0)):.6f}",
"F_res": f"{row['_F_res']:.6f}",
"F_cap": f"{fcap:.6f}",
"B": f"{B:.5f}",
"S": f"{S:.5f}",
"zone": zone
})


with open(args.out, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=["C","dphi","tau","F_res","F_cap","B","S","zone"])
w.writeheader()
w.writerows(out_rows)


if __name__ == "__main__":
main()
