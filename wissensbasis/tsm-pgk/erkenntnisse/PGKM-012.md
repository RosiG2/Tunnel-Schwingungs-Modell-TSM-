# PGKM-012 – Root-Isolation und historischer Selektorfehler

**Forschungsstatus:** `NONCANONICAL_RESEARCH_SYNTHESIS`
**Geltungsbereich:** FSTT-01F; Archivfolge versus wirklich frühester Crossing

## Forschungsfrage und Ausgangspunkt

Ein dokumentierter Grid-Replay kann reproduzierbar und dennoch nicht earliest-event-vollständig sein.

## Definition und Prüfgegenstand

FSTT-01F; Archivfolge versus wirklich frühester Crossing

## Ergebnisse und Geltung

- **PGKC-025 [CONDITIONAL_OLD_STATE_ONLY]** Schritt 10 ist nur für den bedingten historischen Archivzustand zu bewerten; die earliest-korrigierte Folge läuft schon ab Schritt 6 anders. *[QUELLENAUDIT_BERICHT]*

## Gegenbefunde und Grenzen

- **PGKC-024 [EARLIEST_EVENT_FAIL_STEP6]** FSTT-01F fand bei archiviertem Schritt 6 von beiden historischen Rastern verpasste E-Crossing-Insel.
- **Grenze zu PGKC-024:** Archiveventfolge unter altem Raster ≠ earliest-root-vollständige Folge.
- **Grenze zu PGKC-025:** Kein Schritt10 auf korrigierter neuer Branch behaupten.

## Ableitung und Interpretation

Die Beziehungen gelten entsprechend ihrem angegebenen Typ und Geltungsbereich.
**Branch-kritischer Originalbefund:** `SRC-024` meldet für den *bedingten archivierten Zustand* bei Schritt 6 ein frühestes E-Fenster `[0.093251909354, 0.097834417010]`, verpasst von beiden ursprünglichen Scanrastern. Der bedingte Archiv-Schritt 10 besitzt zusätzlich ein C-Fenster `[0.668422789849, 0.684539225877]`, übersehen vom 0,06-Raster, nicht vom 0,04-Raster. Die neue earliest-korrigierte Pfadwahl divergiert aber schon an Schritt 6, deshalb ist Schritt 10 kein geprüfter Schritt auf dem neuen Pfad. Die Multipräzisions-Root-Nachweise sind hier **nur Originalberichtsstatus**, nicht neu ausgeführte oder vollständig um Messunsicherheit erweiterte Zertifikate. Quellen: `SRC-024`, `SRC-015`.
- `E024` → `PGKC-025` **BRANCHBEDINGUNG**: Nach erster korrigierter Insel bei Schritt6 ist Schritt10 nur Archivkonditional. *(QUELLENGETRAGEN)*
- `E035` → `PGKC-013` **METHODOLOGISCHE_VERBINDUNG**: Root-Precision im Historienpfad ist für ausgewählte Prozessordnung relevant, nicht schon eine Zeitmetrik. *(ARBEITSABLEITUNG)*
- `H004` → `PGKC-026` **ZU_PRUEFEN**: Welche RΦ-Gates hängen vom korrigierten earliest-selected Pfad statt dem alten Archiv-Pfad ab? *(NEUE_HYPOTHESE_KEIN_ERGEBNIS)*

## Fachliche Beziehungen

- [PGKM-007 – Prozessordnung, Eichrelation und lokale Zeit](PGKM-007.md)
- [PGKM-001 – Reversibler Ausgangskern und historische Schutzgrenzen](PGKM-001.md)
- [PGKM-002 – E/C-Ereignisse, Fronten und Auswahl](PGKM-002.md)
- [PGKM-005 – Occurrence-konsistente native Passage](PGKM-005.md)
- [PGKM-013 – HΦ, RΦ, NΦ: Funktion und Rückgewinnbarkeit](PGKM-013.md)

## TSM-Anschluss

- **TSM-127:** Begrifflicher Anschluss (ohne eigenständigen empirischen Nachweis).

## Offene Gegenprüfungen

- `H004` Welche RΦ-Gates hängen vom korrigierten earliest-selected Pfad statt dem alten Archiv-Pfad ab?

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-024`** (KORREKTUR; `EARLIEST_EVENT_FAIL_STEP6`): FSTT-01F fand bei archiviertem Schritt 6 von beiden historischen Rastern verpasste E-Crossing-Insel.
- **`PGKC-025`** (GELTUNG; `CONDITIONAL_OLD_STATE_ONLY`): Schritt 10 ist nur für den bedingten historischen Archivzustand zu bewerten; die earliest-korrigierte Folge läuft schon ab Schritt 6 anders.
- **`PGKC-266`** (METHODISCHE_KORREKTUR; `A6_3_LOCAL_NUMERIC_PASS`): Im archivierten CFG-Zustand Schritt 6 bestätigte eine eigene lokale Rechenauswertung eine E-Nullstelleninsel bei t≈0.093251909354 und 0.097834417010; beide historischen Raster haben gleiches negatives Randvorzeichen.
- **`PGKC-267`** (METHODISCHE_KORREKTUR; `A6_3_LOCAL_NUMERIC_PASS_ARCHIVE_CONDITIONAL`): Im bedingten archivierten Schritt-10-Zustand wiederholt A6/3 lokale C-Nullstellen bei t≈0.668422789849 und 0.684539225877; dt=0.04 zeigt Vorzeichenwechsel, dt=0.06 nicht.
- **`A6N-C001`** (offen; `status-offen`): 6 von 6 gewaehlte E/C-Ereignisse entsprechen den schon FSTT-01F-zertifizierten ersten gerichteten Nullstellen (POS1–5 und STOP1).

## Quellenstatus

- `SRC-015`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-024`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-069`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0028](../forschung/B02.md#integration-find-0028)** · PGK-0.43A2YJ · `ROBUST-DP PASS / A2YI INTERPRETATION SUPERSEDED`
- **[INTEGRATION-FIND-0030](../forschung/B03.md#integration-find-0030)** · FSTT-01E2 · `SELECTOR_CONTRACT_CONFLICT_LOCALIZED`
- **[INTEGRATION-FIND-0031](../forschung/B03.md#integration-find-0031)** · FSTT-01F · `FSTT_01F_COMPLETED_CONDITIONAL_FIXED_SPECTRAL_MODEL / NO_NEW_S3_PASS`
- **[INTEGRATION-FIND-0033](../forschung/B03.md#integration-find-0033)** · FSTT-01B/01C/01D · `READONLY_REPLAY / SAME_PARENT_CONTRAST / SYNTHETIC_CONTROL_SEPARATE`
- **[INTEGRATION-FIND-0034](../forschung/B03.md#integration-find-0034)** · PGK-LAMBDA-NAHT / SEAM-H3 · `ARCHIVGEBUNDENER_H3_TRANSPORT / STOP_GEGENKONTROLLE / KEINE_S3_FREIGABE`
- **[INTEGRATION-FIND-0045](../forschung/B05.md#integration-find-0045)** · A6N-01 / prospektives G6 · `OPTIONSRUECKWIRKUNG / KEIN_NEUES_G6_PASS`
- **[INTEGRATION-FIND-0097](../forschung/B08.md#integration-find-0097)** · PGK-0.43A2YN · `PASS FINITE SUITE`
- **[INTEGRATION-FIND-0108](../forschung/B08.md#integration-find-0108)** · PGK-0.43A2YY · `PASS-E1 / SUPPORT-GEOMETRIE INSUFFIZIENT`
