# Bridge README (TSM ↔ Positive Geometry)


## Nutzung
1) Stelle sicher, dass das **Online‑Manifest** aktuell ist (im Korpus oder lokal als Datei).
2) Lege `bridge/tsm_polytope.py` wie bereitgestellt ab.
3) Ausführen (Beispiel, Manifest als JSON‑String):
```bash
python bridge/tsm_polytope.py --manifest "$(cat tsm-online-bundle_v1.20.json)" --out bridge/bridge_report.md