"""
TSM ↔ Positive Geometry Bridge (v0.1)
- Lädt Rohdaten aus Online‑Manifest (local path or dict)
- Normalisiert Baseline/Recommended auf Simplex
- Leitet Simplex/Polytop‑Facetten ab (Positivität, Summe=1, optionale Nebenbedingungen)
- Gibt symbolische dlog‑Kanonische‑Form-Komponenten und einen Mini‑Report aus
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional


import pandas as pd
import numpy as np


# ---------- Manifest ----------


def load_manifest(manifest: str | Dict[str, Any]) -> Dict[str, Any]:
if isinstance(manifest, str):
if manifest.strip().startswith("{"):
return json.loads(manifest)
with open(manifest, "r", encoding="utf-8") as f:
return json.load(f)
return manifest


# ---------- IO helpers ----------


def read_csv_url(url: str) -> pd.DataFrame:
return pd.read_csv(url)




def read_json_url(url: str) -> Any:
return json.loads(pd.read_json(url, typ="series").to_json())


# ---------- Core ----------


@dataclass
class ZoneVector:
names: List[str]
values: np.ndarray # shape (n,)


def normalize_simplex(self) -> "ZoneVector":
v = np.asarray(self.values, dtype=float)
total = v.sum()
if total <= 0:
raise ValueError("Summe der Zonenwerte ist nicht > 0")
return ZoneVector(self.names, v / total)




def load_zone_vector(url: str) -> ZoneVector:
df = read_csv_url(url)
# erwartet Spalten: zone, value
zone = df.iloc[:, 0].astype(str).tolist()
val = df.iloc[:, 1].astype(float).values
if (val < 0).any():
raise ValueError("Negative Werte in Zonenvektor gefunden (Positivitätsannahme verletzt).")
return ZoneVector(zone, val)




def align_vectors(b: ZoneVector, r: ZoneVector) -> Tuple[ZoneVector, ZoneVector]:
# Vereinige auf gemeinsame Zonenreihenfolge (nach Namen)
names = sorted(set(b.names) | set(r.names))
name_to_idx_b = {n: i for i, n in enumerate(b.names)}
name_to_idx_r = {n: i for i, n in enumerate(r.names)}
vb = np.array([b.values[name_to_idx_b.get(n, -1)] if n in name_to_idx_b else 0.0 for n in names])
vr = np.array([r.values[name_to_idx_r.get(n, -1)] if n in name_to_idx_r else 0.0 for n in names])
return ZoneVector(names, vb), ZoneVector(names, vr)




def facet_system(n: int, enforce_sum_one: bool = True) -> Dict[str, Any]:
# H‑Darstellung: x_i >= 0, und optional sum x_i = 1
A = []
b = []
for i in range(n):
ai = np.zeros(n)
ai[i] = -1 # -x_i <= 0 (entspricht x_i >= 0)
A.append(ai)
b.append(0.0)
eq = None
if enforce_sum_one:
eq = {"a": np.ones(n).tolist(), "c": 1.0} # a^T x = c
return {"A": np.vstack(A).tolist(), "b": np.array(b).tolist(), "eq": eq}




def dlog_symbolic(names: List[str], include_sum_constraint: bool = True) -> List[str]:
# symbolische dlog‑Bausteine für Simplex‑artige Struktur
terms = [f"d log({n})" for n in names]
if include_sum_constraint:
terms.append("d log(Σ x_i)")
return terms




def segment_analysis(b: ZoneVector, r: ZoneVector) -> pd.DataFrame:
# einfacher Pfad b→r im Simplex: Differenzen, relative Änderungen, Ranglisten
delta = r.values - b.values
with np.errstate(divide='ignore', invalid='ignore'):
rel = np.where(b.values > 0, delta / b.values, np.nan)
df = pd.DataFrame({
"zone": b.names,
"b": b.values,
"r": r.values,
"delta": delta,
"rel_change": rel
})
df["rank_abs"] = df["delta"].abs().rank(ascending=False, method="min")
df["rank_rel"] = df["rel_change"].abs().rank(ascending=False, method="min")
df.sort_values(["rank_abs", "rank_rel", "zone"], inplace=True)
return df




def build_report_md(df_changes: pd.DataFrame, dlog_terms: List[str]) -> str:
lines = ["# TSM ↔ Positive Geometry – Mini‑Report",
"",
"## dlog‑Kanonische‑Form (symbolische Bausteine)",
"- " + ", ".join(dlog_terms),
"",
"## Größte Änderungen (b → r)"]
top = df_changes.head(15)
for _, row in top.iterrows():
lines.append(f"- {row['zone']}: Δ={row['delta']:.6f} | rel={row['rel_change']:.3f} | b={row['b']:.6f} → r={row['r']:.6f}")
return "\n".join(lines)


# ---------- Runner ----------


def run_from_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
ds = manifest["datasets"]
b = load_zone_vector(ds["zonen_baseline"]["url"]).normalize_simplex()
r = load_zone_vector(ds["zonen_recommended"]["url"]).normalize_simplex()
b, r = align_vectors(b, r)
b = b.normalize_simplex()
r = r.normalize_simplex()


facets = facet_system(len(b.names), enforce_sum_one=True)
dlog_terms = dlog_symbolic(b.names, include_sum_constraint=True)
changes = segment_analysis(b, r)
report_md = build_report_md(changes, dlog_terms)


return {
"names": b.names,
"b": b.values.tolist(),
"r": r.values.tolist(),
"facets": facets,
"dlog_terms": dlog_terms,
"changes": changes.to_dict(orient="records"),
"report_md": report_md
}


if __name__ == "__main__":
import argparse
p = argparse.ArgumentParser()
p.add_argument("--manifest", type=str, required=True, help="Pfad zu JSON oder JSON‑String")
p.add_argument("--out", type=str, default="bridge_report.md")
args = p.parse_args()


man = load_manifest(args.manifest)
out = run_from_manifest(man)
with open(args.out, "w", encoding="utf-8") as f:
f.write(out["report_md"])
print(f"Report geschrieben: {args.out}")