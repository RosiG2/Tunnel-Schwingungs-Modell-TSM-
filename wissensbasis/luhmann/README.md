# Luhmann – Theorieatlas: öffentliche, versionierte Erkenntnisbasis

Dieser Ordner enthält die **ergänzende Wissensbasis** des eigenständigen Plugins **„Luhmann – Theorieatlas“**, herausgegeben von **Rosi Hach**. Er ist nicht die private Skill-Bibliothek des anderen Plugins **„Luhmann Lesehilfe & Forum“**. Beide bleiben organisatorisch und technisch getrennt.

## Wozu der Theorieatlas dient

Eine konkrete Frage über Gesellschaft, Organisation, Bildung oder Kommunikation kann über fünf redaktionelle Zugänge bearbeitet werden:

| Bibliothek | Aufgabe | Beispiel |
|---|---|---|
| A – Begriffe | Begriffe unterscheidungsscharf erklären und vernetzen | Warum ist eine Schule als Organisation nicht identisch mit Unterricht oder dem Erziehungssystem? |
| B – Quellen | Werkangaben und tatsächlich geprüfte Primärstellen trennen | Was ist an Luhmann 1982 geprüft, was zu 1992 nur bibliografisch nachgewiesen? |
| C – Erkenntnis | Beobachtungs-, Zusammenhangs- und Erklärungsgewinn sowie Beobachtungsverlust prüfen | Was macht „operative Geschlossenheit“ im Fall sichtbar? |
| D – Anwendungen | Fälle an mehreren Perspektiven untersuchen, Hypothesen von Daten trennen | Schulreform, Organisationsentscheidung, Politik/Recht oder Mensch–KI-Dialog |
| E – Forschung | Offene Fragen, negative Befunde und Revisionen dokumentieren | Welche Textprüfung oder Falluntersuchung steht noch aus? |

**Direkter Einstieg:** [`so-nutzt-du-den-theorieatlas.md`](entries/so-nutzt-du-den-theorieatlas.md).

## Wie die Daten gelesen werden

`index.json` ist das gemeinsame Register. Alle tatsächlich registrierten Inhalte liegen unter `entries/<id>.md`. Die fünf Bibliotheken sind redaktionelle Zugänge im **selben** Register, keine separaten Verzeichnisse. Das ist eine bewusste Kompatibilitätsentscheidung, weil der bestehende read-only-Cloudflare-Worker genau dieses Schema nutzt.

Im jeweiligen Eintrag ist angegeben, ob es sich um einen redaktionellen Arbeitsstand, eine punktuell belegte Textrekonstruktion, eine Hypothese oder ein Gedankenexperiment handelt. **Redaktioneller Arbeitsstand** ist kein Synonym für geprüfte Primärtextedition. Quellenlinks sind inhaltlich begrenzt zu verwenden: Ein bibliografischer Nachweis beweist nicht jede Theoriebehauptung.

## Nutzungsbeispiele

1. „Warum führen neue Schulpläne nicht automatisch zu besseren Unterrichtsgesprächen? Unterscheide Beobachtung und Erklärung.“
2. „Welche Luhmann-Aussagen zu Autopoiesis sind anhand der dokumentierten Quelle von 1982 geprüft?“
3. „Untersuche eine Organisationsentscheidung und zeige alternative Erklärungen.“
4. „Vergleiche politische und rechtliche Beobachtungen eines hypothetischen Konflikts.“
5. „Welche Forschungsfragen sind noch offen, und was hat sich seit dem ersten Redaktionsentwurf geändert?“

## Technische Zugänglichkeit

Der derzeitige MCP-Server bietet `luhmann_wissensindex` und `luhmann_wissenseintrag` als **lesende** Werkzeuge. Ein erster inhaltlicher Funktionstest in der ChatGPT-Desktop-App wurde am 06.11.2026 durch die Nutzerin berichtet; die unabhängig einsehbare Host-Tool-Aufrufspur und die negativen Reviewfälle stehen noch aus. Das Repository ist keine eigenständige dynamische Analyse-Engine. Für die Veröffentlichung von Änderungen sind redaktionelle Prüfung und ein manueller GitHub-Desktop-Push durch die Projektverantwortliche vorgesehen.

## Rechte und Quellen

Eigene redaktionelle Texte stehen unter der jeweils auf Repository-/Dateiebene ausgewiesenen Lizenz; Rechte an Originalwerken und verlinkten Quellen bleiben bei den Berechtigten. Der Atlas enthält keine vollständigen fremden Primärtexte. Für Zitate und Nachweise sind die Originalpublikationen heranzuziehen.

**Stand:** Arbeitsausgabe 2026-11-06. Der Inhaltsstand (`edition` in `index.json`) ist unabhängig von der Versionsnummer des installierten Plugins.
