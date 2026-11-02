#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ONE-PAGER (TSM ↔ Positive Geometry)
Erzeugt: bridge/ONEPAGER_TSM_PG_v1.md
Inhalte:
- Version & Zeitstempel (Bundle)
- Fixe Caps (tau, core_UB, core-Mitglieder) aus meta.notes
- Kurz-Executive (Auszug), Keypoints (Auszug)
- PG-Overlay-Metriken (Kosinus/L1)
- PG-Crosswalk (Tabelle)
- Abbildungen: bridge_viz_b_r_rstar_r3.png, pg_overlay.png
"""
from pathlib import Path
import json, re, csv, time

BR = Path(__file__).resolve().parents[1] / "bridge"
BUNDLES = [
    BR/"tsm-online-bundle_v1.25.json",
    BR/"tsm-online-bundle_v1.24.json",
    BR/"tsm-online-bundle_v1.23.json",
    BR/"tsm-online-bundle_latest.json",
]
TSM_JSON = BR/"tsm_pg_facets_lifted.json"
EXEC = BR/"README_exec_summary_phase3_star.md"
KEYS = BR/"KEYPOINTS_phase3.md"
OVER = BR/"pg_overlay_summary.md"
XW   = BR/"pg_crosswalk.csv"
VIZ1 = "bridge_viz_b_r_rstar_r3.png"
VIZ2 = "pg_overlay.png"
OUT  = BR/"ONEPAGER_TSM_PG_v1.md"

def pick_bundle():
    for p in BUNDLES:
        if p.exists(): return p
    raise SystemExit("[err] Kein Online-Bundle gefunden.")

def read_head(p: Path, lines=40):
    if not p.exists(): return "_(Datei nicht gefunden)_"
    txt = p.read_text(encoding="utf-8").strip().splitlines()
    return "\n".join(txt[:lines]).strip()

def parse_caps(d):
    tau = None; core_ub = None; core = None
    notes = (d.get("meta", {}) or {}).get("notes", []) or []
    # Suche nach "Phase 5 applied: core_UB=0.60, tau=0.11, core=['kohärent', 'regulativ']"
    for n in notes[::-1]:
        m = re.search(r"core_UB\s*=\s*([0-9.]+).*?tau\s*=\s*([0-9.]+).*?core\s*=\s*\[([^\]]+)\]", str(n))
        if m:
            core_ub = float(m.group(1))
            tau = float(m.group(2))
            core = [c.strip(" '\"") for c in m.group(3).split(",")]
            break
    # Fallback: aus Lifts
    if core_ub is None:
        for L in (d.get("constraints", {}) or {}).get("lifts", []) or []:
            if (L.get("meta", {}) or {}).get("key","").endswith("group_core_ub") and L.get("c") is not None:
                try: core_ub = float(L["c"])
                except: pass
    return tau, core_ub, core

def parse_overlay_metrics(txt):
    # liest L1/Kosinus-Blöcke aus pg_overlay_summary.md
    L1_r3_rS = Kos_r3_rS = None
    L1_r3_b  = Kos_r3_b  = None
    for line in txt.splitlines():
        if "r³ vs r★" in line: mode="rs"
        elif "r³ vs b" in line: mode="rb"
        elif "L1-Delta:" in line:
            val = float(line.split(":")[1].strip())
            if locals().get("mode") == "rs": L1_r3_rS = val
            else: L1_r3_b = val
        elif "Kosinus:" in line:
            val = float(line.split(":")[1].strip())
            if locals().get("mode") == "rs": Kos_r3_rS = val
            else: Kos_r3_b = val
    return L1_r3_rS, Kos_r3_rS, L1_r3_b, Kos_r3_b

def build_crosswalk_table(path: Path):
    if not path.exists(): return "_(pg_crosswalk.csv nicht gefunden)_"
    rows = list(csv.DictReader(open(path, newline='', encoding='utf-8')))
    lines = ["| Zone | PG-Facet | Orientation |", "|---|---|---|"]
    for r in rows:
        o = r.get("orientation", "")
        if str(o) in ("1","+1"): o = "+1"
        elif str(o) in ("-1","-"): o = "-1"
        lines.append(f"| {r.get('zone','')} | {r.get('pg_facet','')} | {o} |")
    return "\n".join(lines)

def main():
    B = pick_bundle()
    bundle = json.loads(B.read_text(encoding="utf-8"))
    tsm = json.loads(TSM_JSON.read_text(encoding="utf-8"))

    version = bundle.get("version","?")
    ts = bundle.get("timestamp", int(time.time()))
    ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

    tau, core_ub, core = parse_caps(tsm)
    exec_md = read_head(EXEC, 40)
    keys_md = read_head(KEYS, 40)
    overlay_txt = read_head(OVER, 60)
    L1_r3_rS, Kos_r3_rS, L1_r3_b, Kos_r3_b = parse_overlay_metrics(overlay_txt)
    xw_tbl = build_crosswalk_table(XW)

    lines = []
    lines += [f"# TSM ↔ Positive Geometry — One-Pager",
              "",
              f"**Bundle:** `{B.name}` (version **{version}**, {ts_str})",
              f"**Caps:** τ = **{tau:.2f}**  ·  core_UB = **{core_ub:.2f}**  ·  core = **{', '.join(core or [])}**" if (tau and core_ub and core) else "_Caps: (nicht bestimmt)_",
              "",
              "## Executive Summary (Auszug)",
              exec_md, "",
              "## Keypoints (Auszug)",
              keys_md, "",
              "## PG-Overlay — Metriken",
              f"- r³ vs r★:   L1 = **{L1_r3_rS:.6f}**,  Kosinus = **{Kos_r3_rS:.6f}**" if L1_r3_rS is not None else "- r★ nicht verfügbar.",
              f"- r³ vs b:    L1 = **{L1_r3_b:.6f}**,  Kosinus = **{Kos_r3_b:.6f}**", "",
              "## PG-Crosswalk (TSM → PG)",
              xw_tbl, "",
              "## Abbildungen",
              f"![b/r/r★/r³ (Zonen)]({VIZ1})",
              f"![PG-Overlay (Facetten)]({VIZ2})",
              "",
              "## Artefakte (Repo-Pfade)",
              "- `bridge/tsm-online-bundle_v1.25.json` (inkl. Brücke)",
              "- `bridge/tsm_symbolic_bridge_v0.1.json`, `bridge/pg_crosswalk.csv`",
              "- `bridge/pg_overlay*.{csv,md,png}`",
              "- `bridge/README_exec_summary_phase3_star.md`, `bridge/KEYPOINTS_phase3.md`",
              ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("[ok] wrote:", OUT)

if __name__ == "__main__":
    main()
