# PGKM-013 – HΦ, RΦ, NΦ: Funktion und Rückgewinnbarkeit

**Forschungsstatus:** `NONCANONICAL_RESEARCH_SYNTHESIS`
**Geltungsbereich:** RΦ-01 bis 04a; intrinsische vs explizit externe Funktionsaufgabe

## Forschungsfrage und Ausgangspunkt

Vorhandene Leistung, bedingte Regeneration und ausgewählte Regeneration getrennt; RΦ-01 STOP ist kein R=0.

## Definition und Prüfgegenstand

RΦ-01 bis 04a; intrinsische vs explizit externe Funktionsaufgabe

## Ergebnisse und Geltung

- **PGKC-028 [RESTRICTED_IO_PASS_FULL64D_FAIL]** RΦ-03 bestätigt Gleichheit auf einem eingeschränkten Eingangsraum, aber keine vollständige Operatorgleichheit. *[ORIGINALQUELLEN_BERICHT]*

## Gegenbefunde und Grenzen

- **PGKC-026 [NO_VALID_PHI__STOP]** RΦ-01 findet keine aus dem Original-PGK unabhängig notwendige intrinsische Φ-Aufgabe; R und N sind deshalb nicht adjudizierbar, nicht beide null.
- **PGKC-027 [R_COND_0_N_0_TASK_RELATIVE]** RΦ-02: Bei externer Aufgabe mit feststehenden Altkomponentenadressen kann der native Merge die alte getrennte Identität nicht regenerieren.
- **Grenze zu PGKC-026:** STOP nur für intrinsisch notwendige Leistung in dieser Quellprüfung.
- **Grenze zu PGKC-027:** Kein allgemeines regeneratives No-Go; nur diese extern definierte Alt-ID-Aufgabe.
- **Grenze zu PGKC-028:** Nicht als wiedergewählte alte Rolle oder S3-Regulation ausgeben.

## Ableitung und Interpretation

Die Beziehungen gelten entsprechend ihrem angegebenen Typ und Geltungsbereich.
**Drei getrennte Prädikate:** `H_Φ` = aktuell nachweisbare Leistung, `R_Φ` = konditional mögliche Rückgewinnung nach einer Störung, `N_Φ` = vom legalen nativen Verfahren tatsächlich realisierte Rückgewinnung. RΦ-01 scheitert schon am vorausgehenden intrinsischen Quellen-Gate `Φ`: folglich `R,N = NOT_ADJUDICABLE` und **nicht** null. RΦ-02 setzt stattdessen eine externe Alt-ID-Aufgabe und begründet nur dafür einen negativen Wiederherstellungsfall. RΦ-03 testet eine andere – reduzierte I/O-Äquivalenz. Sie dürfen nicht zu einem universellen Regenerationssatz verschmelzen. Quelle: `SRC-013`.
- `E025` → `PGKC-027` **AUFGABENWECHSEL**: Nach intrinsischem Phi-STOP kann eine externe Alt-ID-Aufgabe definiert werden; sie ist nicht das ursprünglich gesuchte intrinsische Phi. *(GELTUNGSUNTERSCHIED)*
- `E026` → `PGKC-028` **GELTUNGSUNTERSCHIED**: Negative Wiederherstellung alter IDs und 2D-I/O-Äquivalenz sprechen über unterschiedliche Zielrelationen. *(GELTUNGSUNTERSCHIED)*

## Fachliche Beziehungen

- [PGKM-008 – Funktionale Rollen, Trägerwechsel und Regeneration](PGKM-008.md)
- [PGKM-007 – Prozessordnung, Eichrelation und lokale Zeit](PGKM-007.md)
- [PGKM-012 – Root-Isolation und historischer Selektorfehler](PGKM-012.md)
- [PGKM-011 – Gewichtete Erreichbarkeit und BRW-Provenienz](PGKM-011.md)

## TSM-Anschluss

- **TSM-000:** Begrifflicher Anschluss (ohne eigenständigen empirischen Nachweis).

## Offene Gegenprüfungen

- `H002` Wann ist eine uhrfähige Wiederkehr zugleich eine unabhängig definierte Funktion?
- `H004` Welche RΦ-Gates hängen vom korrigierten earliest-selected Pfad statt dem alten Archiv-Pfad ab?
- `H003` Kann gleiche Teil-I/O-Funktion bei anderer Vollumgebung eine W-Marge verändern?

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-026`** (NEGATIV; `NO_VALID_PHI__STOP`): RΦ-01 findet keine aus dem Original-PGK unabhängig notwendige intrinsische Φ-Aufgabe; R und N sind deshalb nicht adjudizierbar, nicht beide null.
- **`PGKC-027`** (NEGATIV_BEGRENZT; `R_COND_0_N_0_TASK_RELATIVE`): RΦ-02: Bei externer Aufgabe mit feststehenden Altkomponentenadressen kann der native Merge die alte getrennte Identität nicht regenerieren.
- **`PGKC-028`** (GELTUNG; `RESTRICTED_IO_PASS_FULL64D_FAIL`): RΦ-03 bestätigt Gleichheit auf einem eingeschränkten Eingangsraum, aber keine vollständige Operatorgleichheit.
- **`PGKC-268`** (POSITIVER_TEILBEFUND; `A6_3_RAW_CSV_AGGREGATION_PASS`): A6/3 reaggregiert 8 RΦ-03 same-state-Partnerportpaare, alle mit maximaler Portabweichung ≤1.683×10^-15.
- **`PGKC-269`** (NEGATIV; `A6_3_RAW_CSV_AGGREGATION_PASS`): A6/3 reaggregiert 0/8 vollständige Operatorgleichheiten in RΦ-03; die minimale volle Operatornormdifferenz ist 0.80492618.
- **`PGKC-270`** (GEGENBEISPIEL; `A6_3_RAW_CSV_AGGREGATION_PASS`): In 3 der 8 RΦ-03-Paarvergleiche unterscheiden sich die Vorzeichen des aktuellen vollen Antwortwertes, trotz gemeinsamer Portgleichheit.
- **`PGKC-271`** (STATUS_GUARD; `ORIGINAL_CONTRACT_GUARD`): Der fixierte RΦ-03-Vertrag definiert keinen nativen Delegationsoperator und keine gewählte Regeneration; die E-Portvergleiche sind externe Reporter.
- **`PGKC-303`** (GELTUNGSGRENZE; `A6_4_GELTUNGSSCHUTZ`): Übereinstimmung an einem 2D-Port ohne gleiche 64D-Antwort ist kein ausgewählter Träger-Ersatz oder regenerierter Rollenpfad.
- **`A6N-C004`** (offen; `status-offen`): Der externe RPHI-02-Rollenauftrag verliert unter C1 fuer POS (1,13) und STOP (4,5) jeweils H=1 zu H=0.
- **`A6N-C005`** (offen; `status-offen`): Fuer feste alte Atom-IDs kann ihre einmal verlorene native getrennte Komponentenadressierung unter E-Hinzufuegen/C-Vereinigen nicht wiederhergestellt werden.

## Quellenstatus

- `SRC-013`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-070`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-071`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-074`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0033](../forschung/B03.md#integration-find-0033)** · FSTT-01B/01C/01D · `READONLY_REPLAY / SAME_PARENT_CONTRAST / SYNTHETIC_CONTROL_SEPARATE`
- **[INTEGRATION-FIND-0034](../forschung/B03.md#integration-find-0034)** · PGK-LAMBDA-NAHT / SEAM-H3 · `ARCHIVGEBUNDENER_H3_TRANSPORT / STOP_GEGENKONTROLLE / KEINE_S3_FREIGABE`
- **[INTEGRATION-FIND-0044](../forschung/B05.md#integration-find-0044)** · A6N-01 / A6N-T1 / PGKM-029 · `EXAKTER_SATZ_IM_PARTITIONSVERTRAG / BESTAND_VALIDIERT`
- **[INTEGRATION-FIND-0088](../forschung/B07.md#integration-find-0088)** · PGK-0.136 · `R10 PARTIAL, STRONGLY UPGRADED`
- **[INTEGRATION-FIND-0089](../forschung/B07.md#integration-find-0089)** · PGK-0.137 · `OUTCOME E / R11 PARTIAL_CONSTRAINED`
- **[INTEGRATION-FIND-0189](../forschung/B12.md#integration-find-0189)** · RΦ-01 / RΦ-02 · `NO_VALID_PHI / EXTERNAL_TASK_ONLY / R_COND_0_N_0_TASK_RELATIVE`
- **[INTEGRATION-FIND-0190](../forschung/B12.md#integration-find-0190)** · RΦ-03 · `RESTRICTED_IO_PASS / FULL64D_FAIL / NATIVE_REGENERATION_NOT_EARNED`
