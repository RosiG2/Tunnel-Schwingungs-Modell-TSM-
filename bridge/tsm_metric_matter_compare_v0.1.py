#!/usr/bin/env python3
def read_rows(path):
with open(path, newline="") as f:
r = csv.DictReader(f)
rows = [row for row in r]
return rows


def write_rows(path, fieldnames, rows):
os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
with open(path, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=fieldnames)
w.writeheader()
for row in rows:
w.writerow({k: row.get(k, "") for k in fieldnames})


def build_K(B, S, mode="B", lam=0.0):
Bf = float(B)
if mode == "B":
return Bf
if mode == "blend":
lam = max(0.0, min(1.0, float(lam)))
return (1.0 - lam) * Bf + lam * (1.0 - Bf)
return Bf


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out-prefix", required=True)
ap.add_argument("--rho0", type=float, default=1.0)
ap.add_argument("--w", type=float, default=0.0)
ap.add_argument("--metric-a1", type=float, default=1.0)
ap.add_argument("--K-mode", choices=["B","blend"], default="B")
ap.add_argument("--lambda", dest="lam", type=float, default=0.0)
args = ap.parse_args()


rows = read_rows(args.inp)


cmp_rows = []
# Histogramm: 20 Bins in [0,1]
bins = [i/20 for i in range(21)]
hist = {z: [0]*20 for z in ["fragmentiert","regulativ","kohärent"]}


for i, r in enumerate(rows):
B = r.get("B", "0"); S = r.get("S", "0")
zone = (r.get("zone") or "").strip() or "regulativ"
K = build_K(B, S, args.K_mode, args.lam)
dg = args.metric_a1 * K
rho = args.rho0 * K
p = args.w * rho
cmp_rows.append({
"i": i,
"B": f"{float(B):.6f}",
"S": f"{float(S):.6f}",
"K": f"{K:.6f}",
"delta_g_scalar": f"{dg:.6f}",
"T00": f"{rho:.6f}",
"T11": f"{p:.6f}",
"T22": f"{p:.6f}",
"T33": f"{p:.6f}"
})
# Histogramm binning
k = max(0.0, min(0.999999, K))
idx = int(k * 20) # 0..19
if zone in hist:
hist[zone][idx] += 1


write_rows(f"{args.out_prefix}_compare.csv", ["i","B","S","K","delta_g_scalar","T00","T11","T22","T33"], cmp_rows)


# Histogramm CSV schreiben
hist_rows = []
for z in ["fragmentiert","regulativ","kohärent"]:
for b in range(20):
hist_rows.append({
"zone": z,
"bin_lo": f"{bins[b]:.2f}",
"bin_hi": f"{bins[b+1]:.2f}",
"count": hist[z][b]
})
write_rows(f"{args.out_prefix}_K_hist_by_zone.csv", ["zone","bin_lo","bin_hi","count"], hist_rows)


if __name__ == "__main__":
main()