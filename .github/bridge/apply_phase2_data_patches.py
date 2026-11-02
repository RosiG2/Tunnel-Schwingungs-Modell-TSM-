#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Phase 2 data patches:
- Append rows to RGN_state_v0.2.csv (core min and 'nan' UB)
- Ensure top-level key in RGN_qc_metrics_v0.1.json: min_share_per_zone=0.02
Creates backups: *.bak
Idempotent: skips duplicate rows / preserves existing JSON keys.
"""
import csv, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "RGN_state_v0.2.csv"
QC    = ROOT / "RGN_qc_metrics_v0.1.json"

state_rows = [
    # (zone, group, min, ub)
    ("kohärent", "core", "0.45", ""),
    ("regulativ", "core", "", ""),
    ("nan",       "",     "",    "0.40"),
]

def ensure_state():
    if not STATE.exists():
        # create new with header
        backup = None
        with STATE.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["zone","group","min","ub"])
            for r in state_rows:
                w.writerow(r)
        print(f"[ok] created {STATE} with header and Phase-2 rows")
        return

    # backup
    STATE.with_suffix(STATE.suffix + ".bak").write_bytes(STATE.read_bytes())

    # read existing
    with STATE.open("r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    # detect header
    has_header = lines and lines[0].lower().replace(" ", "") == "zone,group,min,ub"
    existing = set()
    start_idx = 1 if has_header else 0
    for line in lines[start_idx:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:  # skip malformed
            continue
        existing.add(tuple(parts[:4]))

    # append missing rows
    appended = 0
    with STATE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in state_rows:
            if r not in existing:
                w.writerow(r)
                appended += 1
    print(f"[ok] patched {STATE} (appended {appended} new row(s))")

def ensure_qc():
    data = {}
    if QC.exists():
        # backup
        QC.with_suffix(QC.suffix + ".bak").write_bytes(QC.read_bytes())
        try:
            data = json.loads(QC.read_text(encoding="utf-8"))
        except Exception:
            print("[warn] existing QC not valid JSON; starting fresh {}")
            data = {}

    # set / keep min_share_per_zone
    if "min_share_per_zone" not in data or data["min_share_per_zone"] != 0.02:
        data["min_share_per_zone"] = 0.02

    QC.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] ensured top-level key in {QC}: min_share_per_zone=0.02")

if __name__ == "__main__":
    ensure_state()
    ensure_qc()
