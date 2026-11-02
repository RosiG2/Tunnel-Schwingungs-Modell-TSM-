#!/usr/bin/env python3
c = Counter(zones)
n = len(zones)
return {k: {"count": c.get(k,0), "pct": (c.get(k,0)/n if n else 0.0)} for k in ["fragmentiert","regulativ","kohärent"]}


# --- Main ---


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out-json", required=True)
ap.add_argument("--out-csv", required=True)
ap.add_argument("--eps-deg", type=float, default=1.0)
ap.add_argument("--d-eps", type=float, default=0.5)
ap.add_argument("--cap-quantile", type=float, default=0.99)
ap.add_argument("--d-cap", type=float, default=0.01)
ap.add_argument("--B-lo", type=float, default=0.2)
ap.add_argument("--B-hi", type=float, default=0.8)
ap.add_argument("--d-B", type=float, default=0.05)
args = ap.parse_args()


# Eingabe lesen
with open(args.inp, newline="") as f:
r = csv.DictReader(f)
rows = [row for row in r]


# Baseline-Zonen aus Datei
baseline_zones = [ (row.get("zone") or "").strip() for row in rows ]
baseline_dist = zone_dist(baseline_zones)


# Parameterraster
eps_vals = [args.eps_deg - args.d_eps, args.eps_deg, args.eps_deg + args.d_eps]
cap_vals = [max(0.5, args.cap_quantile - args.d_cap), args.cap_quantile, min(0.9999, args.cap_quantile + args.d_cap)]
Blo_vals = [max(0.0, args.B_lo - args.d_B), args.B_lo, min(1.0, args.B_lo + args.d_B)]
Bhi_vals = [max(0.0, args.B_hi - args.d_B), args.B_hi, min(1.0, args.B_hi + args.d_B)]


# Ergebnisse sammeln
rows_detail = []
stability_hits = 0
total_cases = 0


# Für Stabilität je Zeile mitzählen
per_row_hits = [0]*len(rows)
combos = []
for e in eps_vals:
for cq in cap_vals:
for blo in Blo_vals:
for bhi in Bhi_vals:
if blo > bhi: # überspringen inkonsistenter Schwellen
continue
combos.append((e,cq,blo,bhi))
zones = recompute(rows, e, cq, blo, bhi)
# Vergleich
eq_flags = [int(z1==z2) for z1,z2 in zip(zones, baseline_zones)]
for i,fl in enumerate(eq_flags):
per_row_hits[i] += fl
total_cases += 1
# Verteilung dieser Kombi
dist = zone_dist(zones)
# Aggregiert: Übereinstimmung (%)
match_pct = sum(eq_flags)/len(eq_flags) if eq_flags else 0.0
rows_detail.append({
"eps_deg": e,
"cap_quantile": cq,
"B_lo": blo,
"B_hi": bhi,
"match_pct": round(match_pct,6),
**{f"{k}_pct": round(dist[k]["pct"],6) for k in ["fragmentiert","regulativ","kohärent"]},
**{f"{k}_count": dist[k]["count"] for k in ["fragmentiert","regulativ","kohärent"]}
})
# Zeilenstabilität
row_stability = [ (h/total_cases if total_cases else 0.0) for h in per_row_hits ]
avg_row_stability = sum(row_stability)/len(row_stability) if row_stability else 0.0


report = {
"input": args.inp,
"baseline_distribution": baseline_dist,
"tested_combinations": len(rows_detail),
"average_row_stability": avg_row_stability
}


# JSON schreiben
with open(args.out_json, "w") as f:
json.dump(report, f, indent=2, ensure_ascii=False)


# CSV schreiben
out_fields = ["eps_deg","cap_quantile","B_lo","B_hi","match_pct",
"fragmentiert_pct","regulativ_pct","kohärent_pct",
"fragmentiert_count","regulativ_count","kohärent_count"]
with open(args.out_csv, "w", newline="") as f:
w = csv.DictWriter(f, fieldnames=out_fields)
w.writeheader()
for row in rows_detail:
w.writerow(row)


if __name__ == "__main__":
main()