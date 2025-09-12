#!/usr/bin/env python3
"""
TSM–GR v0.2 – Analyze & Report
--------------------------------
Liest `sweep_summary.csv` (oder mehrere) ein und erzeugt:
• `report.json` – Kennzahlen + Top-Rankings je Metrik
• `REPORT.md` – kompakte Markdown-Zusammenfassung
• (optional) PNG-Plots, falls matplotlib verfügbar ist (Histogramme/Scatter)


Nutzung:
python analyze_tsmgr_v02.py --root ./out_sweeps --out ./reports


Sucht rekursiv nach Dateien namens `sweep_summary.csv` unter `--root`.
Ohne matplotlib laufen alle Schritte außer den PNG-Plots.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import csv, json, math
from pathlib import Path


# -----------------------------
# Utils
# -----------------------------


def try_import_matplotlib():
try:
import matplotlib.pyplot as plt # noqa
return True
except Exception:
return False




def read_summaries(root: Path) -> List[Path]:
return list(root.rglob('sweep_summary.csv'))




def load_summary(path: Path) -> List[Dict[str, Any]]:
rows: List[Dict[str, Any]] = []
with open(path, 'r', newline='') as f:
r = csv.DictReader(f)
for row in r:
# cast numerics where possible
for k in list(row.keys()):
if k in {"case"}:
try: row[k] = int(row[k])
except: pass
else:
try: row[k] = float(row[k]) if row[k] != '' else None
except: pass
rows.append(row)
return rows




def rank(rows: List[Dict[str, Any]], key: str, reverse: bool) -> List[Dict[str, Any]]:
valid = [r for r in rows if r.get(key) is not None]
return sorted(valid, key=lambda r: r.get(key, float('nan')), reverse=reverse)




def basic_stats(vals: List[float]) -> Dict[str, float]:
if not vals:
return {"n": 0}
import statistics as st
return {
"n": len(vals),
"mean": st.mean(vals),
"median": st.median(vals),
"min": min(vals),
"max": max(vals),
"stdev": st.pstdev(vals) if len(vals) > 1 else 0.0,
}


# -----------------------------
# Report builder
# -----------------------------


def build_report(all_rows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
metrics = ["tt_null", "pct_F+", "pct_F", "transitions", "eps_increase_steps"]
maximize = {"pct_F+", "pct_F"}
minimize = {"tt_null", "transitions", "eps_increase_steps"}


report: Dict[str, Any] = {"sweeps": {}, "meta": {"metrics": metrics}}


for sweep_name, rows in all_rows.items():
sweep_rep: Dict[str, Any] = {"stats": {}, "top": {}}
for m in metrics:
vals = [r[m] for r in rows if r.get(m) is not None]
sweep_rep["stats"][m] = basic_stats(vals)
if m in maximize:
top = rank(rows, m, reverse=True)[:5]
else:
top = rank(rows, m, reverse=False)[:5]
sweep_rep["top"][m] = top
report["sweeps"][sweep_name] = sweep_rep


return report




def write_md(report: Dict[str, Any], out_md: Path) -> None:
lines: List[str] = []
lines.append("# TSM–GR v0.2 – Sweep Report\n")
for name, rep in report.get("sweeps", {}).items():
lines.append(f"\n## {name}\n")
lines.append("\n### Statistiken (Kurz)\n")
lines.append("\nMetrik | n | mean | median | min | max | stdev\n---|---:|---:|---:|---:|---:|---:\n")
for m, st in rep["stats"].items():
if st.get("n", 0) == 0:
lines.append(f"{m} | 0 | | | | | \n")
else:
lines.append(f"{m} | {int(st['n'])} | {st['mean']:.4g} | {st['median']:.4g} | {st['min']:.4g} | {st['max']:.4g} | {st['stdev']:.4g}\n")
lines.append("\n### Top‑Konfigurationen je Metrik (Top‑5)\n")
for m, tops in rep["top"].items():
lines.append(f"\n**{m}**\n\n")
if not tops:
lines.append("(keine gültigen Einträge)\n")
continue
# Spalten dynamisch aus erster Zeile
cols = [k for k in tops[0].keys() if k not in {"case"}]
header = "case | " + " | ".join(cols)
sep = "---:|" + "|".join(["---:" for _ in cols])
lines.append(header + "\n")
lines.append(sep + "\n")
for r in tops:
row = f"{int(r['case'])} | " + " | ".join([f"{r[c]}" for c in cols])
lines.append(row + "\n")
out_md.write_text("".join(lines), encoding="utf-8")



# -----------------------------
# Plotting (optional)
# -----------------------------


def make_plots(all_rows: Dict[str, List[Dict[str, Any]]], out_dir: Path) -> None:
if not try_import_matplotlib():
return
import matplotlib.pyplot as plt # type: ignore


for name, rows in all_rows.items():
K1 = [r["tt_null"] for r in rows if r["tt_null"] is not None]
K2 = [r["pct_F+"] for r in rows if r["pct_F+"] is not None]
K3 = [r["transitions"] for r in rows if r["transitions"] is not None]


# Histogramme
if K1:
plt.figure()
plt.hist(K1, bins=20)
plt.title(f"{name} – tt_null")
plt.xlabel("time to null-line (tau)")
plt.ylabel("count")
plt.tight_layout()
(out_dir / f"{name}_hist_tt_null.png").parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_dir / f"{name}_hist_tt_null.png")
plt.close()
if K2:
plt.figure()
plt.hist(K2, bins=20)
plt.title(f"{name} – pct_F+")
plt.xlabel("fraction of steps in F+")
plt.ylabel("count")
plt.tight_layout()
plt.savefig(out_dir / f"{name}_hist_pctFplus.png")
plt.close()
if K3:
plt.figure()
plt.hist(K3, bins=20)
plt.title(f"{name} – transitions")
plt.xlabel("zone transitions")
plt.ylabel("count")
plt.tight_layout()
plt.savefig(out_dir / f"{name}_hist_transitions.png")
plt.close()

# -----------------------------
# Main
# -----------------------------


def main():
import argparse
ap = argparse.ArgumentParser(description="Analyze sweep_summary.csv for TSM–GR v0.2")
ap.add_argument("--root", default="./out_sweeps", help="Wurzelverzeichnis mit sweep_summary.csv (rekursiv)")
ap.add_argument("--out", default="./reports", help="Ausgabeverzeichnis")
args = ap.parse_args()


root = Path(args.root)
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)


paths = read_summaries(root)
if not paths:
print(f"Keine sweep_summary.csv unter {root} gefunden.")
return


all_rows: Dict[str, List[Dict[str, Any]]] = {}
for p in paths:
name = p.parent.name
rows = load_summary(p)
all_rows[name] = rows


report = build_report(all_rows)


# JSON
with open(out / "report.json", "w", encoding="utf-8") as f:
json.dump(report, f, indent=2)


# Markdown
write_md(report, out / "REPORT.md")


# Plots (optional)
make_plots(all_rows, out)


print(f"Fertig. Berichte in {out}")


if __name__ == "__main__":
main()