#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Editiert tsm_symbolic_bridge_v0.1.json:
- list                       → zeigt aktuelle Zuordnung
- set --zone Z --facet F --orientation {+1,-1}
- import_csv path.csv        → Spalten: zone,pg_facet,orientation
"""
from pathlib import Path
import json, argparse, csv

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_symbolic_bridge_v0.1.json"

def load():
    return json.loads(J.read_text(encoding="utf-8"))

def save(d):
    J.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] wrote:", J)

def norm_orient(v):
    if v is None or v=="":
        return None
    s=str(v).strip().replace("±","").replace("–","-")
    if s in {"+","+1","1"}: return +1
    if s in {"-","-1"}:     return -1
    raise ValueError(f"orientation muss +1/-1 sein, bekam: {v}")

def set_one(d, zone, facet, orient):
    zs = d.get("zones", [])
    by_id = {z["id"]: z for z in zs}
    if zone not in by_id:
        raise SystemExit(f"[err] zone nicht gefunden: {zone}")
    z = by_id[zone]
    if facet is not None: z["pg_facet"] = facet
    if orient is not None: z["orientation"] = orient
    return d

def cmd_list(args):
    d = load()
    for z in d.get("zones", []):
        print(f"{z['id']}\tpg_facet={z.get('pg_facet')}\torientation={z.get('orientation')}")

def cmd_set(args):
    d = load()
    orient = norm_orient(args.orientation) if args.orientation is not None else None
    d = set_one(d, args.zone, args.facet, orient)
    save(d)

def cmd_import_csv(args):
    d = load()
    with open(args.import_csv, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            zone = row.get("zone")
            facet = row.get("pg_facet")
            orient = norm_orient(row.get("orientation"))
            d = set_one(d, zone, facet, orient)
    save(d)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap_list = sub.add_parser("list")
    ap_list.set_defaults(func=cmd_list)

    ap_set = sub.add_parser("set")
    ap_set.add_argument("--zone", required=True)
    ap_set.add_argument("--facet", required=False)
    ap_set.add_argument("--orientation", required=False)
    ap_set.set_defaults(func=cmd_set)

    ap_imp = sub.add_parser("import_csv")
    ap_imp.add_argument("import_csv")
    ap_imp.set_defaults(func=cmd_import_csv)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
