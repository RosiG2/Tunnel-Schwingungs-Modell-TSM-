#!/usr/bin/env python3
return xs[k]
out = []
for z in ["fragmentiert","regulativ","kohärent"]:
xs = acc.get(z, [])
if xs:
out.append({
"zone": z,
"min": min(xs),
"p10": pctl(xs, 0.10),
"median": median(xs),
"mean": mean(xs),
"p90": pctl(xs, 0.90),
"max": max(xs),
"count": len(xs)
})
else:
out.append({"zone": z, "min": "", "p10": "", "median": "", "mean": "", "p90": "", "max": "", "count": 0})
return out


def coherence_index(rows):
dist = zone_distribution(rows)
d = {r["zone"]: to_float(r["pct"], 0.0) for r in dist}
ci = d.get("kohärent",0.0) - d.get("fragmentiert",0.0)
return [{"coherence_index": round(ci,6)}]


# Transition Matrix (optional)


def transition_matrix(rows, id_col, time_col):
if not id_col or not time_col:
return []
groups = defaultdict(list)
for r in rows:
rid = r.get(id_col, "")
t = r.get(time_col, "")
groups[rid].append((t, (r.get("zone") or "").strip() or "regulativ"))
states = ["fragmentiert","regulativ","kohärent"]
idx = {s:i for i,s in enumerate(states)}
mat = [[0]*3 for _ in range(3)]
for rid, seq in groups.items():
seq = sorted(seq, key=lambda x: x[0])
for i in range(1, len(seq)):
a = seq[i-1][1]; b = seq[i][1]
ia = idx[a]; ib = idx[b]
mat[ia][ib] += 1
out = []
for i,a in enumerate(states):
for j,b in enumerate(states):
out.append({"from": a, "to": b, "count": mat[i][j]})
return out


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out-prefix", required=True)
ap.add_argument("--id-col", default="")
ap.add_argument("--time-col", default="")
args = ap.parse_args()


rows = read_rows(args.inp)


# Falls K nicht existiert, setze K=B
for r in rows:
if (r.get("K") or "") == "":
r["K"] = r.get("B", "")


# Outputs
write_rows(f"{args.out_prefix}_zone_distribution.csv", ["zone","count","pct"], zone_distribution(rows))
write_rows(f"{args.out_prefix}_K_hist_overall.csv", ["bin","bin_lo","bin_hi","count"], k_hist(rows))
write_rows(f"{args.out_prefix}_K_stats_by_zone.csv", ["zone","min","p10","median","mean","p90","max","count"], k_stats_by_zone(rows))
# by-zone histogramm
hz_rows = []
for z in ["fragmentiert","regulativ","kohärent"]:
for binrow in k_hist(rows, zone=z):
hz_rows.append({"zone": z, **binrow})
write_rows(f"{args.out_prefix}_K_hist_by_zone.csv", ["zone","bin","bin_lo","bin_hi","count"], hz_rows)


# transition matrix (optional)
tm = transition_matrix(rows, args.id_col, args.time_col)
if tm:
write_rows(f"{args.out_prefix}_transition_matrix.csv", ["from","to","count"], tm)


write_rows(f"{args.out_prefix}_coherence_index.csv", ["coherence_index"], coherence_index(rows))


if __name__ == "__main__":
main()