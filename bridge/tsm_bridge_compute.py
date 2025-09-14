#!/usr/bin/env python3
from typing import List


def ecdf(values: List[float]):
# Empirische Verteilungsfunktion (nicht-absteigend)
xs = sorted(values)
n = len(xs)
def F(x: float) -> float:
# Anteil <= x (binäre Suche)
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


if not rows:
# Leere Eingabe: trotzdem Header schreiben
with open(args.out, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=["C","dphi","tau","F_res","F_cap","B","S","zone"])
w.writeheader()
return


# Basismengen
eps_rad = args.eps_deg * math.pi / 180.0
fres_list = []
for row in rows:
C = float(row.get("C") or row.get("C_cl") or row.get("C0") or 0.0)
dphi = float(row.get("dphi") or row.get("Delta_phi") or 0.0)
tau = float(row.get("tau") or row.get("tau_eff") or row.get("tau0") or 0.0)
fres = C / max(dphi, eps_rad) * tau
row["_F_res"] = fres
fres_list.append(fres)


# Cap-Quantil bestimmen (robust, indexbasiert)
q = max(0.5, min(1.0, args.cap_quantile))
xs = sorted(fres_list)
idx = int(q * (len(xs) - 1))
cap = xs[idx]


# F_cap und ECDF
fcap_list = []
for row in rows:
fcap = min(row["_F_res"], cap)
row["_F_cap"] = fcap
fcap_list.append(fcap)


F = ecdf(fcap_list)


# Ableiten von B,S,zone und Ausgabe schreiben
out_rows = []
for row in rows:
B = F(row["_F_cap"])
S = 1.0 - B
if B <= args.B_lo:
zone = "fragmentiert"
elif B <= args.B_hi:
zone = "regulativ"
else:
zone = "kohärent"
out_rows.append({
**{k: row.get(k, "") for k in row.keys() if k in ("C","dphi","tau")},
"F_res": f"{row['_F_res']:.6f}",
"F_cap": f"{row['_F_cap']:.6f}",
"B": f"{B:.5f}",
"S": f"{S:.5f}",
"zone": zone,
})


fieldnames = ["C","dphi","tau","F_res","F_cap","B","S","zone"]
with open(args.out, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=fieldnames)
w.writeheader()
for row in out_rows:
w.writerow(row)


if __name__ == "__main__":
main()
