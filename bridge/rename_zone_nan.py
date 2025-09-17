# bridge/rename_zone_nan.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, pandas as pd
from pathlib import Path
BR=Path(__file__).resolve().parents[1]/"bridge"
OLD, NEW = "nan", "hyperresonant"

# 1) Haupt-JSON
J=BR/"tsm_pg_facets_lifted.json"
d=json.loads(J.read_text(encoding="utf-8"))
d["names"]=[NEW if str(n)==OLD else n for n in d["names"]]
J.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

# 2) CSVs mit Zonen-Spalte
for fn in ["tsm_pg_changes.csv","tsm_pg_r_projected.csv","tsm_pg_r_projected_p3.csv",
           "tsm_pg_bindings_phase2_star.csv","tsm_pg_bindings_phase3_star.csv"]:
    p=BR/fn
    if p.exists():
        df=pd.read_csv(p)
        if "zone" in df.columns:
            df["zone"]=df["zone"].replace({OLD:NEW})
            df.to_csv(p,index=False)
print("[ok] renamed", OLD, "->", NEW)
