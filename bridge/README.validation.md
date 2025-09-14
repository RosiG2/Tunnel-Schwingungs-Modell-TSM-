# Validation & CI für die TSM↔GR‑Bridge (v0.1)


Dieses Pack liefert:
- `tsm_bridge_validation_v0.1.py` — Validiert `computed.csv` (Spalten, Wertebereiche, Zonenkohärenz) und erzeugt einen JSON‑Report.
- `tsm_bridge_output_schema_v1.json` — CSV‑Schemaspezifikation für `computed.csv`.
- Erwartete Referenz‑Outputs für den Mini‑Datensatz (`expected_*.csv`).
- GitHub‑Actions Workflow (`.github/workflows/tsm-bridge-ci.yml`) — führt Compute → Export → Validation automatisch aus.


## Schnellstart lokal