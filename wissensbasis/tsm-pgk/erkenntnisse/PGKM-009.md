# PGKM-009 – Vorhersehbarkeit ohne Informationsleck

**Forschungsstatus:** `NONCANONICAL_RESEARCH_SYNTHESIS`
**Geltungsbereich:** 0.139–0.140; pre-rewrite vs transition-contemporaneous

## Forschungsfrage und Ausgangspunkt

Nach-Rewrite-Information darf einen vor-Rewrite-Regulationsanspruch nicht tragen.

## Definition und Prüfgegenstand

0.139–0.140; pre-rewrite vs transition-contemporaneous

## Gegenbefunde und Grenzen

- **PGKC-017 [OUTCOME_T__TEMPORAL_INFORMATION_BOUNDARY_FAIL]** PGK-0.139: R10c überschreitet die zeitliche Informationsgrenze, weil die REORDERING_CLASS erst nach dem Rewrite feststeht.
- **PGKC-018 [OUTCOME_P0]** PGK-0.140: vorab gesetzter normalisierter Gain >=0.10 scheitert in beiden Held-out-Blöcken.
- **Grenze zu PGKC-017:** Transition-contemporaneous Korrelation nicht als pre-rewrite Regulation ausweisen.
- **Grenze zu PGKC-018:** Positive kleinere Effekte nicht in den strikten PASS hochstufen.

## Ableitung und Interpretation

Die Beziehungen gelten entsprechend ihrem angegebenen Typ und Geltungsbereich.
**Prospektivitätsregel:** Ein vor dem Rewrite definierter Reporter `R_n` darf nur Informationen aus dem aktuellen zulässigen Zustand / der fixierten Aufgabe verwenden; sobald eine Klassifikation erst aus `S_(n+1)` oder dem Übergangsergebnis gewonnen wird, ist sie *transition-contemporaneous*, nicht prognostisch. Der originale 0.139-Entscheid qualifiziert die gefundene Grammatik deshalb `OUTCOME_T`. Der methodisch gehärtete Nachfolger 0.140 bestandenene Formal-Gates G1–G5 und kleine Primäreffekte genügen nicht für den vorab fixierten `Gain ≥ 0.10`, der in beiden Held-out-Stufen scheitert (`OUTCOME_P0`). Quellen: `SRC-018`, `SRC-019`.
- `E017` → `PGKC-018` **KORREKTURPFAD**: Prospektiver pre-rewrite Nachfolgetest adressiert Leakage, findet jedoch keinen replicated Additionality PASS. *(HISTORISCHE_ENTWICKLUNG)*
- `E029` → `PGKC-031` **KATEGORIENTRENNUNG**: Die formal getypte Grammatik kann Fehlerarten beschreiben, ersetzt aber keinen prospektiven R10c-Test. *(SYNTHETISCHE_VERBINDUNG)*
- `E018` → `PGKC-019` **FORSCHUNGSWECHSEL**: Nach PGK 0.140 folgt eine strengere Konfigurationsfrage; auch der 0.141 Null-Gate fällt negativ aus. *(HISTORISCHE_ENTWICKLUNG)*

## Fachliche Beziehungen

- [PGKM-015 – Geschichtete Funktionsgrammatik und TSM-Konkordanz](PGKM-015.md)
- [PGKM-010 – Konfigurationsprofil, FRE und Äquivalenz](PGKM-010.md)

## TSM-Anschluss

- **TSM-000:** Begrifflicher Anschluss (ohne eigenständigen empirischen Nachweis).

## Offene Gegenprüfungen

- Zuerst die jeweils ausgewiesenen historischen Geltungs- und Reproduktionsgrenzen schließen, bevor eine stärkere Wirkung behauptet wird.

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-017`** (NEGATIV; `OUTCOME_T__TEMPORAL_INFORMATION_BOUNDARY_FAIL`): PGK-0.139: R10c überschreitet die zeitliche Informationsgrenze, weil die REORDERING_CLASS erst nach dem Rewrite feststeht.
- **`PGKC-018`** (NEGATIV; `OUTCOME_P0`): PGK-0.140: vorab gesetzter normalisierter Gain >=0.10 scheitert in beiden Held-out-Blöcken.
- **`PGKC-277`** (NEGATIV; `HISTORICAL_DECISION_RECONFIRMED`): 0.139s Klassifikator REORDERING_CLASS verwendet das nachherige Rewrite-Ergebnis und verdient daher ausschließlich transition-contemporaneous Status.
- **`PGKC-278`** (GELTUNG; `HISTORICAL_DECISION_RECONFIRMED`): 0.140 meldet formal G1–G5 PASS, aber den vorab fixierten Gain >=0.10 in beiden Held-outs FAIL; diese beiden Aussagen sind kompatibel, kein R10c-Erfolg.
- **`PGKC-291`** (GELTUNGSGRENZE; `HISTORISCH_NEGATIV`): Der 0.139-Deskriptor REORDERING_CLASS ist post-rewrite und somit für die untersuchte Regel kein gültiger pre-rewrite-Selektor.
- **`PGKC-292`** (MATHEMATISCH_NEGATIVE_IMPLIKATION; `A6_4_EIGENE_FORMALPRUEFUNG`): Zwei Welten mit identischen pre-event-Informationen und unterschiedlichen post-event-Labels erlauben 2/2 retrospektive, aber maximal 1/2 deterministische prospektive Treffer.
- **`PGKC-294`** (EXPLORATIVE_LOGISCHE_MOEGLICHKEIT; `A6_4_EIGENE_DEMO_NICHT_NATIVE`): Ein erfolgreicher vorab sichtbarer Feedbackselektor kann in einer künstlichen endlichen E/C-Variante eine Zielgröße verbessern; dieser neue Selektor wäre für PGK ein eigener Fork.
- **`PGKC-295`** (GELTUNGSGRENZE; `A6_4_EIGENE_DEMO_NICHT_NATIVE`): Die künstliche E/C-Feedback-Demonstration hat einen Gesamteffekt, aber keine positive Verbesserung auf der separat ausgewerteten Teilmenge f<=2.
- **`PGKC-296`** (NEGATIV; `HISTORISCH_NEGATIV`): 0.140 und 0.141 bestehen im jeweiligen Originalvertrag nicht die vorab geforderte replizierte Additionality gegen geeignete Vergleichsmodelle.
- **`A6N-C008`** (offen; `status-offen`): Kein neues G6-PASS: externe H-Aufgabe, fehlender legaler Nicht-Rewrite-Baselinepfad und kein unabhaengiger Heldout-Nachweis.

## Quellenstatus

- `SRC-018`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-019`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-020`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-076`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-077`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0032](../forschung/B03.md#integration-find-0032)** · CSTOP-ACCESS-01 / PGK-ROOT-01 · `C→STOP / NATIVE_NO_PASSAGE; FORMAL_SPLIT_SEPARATE`
- **[INTEGRATION-FIND-0045](../forschung/B05.md#integration-find-0045)** · A6N-01 / prospektives G6 · `OPTIONSRUECKWIRKUNG / KEIN_NEUES_G6_PASS`
- **[INTEGRATION-FIND-0091](../forschung/B07.md#integration-find-0091)** · PGK-0.139 · `OUTCOME_T__TEMPORAL_INFORMATION_BOUNDARY_FAIL`
- **[INTEGRATION-FIND-0092](../forschung/B07.md#integration-find-0092)** · PGK-0.140 · `OUTCOME_P0 / R10c OPEN`
- **[INTEGRATION-FIND-0093](../forschung/B07.md#integration-find-0093)** · PGK-0.141 · `OUTCOME_C0__NO_CONFIGURATION_ADDITIONALITY`
