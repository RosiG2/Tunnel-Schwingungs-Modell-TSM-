# TSM-Operationalisierung: Werkzeugfamilie

## Status und Autorität

Diese Datei ist die kanonische Korpusbeschreibung der TSM-Werkzeugfamilie für praktische Operationalisierung. Sie fasst drei getrennte Instrumente zusammen:

1. **TSM-Universalbewertung** – Einzelbewertung einer Lage, Maßnahme, Entscheidung oder Struktur.
2. **Gedeihlichkeitspyramide / Reflexionsmappe** – Betrachtung verbleibender destruktiver Strecken auf sieben tragenden Ebenen.
3. **TSM-Bündelkompass** – Mehrpunkt- und Wechselwirkungsanalyse für Maßnahmen-, Risiko- oder Konfliktbündel.

Die drei Instrumente ergänzen sich. Keines ersetzt die beiden anderen. Die Excel-Mappen bleiben die ausführbaren Referenzartefakte; diese Markdown-Datei stellt die für GPT-Wissen und Runner erforderliche Semantik, Formellogik, Schnittstellen und Schutzregeln bereit.

Die Werkzeuge erzeugen keine automatische Wahrheit, kein amtliches Ranking, keinen mathematischen Beweis und keine Freigabe ohne fachliche Verantwortung.

---

## 1. Auswahl des richtigen Instruments

| Fragestellung | Instrument | Kernfrage |
|---|---|---|
| Ein einzelner Fall, eine Maßnahme, Entscheidung oder Systemlage | TSM-Universalbewertung | Wie tragfähig, belastet, geschützt und rückbindbar ist dieser einzelne Gegenstand? |
| Gesellschaftliche, institutionelle oder historische Bedingungen | Gedeihlichkeitspyramide | Welche destruktiven Strecken werden kürzer oder länger, und wo liegt der höchste strukturelle Handlungsdruck? |
| Mehrere Punkte wirken gemeinsam | TSM-Bündelkompass | Welche Gesamtform entsteht aus den Einzelpunkten, ihren Wechselwirkungen, Schutzgrenzen und Evidenzlagen? |

**Arbeitsfolge:** Einzelpunkt → Bedingungs- und Weglängenreflexion → Bündelwirkung.

Der Bündelkompass darf nur verdichtete, gekennzeichnete Ergebnisse übernehmen. Er ersetzt weder die ursprüngliche Einzelbewertung noch deren Begründungen und Quellen.

---

## 2. Verbindliche Namensräume

Gleichnamige TSM-Zeichen besitzen in verschiedenen Domänen nicht automatisch dieselbe Bedeutung. Deshalb gelten folgende Präfixe:

- `UB_` – Universalbewertung
- `GP_` – Gedeihlichkeitspyramide
- `BK_` – Bündelkompass
- `PHYS_` beziehungsweise bestehende 136D-Feldnamen – physikalischer oder 136D-Kontext

Beispiele:

| Unzulässig mehrdeutig | Kanonische Felder |
|---|---|
| `C` | `UB_C_n`, `BK_B`, physikalisches `C` nur im ausdrücklich benannten Physikprofil |
| `Phi` | `UB_Phi_n` für Prozessasynchronie; `dphi_rad` für Phasenwinkel |
| `tau` | `UB_Tau_n` für Reaktionszeitpassung; `tau` oder `tau_eff` nur im benannten Resonanzprofil |
| `B` | `UB_B`, `BK_B`, `B_rank` beziehungsweise `recommended_B_rank` |
| `S` | `UB_S`, `BK_S`, `S_rank` beziehungsweise `recommended_S_rank` |
| `Delta` | `UB_Delta`; physikalische oder andere Differenzen benötigen einen eigenen Namen |
| `K`, `R`, `F` | nur mit Zonen- oder Werkzeugkontext, z. B. `UB_final_zone`, `BK_status`, `sim_regime` |

Eine automatische Übertragung zwischen Namensräumen ist verboten. Sie benötigt:

1. benanntes Quellwerkzeug,
2. explizite Feldzuordnung,
3. Skalen- und Einheitenangabe,
4. Quellen- oder Evidenzstatus,
5. dokumentierte Unsicherheit.

---

# Teil A – TSM-Universalbewertung

## 3. Zweck

Die Universalbewertung strukturiert einen einzelnen Gegenstand über sechs Achsen, einen nicht kompensierbaren Schutzkanal und einen Rückbindungspfad. Geeignete Gegenstände sind Organisationen, Maßnahmen, IT-Systeme, Finanzentscheidungen, Kapitalflüsse, Produkte, Kredite, Förderungen, Systemlagen und gemeinwohl- oder grundrechtsnahe Fälle.

Sie bewertet keine Personen und ersetzt keine Rechts-, Finanz-, Fach- oder Sicherheitsprüfung.

## 4. Eingaben und Achsen

Die Beobachtungswerte werden auf einer Skala von 0 bis 4 erhoben und auf 0 bis 1 normiert.

- `UB_C_n` – Ziel- und Strukturkonsistenz
- `UB_Phi_n` – Prozessasynchronie
- `UB_Tau_n` – normierte Reaktionsgeschwindigkeit beziehungsweise Zeitpassung
- `UB_H_n` – strukturelle Trägheit
- `UB_N_n` – Nebenwirkungsdruck
- `UB_D_n` – Zeitstabilität

Alternativ dürfen `UB_C_raw`, `UB_Phi_raw`, `UB_Tau_raw`, `UB_H_raw`, `UB_N_raw`, `UB_D_raw` im Bereich 0 bis 4 geliefert werden. Der Runner normiert diese durch Division durch 4. Ein ausdrücklich gesetztes `UB_Tau_override_n` hat Vorrang vor `UB_Tau_n` und `UB_Tau_raw`.

Positive Rückkopplungsfragen der Phi-Achse werden vor der Achsenmittelung invertiert: `4 - Score`.

## 5. Kernformeln

Kontrollparameter der Referenzmappe:

```text
w_C = 0.40
w_T = 0.30
w_L = 0.30
v_Phi = 0.50
v_H = 0.25
v_N = 0.25
lambda_mix = 0.50
tau_target = 0.60
sigma_tau = 0.15
k_logistic = 4
```

Zeitfenster und Gegenpol zur Asynchronie:

```text
UB_T_n = exp(-((UB_Tau_n - 0.60)^2) / (2 * 0.15^2))
UB_L_n = 1 - UB_Phi_n
```

Lineare und geometrische Tragfähigkeit:

```text
UB_B_lin = 0.40*UB_C_n + 0.30*UB_T_n + 0.30*UB_L_n
UB_B_geo = UB_C_n^0.40 * UB_T_n^0.30 * UB_L_n^0.30
UB_B = 0.50*UB_B_lin + 0.50*UB_B_geo
```

Belastung, Saldo und Entscheidungsformen:

```text
UB_S = 0.50*UB_Phi_n + 0.25*UB_H_n + 0.25*UB_N_n
UB_Delta = UB_B - UB_S
UB_G21a = UB_D_n * clamp((UB_Delta + 1)/2, 0, 1)
UB_G21b = UB_D_n * (1 / (1 + exp(-4*UB_Delta)))
UB_R_rel = UB_B / (UB_B + UB_S + 0.001)
```

Der Evidenzgrad ist eine Meta-Information. Er verändert die Formeln für `UB_B` und `UB_S` nicht.

## 6. Basis-Guard

STOP wird ausgelöst, wenn mindestens eine Bedingung gilt:

```text
UB_Phi_n > 0.80
UB_N_n > 0.70
UB_D_n < 0.50
UB_C_n < 0.25
```

CHECK wird ausgelöst, wenn kein STOP vorliegt, aber mindestens eine Vorwarnschwelle gilt:

```text
UB_Phi_n > 0.68
UB_N_n > 0.595
UB_D_n < 0.55
UB_C_n < 0.275
```

Andernfalls lautet der Basis-Guard `OK`.

## 7. Schutzgrenzen

Die sechs Schutzwerte `UB_SG1` bis `UB_SG6` liegen auf der Skala 0 bis 4:

1. schutzlos belastete Betroffene,
2. verdeckte Lastverschiebung,
3. Intransparenz oder Nicht-Erklärbarkeit,
4. fehlende Korrigierbarkeit,
5. Funktionalisierung von Personen oder Gruppen,
6. fehlende kontrollierte Rücknahme.

Die Schutzwerte werden nicht in `UB_B`, `UB_S` oder `UB_G21a` eingemittelt.

Fail-closed-Regel des Runners:

- kein oder unvollständiger Schutzsatz → `UB_protection_status = OFFEN`
- vollständiger Satz und mindestens eine STOP-Bedingung → `STOP`
- sonst mindestens ein Wert ab 2 → `CHECK`
- andernfalls → `OK`

STOP-Bedingungen der Referenzmappe:

```text
max(SG1..SG6) = 4
oder mindestens zwei SG-Werte >= 3
oder SG1 >= 3
oder SG2 >= 3
oder SG5 >= 3
```

## 8. Final Guard, Zone und Außenstatus

```text
Basis-STOP oder Schutz-STOP -> UB_final_guard = STOP
Basis-CHECK, Schutz-CHECK oder Schutz-OFFEN -> UB_final_guard = CHECK
sonst -> UB_final_guard = OK
```

Basiszone, sofern der Basis-Guard nicht STOP ist:

```text
K+ : UB_G21a >= 0.85 und UB_B >= 0.80 und UB_S <= 0.20
K  : UB_G21a >= 0.70 und UB_B >= 0.65 und UB_S <= 0.35
R↑ : UB_G21a >= 0.55
R↓ : UB_G21a >= 0.40
F  : UB_G21a >= 0.20
F+ : darunter
```

Bei Basis-STOP oder Schutz-STOP gilt `UB_final_zone = F+`.

Außenstatus:

- `K+` oder `K` → tragfähig
- `R↑` → nachsteuerungsbedürftig (aufwärts)
- `R↓` → nachsteuerungsbedürftig (abwärts)
- `F` → kritisch
- `F+` → nicht freigabefähig

Schutz-CHECK oder Schutz-OFFEN deckelt einen sonst tragfähigen oder aufwärts gerichteten Außenstatus auf „nachsteuerungsbedürftig (abwärts)“.

## 9. Historische Lernlogik

Optional können zehn Statusfelder `UB_HL1` bis `UB_HL10` geführt werden:

1. Gewaltreduktion
2. Würdegewinn
3. Transparenzgewinn
4. Beteiligung
5. Korrigierbarkeit
6. Wissensbindung
7. Lastenrückholung
8. Langzeitfähigkeit
9. Gemeinwohlbindung
10. systemische Kohärenz

Erlaubte Werte:

```text
erfüllt | teilweise | offen | kritisch | nicht anwendbar
```

Die Lernlogik verändert die Hauptformeln nicht. Sie erhöht die Begründungspflicht und liefert eine Zusatzlesart:

- mindestens ein dominantes kritisches Muster → Rückfallmuster erkennbar
- offene Daten dominieren → Verbesserungslinie offen
- mehrere erfüllte Punkte, keine kritischen → Verbesserungslinie erkennbar
- sonst → Verbesserungslinie teilweise erkennbar

## 10. Ausgaben und Rückbindung

Pflichtausgaben sind:

```text
UB_B, UB_S, UB_Delta, UB_G21a, UB_G21b, UB_R_rel
UB_base_guard, UB_protection_status, UB_final_guard
UB_base_zone, UB_final_zone, UB_final_external_status
UB_next_step, UB_evidence_grade, UB_status
```

CHECK, STOP, OFFEN oder fehlende Tragfähigkeit öffnen den Rückbindungspfad. Eine vollständige Rückbindungszeile enthält mindestens Maßnahme, Verantwortung, Start- beziehungsweise Prüftermin und Sollsignal.

---

# Teil B – Gedeihlichkeitspyramide

## 11. Zweck und Ebenen

Die Gedeihlichkeitspyramide fragt nicht nach dem Wert eines Landes, einer Kultur oder einer Person. Sie untersucht, welche destruktiven Strecken kürzer oder länger werden.

Sieben Ebenen:

| GP_level_id | Ebene | Standardfaktor |
|---:|---|---:|
| 1 | Weniger Not | 1.60 |
| 2 | Weniger Angst | 1.50 |
| 3 | Weniger Willkür | 1.40 |
| 4 | Weniger Intransparenz | 1.30 |
| 5 | Weniger Ungerechtigkeit | 1.20 |
| 6 | Weniger Ohnmacht / mehr Freiheit | 1.10 |
| 7 | Mehr Gedeihlichkeit / gemeinsame Zukunft | 1.00 |

Die tiefen Ebenen erhalten höhere Positionsfaktoren wegen ihrer Tragwirkung, nicht wegen eines höheren moralischen Werts.

## 12. Eingaben

Pro Ebene:

- `GP_level_id` oder `GP_level`
- `GP_assessment` aus `-2, -1, 0, 1, 2, ?`
- `GP_certainty_pct` von 0 bis 100
- optional `GP_position_factor`
- optional `GP_rollback_risk`
- `GP_reason`, `GP_counterevidence`, `GP_source`

Skalenlesart:

- `+2` – destruktive Strecke wird deutlich kürzer
- `+1` – etwas kürzer
- `0` – keine erkennbare Veränderung
- `-1` – etwas länger
- `-2` – deutlich länger
- `?` – unklar oder nicht beurteilbar

Leere Felder sind nicht dasselbe wie Bewertung 0.

## 13. Formeln

```text
GP_path_length = (2 - GP_assessment) / 4
GP_urgency = GP_path_length * GP_position_factor
GP_weighted_change = GP_assessment * (GP_certainty_pct/100) * GP_position_factor
```

`GP_weighted_change` ist ein Profilwert aus Bewertung, Sicherheit und Tragwirkung. Er ersetzt nicht die Weglänge.

Dringlichkeitsstatus:

```text
0 bis <0.01   -> niedrig
0.01 bis <0.35 -> gering
0.35 bis <0.65 -> mittel
0.65 bis <1.00 -> erhöht
ab 1.00        -> hoch
```

Eine Sicherheit unter 60 Prozent erzeugt einen Prüfhinweis, verändert aber die Weglänge und den Dringlichkeitsindex nicht automatisch.

## 14. Mittelachse, Quellen und Rückfallrisiko

Kunst, Kultur, Sprache, Erzählung, Spiel und Sinn bilden eine Mittelachse über alle sieben Ebenen. Sie sind kein nachträglicher Zusatz, sondern vermitteln Deutung, Kritik, Erinnerung, Ausdruck und gemeinsame Zukunft.

Zu jeder Ebene sollen Quellen, Gegenanzeichen und Unsicherheit getrennt dokumentiert werden. Rückfallrisiken zeigen, ob eine bereits verkürzte Strecke wieder länger werden könnte.

Pflichtzusammenfassungen:

```text
GP_highest_urgency_level
GP_longest_path_level
GP_average_path_length
GP_lowest_certainty_pct
GP_highest_rollback_risk
GP_priority_order
```

## 15. Grenzen

- kein amtliches Ranking
- keine moralische Gesamtverurteilung
- keine automatische Maßnahme
- keine Objektivität ohne Kontext, Zeitraum und Quellen
- keine Fortschrittsgarantie

---

# Teil C – TSM-Bündelkompass

## 16. Zweck

Der Bündelkompass verarbeitet mehrere Einzelpunkte und ihre gerichteten Wechselwirkungen. Geeignete Fälle sind Reformpakete, Projektportfolios, KI-Einführungen, Konfliktfelder, Maßnahmenbündel und kombinierte Risiko- oder Chancenlagen.

Jeder Punkt bleibt als Einzelpunkt erhalten. Schutzgrenzen, Evidenzlücken und Unsicherheit dürfen nicht durch Durchschnittswerte verschwinden.

## 17. Kanonische Eingabefelder

Pro Punkt:

```text
BK_bundle_id, BK_case_id, BK_point_id, BK_point
BK_source_tool, BK_weight
BK_B, BK_S, BK_pyramid_restway
BK_rollback_risk, BK_protection_warning, BK_certainty_pct
BK_synergy_potential, BK_conflict_potential
BK_key_fit, BK_ethics_compatibility, BK_source_reliability
BK_evidence_type, BK_confidence_min, BK_confidence_max
BK_source, BK_scenario
```

`BK_B` und `BK_S` sind übernommene, ausdrücklich gemappte Bündel-Eingänge. Sie dürfen nicht still aus physikalischen `B_rank`- oder `S_rank`-Feldern übernommen werden.

Gerichtete Wechselwirkungen werden separat geführt:

```text
BK_source_id, BK_target_id, BK_interaction
```

`BK_interaction` liegt zwischen -3 und +3. Diagonalwerte werden ignoriert. A→B ist nicht automatisch B→A.

## 18. Kategoriale Normierung

Rückfallrisiko und Synergie-/Konfliktpotenzial:

```text
niedrig = 0.25
mittel = 0.50
hoch = 0.75
sehr hoch = 1.00
```

Schutzwarnung:

```text
keine = 0
weich = 0.50
hart = 1.00
```

Schlüsselpassung:

```text
schwach = 0.25
mittel = 0.50
stark = 0.75
sehr stark = 1.00
```

Ethikverträglichkeit:

```text
kritisch = 0.25
unklar = 0.50
tragfähig = 0.75
sehr tragfähig = 1.00
```

Quellenbelastbarkeit:

```text
offen = 0.25
unsicher = 0.35
gemischt = 0.60
gut = 0.85
sehr gut = 1.00
```

Evidenztyp für den Evidenzfaktor:

```text
Metaanalyse/Review = 1.00
amtliche Quelle = 0.85
Daten/Statistik = 0.80
Expert:innenurteil = 0.55
Medienbericht = 0.45
Annahme/Illustration = 0.30
sonstige/unklare Quelle = 0.50
```

## 19. Punktformeln

```text
BK_pressure = clamp(
    0.40*BK_pyramid_restway
  + 0.25*BK_rollback_norm
  + 0.25*BK_protection_norm
  + 0.10*(1 - BK_certainty_factor), 0, 1)

BK_coherence = clamp(
    0.35*BK_key_fit_norm
  + 0.25*BK_synergy_norm
  + 0.25*BK_ethics_norm
  + 0.15*BK_source_reliability_norm, 0, 1)

BK_bridge = clamp(
    0.50*BK_B
  + 0.25*(1 - BK_S)
  + 0.25*(1 - BK_pyramid_restway), 0, 1)
```

Interaktionsdruck pro Punkt ist der Mittelwert der auf -1 bis +1 normierten ein- und ausgehenden Wechselwirkungen.

Punktlesart:

```text
harte Schutzwarnung -> gesperrt
BK_bridge >= 0.65 und BK_pressure < 0.35 und Ethik >= 0.65 -> kohärent gedeihlich
BK_B >= 0.65 und Ethik < 0.50 -> formal tragfähig / ethisch fragmentiert
Ethik >= 0.65 und (BK_B < 0.35 oder BK_pressure >= 0.65) -> ethisch plausibel / resonanztechnisch instabil
BK_pressure >= 0.65 oder BK_bridge < 0.35 -> Rückholplan erforderlich
sonst -> regulativer Übergang
```

Kurzstatus:

```text
hart -> gesperrt
BK_pressure >= 0.75 und BK_coherence < 0.50 -> fragmentiert
BK_pressure >= 0.65 -> rückholpflichtig
BK_coherence >= 0.65 und BK_pressure < 0.35 -> kohärent
sonst -> regulativ
```

Rückholpriorität:

```text
hart -> 5
sonst ceil(clamp(0.55*BK_pressure + 0.25*(1-BK_coherence) + 0.20*max(0,BK_interaction_pressure),0,1)*5)
Minimum = 1
```

## 20. Evidenz und Konfidenz

```text
BK_confidence_span = BK_confidence_max - BK_confidence_min
BK_pressure_min = max(0, BK_pressure - (0.15*(1-BK_evidence_norm) + 0.05*(1-BK_certainty_factor)))
BK_pressure_max = min(1, BK_pressure + (0.15*(1-BK_evidence_norm) + 0.05*(1-BK_certainty_factor)))
BK_evidence_weighted_pressure = BK_pressure * (0.75 + 0.25*BK_evidence_norm)
```

Prüfhinweis:

- Konfidenzspanne über 0.35 → hohe Unsicherheit
- Evidenzfaktor unter 0.50 → Evidenz schwach
- niedrige Evidenz plus hoher Druck muss im Prüflog sichtbar werden

## 21. Bündelgeometrie

Gemeinsamer heuristischer Ordnungsraum:

```text
X = BK_B
Y = 1 - BK_pyramid_restway
Z = BK_pressure
```

Das Zentrum ist der Mittelwert der aktiven Punkte. Der Abstand ist die euklidische Distanz zum Zentrum. Standard-Randpunktschwelle: 0.35.

```text
BK_fragmentation = clamp(
    0.40*mittlerer_Abstand
  + 0.30*Randpunktquote
  + 0.30*Widerspruchsanteil, 0, 1)
```

Hüllenstatus:

- mindestens eine harte Schutzwarnung → ethisch gesperrt
- Fragmentierungsindex unter 0.35 → kompakt-kohärent
- unter 0.65 → regulativ-gestreut
- ab 0.65 und Randpunktquote über 0.50 → randlastig
- sonst → fragmentiert

Dies ist eine geometrische Heuristik. Es ist keine formale Talagrand-Berechnung und kein mathematischer Beweis.

## 22. Szenarien

| Szenario | B-Faktor | S-Faktor | Restweg | Risiko | Schutzkorrektur |
|---|---:|---:|---:|---:|---:|
| Baseline | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| mit Rückholmaßnahmen | 1.05 | 0.90 | 0.85 | 0.80 | -0.25 |
| Worst-Case | 0.90 | 1.15 | 1.20 | 1.20 | +0.25 |
| Best-Case | 1.10 | 0.85 | 0.80 | 0.75 | -0.50 |

Szenarien verändern keine Grunddaten. Sie erzeugen eine getrennte Sensitivitätssicht. Eine harte Schutzwarnung bleibt auch in einem günstigen Szenario sperrend, bis sie sachlich behoben und neu bewertet wurde.

## 23. Rückholplan

Der Rückholplan enthält mindestens:

- Priorität
- Problemtyp
- Anzeiger
- Schlüssel
- Maßnahme oder Klärungsschritt
- Verantwortlichkeit
- Frist
- Monitoring-Metrik
- Bearbeitungsstatus

---

# Teil D – Schnittstellen und Schutzregeln

## 24. Übergabe aus der Universalbewertung

Zulässige verdichtete Felder:

```text
UB_case_id
UB_final_guard
UB_final_zone
UB_final_external_status
UB_B
UB_S
UB_protection_status
UB_evidence_grade
UB_source
```

Eine Übernahme in den Bündelkompass benötigt einen dokumentierten Mapper:

```text
UB_B -> BK_B
UB_S -> BK_S
UB_protection_status -> BK_protection_warning
```

Die Übersetzung des Schutzstatus lautet standardmäßig:

```text
OK -> keine
CHECK oder OFFEN -> weich
STOP -> hart
```

## 25. Übergabe aus der Gedeihlichkeitspyramide

Zulässige verdichtete Felder:

```text
GP_highest_urgency_level
GP_longest_path_level
GP_average_path_length
GP_highest_rollback_risk
GP_lowest_certainty_pct
GP_culture_axis_question
GP_reason
GP_source
```

Standardzuordnung:

```text
GP_average_path_length -> BK_pyramid_restway
```

Die Einzelwerte und Begründungen bleiben in der Pyramidenanalyse erhalten.

## 26. Fail-closed-Regeln

1. Fehlende Pflichtfelder erzeugen `not_evaluable`, `OFFEN`, `FLAG` oder `FAIL`, keinen positiven Befund.
2. Schutzgrenzen haben Vorrang vor Durchschnitts- und Szenariologik.
3. Unsicherheit wird angezeigt, nicht still geglättet.
4. Quellen, Beobachtung, Deutung und Entscheidung bleiben getrennt.
5. Personen-Scoring, Kultur-Ranking und automatische politische, finanzielle, rechtliche oder medizinische Entscheidungen sind verboten.
6. Physikalische und sozial-organisatorische Variablen dürfen trotz gleicher Buchstaben nicht gleichgesetzt werden.
7. Die Excel-Mappen sind Referenzimplementierungen; der Runner ist eine nachvollziehbare, namespaced Reproduktion der dokumentierten Kernlogik, kein Ersatz für die vollständige Benutzeroberfläche.

## 27. Runner-Befehle

```text
universal-evaluate
pyramid-evaluate
bundle-evaluate
tool-family-audit
operational-namespace-audit
bundle-import-audit
```

Die Audits prüfen Werkzeugauswahl, Namensräume, Übergabeverträge, Schutzvorrang und die interne Vollständigkeit dieser Datei.

## 28. Referenzartefakte

Ausführbare Referenzmappen außerhalb des aktiven GPT-Korpus:

```text
TSM_Universalbewertung_v4_0_1_repariert.xlsx
Gedeihlichkeitspyramide_Reflexionsmappe_v1_0_2_repariert.xlsx
TSM_Buendelkompass_v1_0_2_repariert.xlsx
```

Die Handbücher dienten als semantische Quellen dieser kanonischen Zusammenführung. Sie werden nicht zusätzlich als parallele Korpusdateien benötigt.

## 29. Schlussregel

Die Werkzeugfamilie ist dann korrekt eingesetzt, wenn sie nicht möglichst schnell eine Zahl erzeugt, sondern den richtigen Gegenstand, die richtige Ebene, die Schutzgrenzen, die Quellenlage und den Rückholweg sichtbar hält.
# Teil E – Mehrskaliges Durchblickprofil

## 30. Status und kanonische Kurzform

Das mehrskalige Durchblickprofil ist kein viertes Instrument. Es koordiniert wiederholte und eindeutig abgegrenzte Anwendungen von Universalbewertung, Gedeihlichkeitspyramide und Bündelkompass.

Es erzeugt keine neuen Grundwerte durch freie Umdeutung. Sämtliche Kartenpunkte und Ableitungen müssen auf freigegebene Quellfelder der drei Werkzeuge oder auf ausdrücklich deklarierte manuelle Beobachtungen zurückführbar bleiben.

Kanonische Kurzform:

> Die Universalbewertung sieht den einzelnen Knoten.  
> Die Gedeihlichkeitspyramide sieht Ebene, Tiefe und verbleibende Strecke.  
> Der Bündelkompass sieht gerichtete Wechselwirkungen und die Gesamtform.  
> Das Durchblickprofil ordnet diese Ergebnisse nach Einheit, Kanal, Skala und Zeit.

## 31. Verbindlicher Namensraum

Für das Profil gilt der Präfix:

```text
TF_ = Tool-Family profile
```

Der Präfix bezeichnet keine vierte Bewertungslogik. Er kennzeichnet Metadaten, Orchestrierung, Vergleich und Visualisierung über UB, GP und BK.

Pflichtfelder:

```text
TF_map_id
TF_map_version
TF_question
TF_unit_id
TF_unit_type
TF_channel_id
TF_scale_id
TF_scale_definition
TF_time_id
TF_time_start
TF_time_end
TF_source_tool
TF_source_case_id
TF_source_status
TF_source_fields
TF_mapper_id
TF_evidence_grade
TF_source
TF_counterevidence
TF_uncertainty
TF_protection_status
TF_map_status
```

Optionale Orchestrierungs- und Ergebnisfelder:

```text
TF_scope_role
TF_scale_order
TF_local_status
TF_local_protection_flag
TF_local_evidence_flag
TF_boundary_point
TF_scale_break
TF_scale_break_from
TF_scale_break_to
TF_scale_break_reason
TF_channel_conflict
TF_temporal_shift
TF_structural_reach_profile
TF_local_global_gap
TF_recovery_priority
TF_note
TF_row_audit_status
TF_fail_closed_reason
```

Physikalische Felder wie `dphi_rad`, `tau_eff`, `R_PLV` oder `Q_c` dürfen nicht in `TF_`-Felder umbenannt oder automatisch übernommen werden.

## 32. Untersuchungseinheiten und Schutz vor Gruppen-Scoring

Vor der Bewertung ist festzulegen, was einen eigenständigen Knoten bildet.

Zulässige Beispiele:

- Maßnahme,
- Prozessschritt,
- Organisationseinheit,
- technische Komponente,
- institutionelle Schnittstelle,
- Region,
- Betroffenen- oder Wirkungsperspektive,
- Zeitabschnitt.

Eine Nutzer- oder Bevölkerungsgruppe darf nur als Perspektive auf Wirkungen, Schutz, Zugang, Belastung oder Teilhabe geführt werden. Die Gruppe selbst darf nicht gerankt oder hinsichtlich ihres Wertes, Charakters oder ihrer Gedeihlichkeit bewertet werden.

Unzulässig ist eine nachträgliche Knotenbildung allein deshalb, weil dadurch ein gewünschtes Gesamtbild entsteht.

## 33. Wirkungskanäle

Ein Knoten kann in mehreren Kanälen getrennt untersucht werden, beispielsweise:

```text
Schutz
Versorgung
Beteiligung
Transparenz
Kommunikation
Technik
Wirtschaftlichkeit
Umwelt
Langzeitstabilität
Rückholfähigkeit
```

Kanäle dürfen nicht still gemittelt werden. Gegensätzliche Kanalbefunde werden als `TF_channel_conflict = true` ausgewiesen und bleiben getrennt nachvollziehbar.

## 34. Skalen und Tragweitenprofil

Skalen werden fallbezogen vorab definiert. Eine empfohlene, aber nicht universell verpflichtende Grundstruktur ist:

```text
S1 = Einzelpunkt oder unmittelbarer Prozess
S2 = lokaler Verbund oder Team
S3 = Organisation oder Institution
S4 = organisationsübergreifender oder regionaler Kontext
S5 = gesellschaftlicher oder langfristiger Kontext
```

Die Bezeichnungen sind anpassbar. Reihenfolge, Einschlusslogik und Übergangskriterien müssen vor der Auswertung dokumentiert werden.

`TF_structural_reach_profile` ist primär ein Profil je Skala, beispielsweise:

```text
S1=carried; S2=carried; S3=broken; S4=not_tested; S5=counteracting
```

Eine einzelne höchste Tragweitenstufe darf nur erzeugt werden, wenn die Skalen im konkreten Fall tatsächlich geordnet, vergleichbar und geprüft sind. Fehlende Ebenen werden nicht interpoliert.

## 35. Arbeitsablauf

### 35.1 Kartenrahmen

Vorab festlegen:

```text
Erkenntnisziel
Knoten und Abgrenzungsregel
Kanäle
Skalen und Übergangskriterien
Zeitfenster
Quellenanforderungen
Schutzanforderungen
Mapper
Vergleichsregeln
```

### 35.2 Einzelpunktaufnahme

Für jeden Knoten und relevanten Kanal kann eine Universalbewertung ausgeführt werden:

```text
universal-evaluate
```

Zulässige Übernahmefelder:

```text
UB_case_id
UB_final_guard
UB_final_zone
UB_final_external_status
UB_B
UB_S
UB_protection_status
UB_evidence_grade
UB_source
```

### 35.3 Ebenen- und Wegaufnahme

Für die strukturelle Einbettung kann die Gedeihlichkeitspyramide ausgeführt werden:

```text
pyramid-evaluate
```

Zulässige Übernahmefelder:

```text
GP_highest_urgency_level
GP_longest_path_level
GP_average_path_length
GP_highest_rollback_risk
GP_lowest_certainty_pct
GP_reason
GP_source
```

### 35.4 Wechselwirkungsaufnahme und Bündelauswertung

Gerichtete Beziehungen werden getrennt als A→B und B→A erfasst. Eine Wechselwirkung benötigt eine begründete Wirkannahme oder Quelle; Gleichzeitigkeit allein reicht nicht.

```text
bundle-evaluate
```

Zulässige Übernahmefelder:

```text
BK_point_id
BK_source_id
BK_target_id
BK_interaction
BK_coherence
BK_pressure
BK_fragmentation
BK_status
BK_recovery_priority
BK_protection_status
BK_source
BK_certainty_pct
```

### 35.5 Durchblickkarte

Die Ergebnisse werden nicht erneut zu einem universellen Gesamtwert verdichtet. Die Ausgabe hält mindestens getrennt:

1. Knotenlage,
2. Schutzlage,
3. Evidenzlage,
4. gerichtete Wechselwirkungen,
5. Skalenprofil,
6. Zeitvergleich,
7. Rückhol- und Klärungspfade.

## 36. Quellenvertrag und Mapper

Jeder Kartenpunkt benötigt:

- Quellwerkzeug oder manuelle Quellenklasse,
- Quellfall-ID,
- tatsächlich verwendete Quellfelder,
- Mapper-ID und Mapper-Version,
- Evidenzstatus,
- Quelle und Gegenbelege,
- Unsicherheit,
- Schutzstatus,
- Freigabe- oder Kartenstatus.

`TF_source_fields` muss die übernommenen Felder ausdrücklich nennen. Ein Mapper darf fehlende Werte nicht erfinden, physikalische Felder nicht automatisch übertragen und Schutzstatus nicht herabstufen.

Zulässige Quellwerkzeuge:

```text
UB
GP
BK
manual
```

Bei `manual` sind Beobachtungsbasis, Quelle, Gegenbelege und Unsicherheit vollständig zu dokumentieren.

## 37. Lokale-globale Abweichung

`TF_local_global_gap` wird kategorial ausgewiesen:

```text
none
moderate
high
protection_relevant
evidence_driven
not_evaluable
```

Kanonisch ist nicht eine feste Zahlenschwelle, sondern die Regel:

> Eine lokale-globale Abweichung liegt vor, wenn eine Verdichtung wesentliche Schutz-, Evidenz-, Belastungs- oder Teilgruppenbefunde verdeckt.

Numerische Schwellen sind zunächst `candidate_baseline`, E1/E2 und konfigurierbar. Sie dürfen nach realen Falltests verändert oder verworfen werden.

`protection_relevant` gilt unabhängig von Mittelwerten, sobald ein lokaler harter Schutzstatus durch eine Gesamtsicht verdeckt würde.

## 38. Skalenbruch

`TF_scale_break = true`, wenn ein Befund auf einer niedrigeren geprüften Skala getragen oder angespannt erscheint, auf einer höheren geprüften Skala jedoch:

- blockiert oder gegenläufig wird,
- seine Schutzverträglichkeit verliert,
- durch gerichtete Gegenwirkungen aufgehoben wird,
- nicht mehr durch Quellen getragen ist.

Der Skalenbruch wird mindestens dokumentiert durch:

```text
TF_scale_break_from
TF_scale_break_to
TF_scale_break_reason
```

Eine automatische Skalenbrucherkennung ist nur zulässig, wenn `TF_scale_order` und ein explizites Statusmapping vorliegen.

## 39. Zeitvergleich

Zeitvergleiche benötigen stabile oder versionierte:

```text
TF_unit_id
TF_channel_id
TF_scale_id
TF_scale_definition
TF_mapper_id
TF_map_version
```

Ändert sich eine Definition oder ein Mapper, lautet der Befund:

```text
TF_temporal_shift = method_changed
```

Weitere zulässige Werte:

```text
improved
worsened
mixed
stable
uncertain
method_changed
not_evaluable
```

Verbesserung oder Verschlechterung darf nur ausgegeben werden, wenn die verglichenen Status in einem vorab dokumentierten qualitativen Statusmapping geordnet sind.

## 40. Standardvisualisierungen und Ausgaben

Empfohlen werden getrennte Ansichten:

1. **Knotenkarte:** lokaler Status, Schutzstatus und Evidenz je Knoten.
2. **Beziehungskarte:** gerichtete BK-Wechselwirkungen.
3. **Skalenleiter:** Tragweitenprofile und Skalenbrüche.
4. **Kanalmatrix:** unterschiedliche Befunde je Wirkungskanal.
5. **Zeitvergleich:** Veränderungen stabil definierter Knoten.
6. **Rückholkarte:** Prioritäten, Verantwortlichkeiten und Monitoring.

Schutz- und Evidenzebenen dürfen visuell nicht hinter einer Gesamtfarbe verschwinden.

Eine vollständige Ausgabe enthält mindestens:

```text
Kartenrahmen
Knotenübersicht
Kanäle
Skalen
Zeitfenster
lokale Quellprofile
gerichtete Wechselwirkungen
Schutz-Hotspots
Evidenzlücken
Randpunkte
Skalenbrüche
lokale-globale Abweichungen
Tragweitenprofile
Rückholplan
Auditstatus
```

## 41. Fail-closed-Status

```text
fehlender Knotenrahmen -> incomplete_map
fehlender Kanal -> channel_undefined
fehlende Skala -> scale_undefined
fehlendes Zeitfenster -> time_undefined
fehlende Quelle -> source_open
fehlender Mapper -> mapping_blocked
unvollständiger Schutzstatus -> protection_open
nicht vergleichbare Durchläufe -> comparison_blocked
starke Knoten-, Mapper- oder Skalenempfindlichkeit -> unstable_map
Gruppen-Ranking oder Personen-Scoring -> prohibited_scoring
physikalische Bedeutungsidentität -> category_error
```

Keiner dieser Status darf als neutraler oder positiver Kartenpunkt behandelt werden.

## 42. Runner-Befehle und Schlussregel

```text
tool-family-map-audit
tool-family-map
tool-family-map-compare
```

Version 1 führt keine neue Bewertungsformel ein. Der Runner:

- prüft Pflichtdimensionen und Namensräume,
- validiert UB-, GP-, BK- und manuelle Quellfälle,
- kontrolliert Mapper und Schutzweitergabe,
- erzeugt eine strukturierte Kartenansicht,
- weist Konflikte, Skalenbrüche, Vergleichsblockaden und Evidenzlücken aus,
- vergleicht Zeitstände nur bei stabiler oder versionierter Methodik.

Das Profil ist korrekt eingesetzt, wenn es lokale Unterschiede und ihre Beziehungen sichtbar macht, ohne aus Visualisierung eine neue Evidenz, aus Analogie eine Bedeutungsidentität oder aus Verdichtung eine automatische Freigabe zu erzeugen.
