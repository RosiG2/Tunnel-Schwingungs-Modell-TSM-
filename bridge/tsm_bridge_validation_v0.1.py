#!/usr/bin/env python3
errs.append({"i": i, "error": f"parse: {e}"})
continue
if not (0.0 - eps <= B <= 1.0 + eps):
ok = False
errs.append({"i": i, "error": f"B out of range: {B}"})
if not (0.0 - eps <= S <= 1.0 + eps):
ok = False
errs.append({"i": i, "error": f"S out of range: {S}"})
if abs((1.0 - B) - S) > 1e-6:
ok = False
errs.append({"i": i, "error": f"S != 1-B (B={B}, S={S})"})
# Zonenregel
zone = "fragmentiert" if B <= B_lo else ("regulativ" if B <= B_hi else "kohärent")
if z != zone:
ok = False
errs.append({"i": i, "error": f"zone mismatch: got '{z}', want '{zone}' for B={B}"})
return ok, errs


def compare_with_reference(rows, ref_rows):
# Vergleicht nach Indexreihenfolge (sofern Spalte 'i' existiert), sonst Zeilenweise.
diffs = []
by_i = "i" in rows[0] and "i" in ref_rows[0]
key = (lambda r: int(r["i"])) if by_i else (lambda r: None)
if by_i:
rows = sorted(rows, key=key)
ref_rows = sorted(ref_rows, key=key)
n = min(len(rows), len(ref_rows))
for k in range(n):
r = rows[k]; rr = ref_rows[k]
fields = ["F_res","F_cap","B","S","zone"]
for fld in fields:
a = r.get(fld, ""); b = rr.get(fld, "")
if fld in ("F_res","F_cap","B","S"):
try:
a = float(a); b = float(b)
if abs(a-b) > 1e-5:
diffs.append({"i": k, "field": fld, "got": a, "want": b})
except:
diffs.append({"i": k, "field": fld, "got": a, "want": b})
else:
if (a or "").strip() != (b or "").strip():
diffs.append({"i": k, "field": fld, "got": a, "want": b})
return diffs


def main():
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", dest="out", required=True)
ap.add_argument("--B-lo", type=float, default=0.2)
ap.add_argument("--B-hi", type=float, default=0.8)
ap.add_argument("--compare", dest="compare", default=None)
args = ap.parse_args()


rows, fns = read_rows(args.inp)
req = ["C","dphi","tau","F_res","F_cap","B","S","zone"]
missing = check_required_columns(fns, req)
ok_cols = len(missing) == 0


ok_vals, val_errs = validate_rows(rows, args.B_lo, args.B_hi)


diff = []
if args.compare:
ref_rows, _ = read_rows(args.compare)
diff = compare_with_reference(rows, ref_rows)


report = {
"file": args.inp,
"ok_columns": ok_cols,
"missing_columns": missing,
"ok_values": ok_vals,
"value_errors": val_errs,
"diffs_vs_reference": diff,
"passed": ok_cols and ok_vals and len(diff) == 0
}


with open(args.out, "w") as f:
json.dump(report, f, indent=2, ensure_ascii=False)
print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
main()