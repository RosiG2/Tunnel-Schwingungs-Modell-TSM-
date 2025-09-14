# TSM↔GR Bridge Pack v0.1


**Ziel:** Eine gemeinsame, reproduzierbare *Notation* für das Resonanzgesetz (TSM‑136D) in einer physik‑lesbaren Form.
Dieses Pack liefert Daten‑/Konfig‑Artefakte, die Du 1:1 in GitHub ablegen kannst. Ich kann sie danach direkt aus dem Netz nutzen.


**Bestandteile**
- `tsm_bridge_defaults_v1.json` — geprüfte Defaults (ε, Cap‑Quantil, B/S‑Schwellen).
- `tsm_bridge_schema_v1.json` — JSON‑Schema zur Validierung.
- `tsm_gr_minimalformalismus_v0.1.md` — 1‑Seiten‑Formalisierung (TSM‑Notation → gemeinsame Sprache).
- `tsm_bridge_examples.csv` — kleines, selbsterklärendes Beispiel‑CSV.
- `MANIFEST.bridge.v01.json` — Prüfsummen & vorgeschlagene Web‑Pfade.


**Upload‑Vorschlag**
1. Lege im Repo `Tunnel-Schwingungs-Modell-TSM-` einen Ordner `bridge/` an.
2. Kopiere alle Dateien aus diesem Pack dort hinein.
3. Optional (Corpus‑Slot bleibt bei 19/20): Ersetze in Deinem Korpus die defekte `TSM-136D_recommended v3.json` durch **`tsm_bridge_defaults_v1.json`** (gleiche Rolle, aber valide + präzise).


**Reproduzierbarkeit**
Die hier gesetzten Defaults reproduzieren auf dem mitgelieferten 100×100‑Datensatz die Zonenverteilung **20 % / 60 % / 20 %** (kohärent / regulativ / fragmentiert) mittels
`B = ECDF(F_cap)` und `S = 1−B` bei `cap_quantile = 0.99` und `ε = 1°`.