#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG Orientation Tuner:
- liest: tsm-online-bundle_v1.25.json (Fallback: v1.24/v1.23/latest), tsm_symbolic_bridge_v0.1.json
- sucht ±1-Orientierungen der vorhandenen PG-Facetten, die Kosinus(r3 vs r★) maximieren
  (Fallback: r3 vs b, wenn r★ fehlt)
- schreibt eine Vorschlagsdatei: tsm_symbolic_bridge_v0.1.suggested.json
- erzeugt Vergleichsreport: pg_orientation_tuner_report.md
- aktualisiert Overlay-Dateien für die vorgeschlagene Orientierung: pg_overlay.csv/signed.csv/summary.md/png
"""
from pathlib import Path
import json, itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BR = Path(__file__).resolve().parents[1]/"bridge"
BUNDLE_CAND = [
    BR/"tsm-online-bundle_v1.25.json",
    BR/"tsm-online-bundle_v1.24.json",
    BR/"tsm-online-bundle_v1.23.json",
    BR/"tsm-online-bundle_latest.json",
]
SBR = BR/"tsm_symbolic_bridge_v0.1.json"

def pick_bundle():
    for p in BUNDLE_CAND:
        if p.exists(): return p
    raise SystemExit("[err] Kein Bundle gefunden.")

def safe(v): return [float(x) if x is not None else 0.0 for x in v]

def cosine(a, b):
    a=np.array(a,float); b=np.array(b,float)
    if not np.any(np.isfinite(a)) or not np.any(np.isfinite(b)): return float("nan")
    a=np.nan_to_num(a); b=np.nan_to_num(b)
    na=np.linalg.norm(a); nb=np.linalg.norm(b)
    if na==0 or nb==0: return float("nan")
    return float(np.dot(a,b)/(na*nb))

def norm1(v):
    s=sum(abs(x) for x in v)
    return [x/s if s>0 else x for x in v]

def overlay(names, vec, zones, facets, orient, signed=False):
    acc={f:0.0 for f in facets}
    for z, val in zip(names, vec):
        pg = zones[z]["pg_facet"]
        if pg not in acc: continue
        s = zones[z].get("orientation", +1)
        s = orient.get(pg, s)
        acc[pg] += (s*val) if signed else val
    return [acc[f] for f in facets]

def main():
    B = pick_bundle()
    d = json.loads(B.read_text(encoding="utf-8"))
    bridge=json.loads(SBR.read_text(encoding="utf-8"))

    names=list(map(str,d["names"]))
    b = safe(d["b"]); r = safe(d["r"]); r3 = safe(d.get("r3") or [])
    rS = d.get("r_star"); rS = safe(rS) if rS else None

    # Zonen -> Facet; Facet-Liste
    zones={z["id"]: {"pg_facet": z.get("pg_facet"), "orientation": z.get("orientation", +1)}
           for z in bridge.get("zones",[])}
    facets=[z.get("pg_facet") for z in bridge.get("zones",[]) if z.get("pg_facet")]
    facets=sorted(set(facets))
    if not facets: raise SystemExit("[err] Keine PG-Facetten in der Bridge gefunden.")

    # Zielvektor (unsigned, normiert)
    target = norm1(overlay(names, rS if rS else b, zones, facets, orient={}, signed=False))

    # Baseline-Orientierungen aus Bridge
    base_orient={f: +1 for f in facets}
    for z in bridge.get("zones",[]):
        f=z.get("pg_facet")
        if f: base_orient[f]=z.get("orientation", +1)

    # Suche: alle ±1-Kombinationen
    best=(None, -1.0, None)  # (orient_map, cosine, vector)
    for signs in itertools.product([-1,1], repeat=len(facets)):
        cand_orient={f:s for f,s in zip(facets, signs)}
        vec = norm1(overlay(names, r3, zones, facets, orient=cand_orient, signed=False))
        c = cosine(vec, target)
        if c>best[1]:
            best=(cand_orient, c, vec)

    # Berichte
    base_vec = norm1(overlay(names, r3, zones, facets, orient=base_orient, signed=False))
    base_cos = cosine(base_vec, target)

    lines=[
        "# PG Orientation Tuner — Report",
        f"- bundle: `{B.name}`",
        f"- facets: {facets}",
        "",
        f"Baseline cosine(r³, target) = {base_cos:.6f} (target = r★{'/' if rS else '/'}b)",
        f"Best     cosine(r³, target) = {best[1]:.6f}",
        "",
        "## Suggested orientation per facet (old → new)",
    ]
    for f in facets:
        lines.append(f"- {f}: {base_orient[f]:+d} → {best[0][f]:+d}")
    (BR/"pg_orientation_tuner_report.md").write_text("\n".join(lines), encoding="utf-8")

    # Vorschlag in Bridge schreiben (separate Datei)
    bridge2 = json.loads(SBR.read_text(encoding="utf-8"))
    for z in bridge2.get("zones",[]):
        f=z.get("pg_facet")
        if f in best[0]:
            z["orientation"]=int(best[0][f])
    (BR/"tsm_symbolic_bridge_v0.1.suggested.json").write_text(
        json.dumps(bridge2, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Overlay mit vorgeschlagenen Orientierungen neu berechnen
    zones2={z["id"]: {"pg_facet": z.get("pg_facet"), "orientation": z.get("orientation", +1)}
            for z in bridge2.get("zones",[])}
    def ov(vec, signed=False, orient_map=None, zones_map=None):
        return overlay(names, vec, zones_map or zones2, facets, orient=orient_map or {}, signed=signed)

    O_b = norm1(ov(b, signed=False))
    O_r = norm1(ov(r, signed=False))
    O_rS= norm1(ov(rS, signed=False)) if rS else None
    O_r3= norm1(ov(r3, signed=False))

    import pandas as pd, numpy as np, matplotlib.pyplot as plt
    df = pd.DataFrame({"pg_facet": facets, "b":O_b, "r":O_r, **({"r_star":O_rS} if O_rS else {}), "r3":O_r3})
    df.to_csv(BR/"pg_overlay.csv", index=False)

    fig, ax = plt.subplots(figsize=(8,4.5), dpi=160)
    X=np.arange(len(facets)); W=0.22
    ax.bar(X-1.5*W, O_b,  width=W, label="b")
    ax.bar(X-0.5*W, O_r,  width=W, label="r")
    if O_rS is not None: ax.bar(X+0.5*W, O_rS, width=W, label="r★")
    ax.bar(X+1.5*W, O_r3, width=W, label="r³")
    ax.set_xticks(X); ax.set_xticklabels(facets, rotation=0)
    ax.set_ylim(0,1.0); ax.legend(ncol=4, frameon=False, fontsize=8, loc="upper center")
    ax.set_title("TSM → PG Overlay (with suggested orientations)")
    fig.tight_layout(); fig.savefig(BR/"pg_overlay.png")

    print("[ok] wrote:", BR/"pg_orientation_tuner_report.md", BR/"tsm_symbolic_bridge_v0.1.suggested.json", BR/"pg_overlay.csv", BR/"pg_overlay.png")

if __name__ == "__main__":
    main()
