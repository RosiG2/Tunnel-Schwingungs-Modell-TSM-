# Luhmann – Theorieatlas | integrierte Edition 0.4

Der öffentlich abrufbare Forschungs- und Leseatlas besteht aus fünf Bibliotheken (A–E), einer Einführung und einer Begriffs-/Anschlusslandkarte. Er verbindet systematische Rekonstruktion, Werkhinweise, methodische Gegenbeobachtung, konstruierte Fallanalysen und ein Revisionsregister. Fachliche Bewertung und Interpretation sind von der technischen Volltextsuche getrennt.

## Öffentlicher Stand

- **Edition:** `atlas-0.4-redaktion`, 8. November 2026
- **Umfang:** 30 registrierte Beiträge; 17 weiterentwickelte Bestandsbeiträge, 13 neue integrierte Texte
- **Start:** `entries/so-nutzt-du-den-theorieatlas.md`
- **Begriffsnavigation:** `entries/begriffs-und-anschlusslandkarte.md`
- **Verbindliche Eintragsliste:** `index.json`
- **Fachstatus:** redaktioneller Arbeitsstand, keine pauschale externe Begutachtung und keine pauschale Primärtextprüfung

## Bibliotheken

- **A – Begriffs- und Strukturatlas:** Grundbegriffe, Relationen, unterschiedliche Theorieebenen und Erklärungsgrenzen
- **B – Werk- und Quellenatlas:** bibliografische Werkanker, tatsächlich kontrollierte Primärpassagen und noch offene Lektüre
- **C – Erkenntnis- und Gegenbeobachtungsatlas:** C1 Beobachtungsgewinn, C2 Zusammenhangsgewinn, C3 Erklärungsgewinn, C4 Beobachtungsverlust sowie methodischer Perspektivenvergleich
- **D – Anwendungs- und Fallatlas:** explizit hypothetische Fälle und theorievergleichende Untersuchungen
- **E – Forschungs- und Revisionsregister:** offene Nachweise, Gegenprüfungen, Editionsgeschichte

## Technische Schnittstelle

Die vier lesenden Werkzeuge `luhmann_wissensindex`, `luhmann_themenrecherche`, `luhmann_wissenseintrag` und `luhmann_bezugspfad` bleiben unverändert. Der bestehende Cloudflare-Worker liest das Register und die Artikel unter diesem GitHub-Ordner dynamisch. Die inneren Artikeltexte werden im MCP-Abruf im Feld `article_markdown` ausgegeben. Weder das öffentliche Plugin noch der Worker-Code sind Bestandteil dieser Inhaltsedition.

Die Suche ist lexikalisch, begrenzt auf die registrierten Artikel und keine wissenschaftliche Evidenzbewertung. `related_ids` sind redaktionelle Verweiskanten, keine theoretischen Beweise. Die registrierten Dateien sind lesbare Markdown-Texte; eine Änderung des Registers ist ausschließlich gemeinsam mit vorhandenen, konsistenten Artikeldateien zu veröffentlichen.

## Editionshinweise

- Die vorhandenen 17 Artikel wurden argumentativ **bewahrt** und an den fachlich passenden Stellen mit Integrationsabschnitten verknüpft. Zwei zuvor nur textlich angekündigte Themen sind jetzt geklärt: `komplexitaet-und-kontingenz` ist registriert; Selbst-/Fremdreferenz ist ausdrücklich in `system-und-umwelt` und Nachbarartikeln erschlossen.
- Bibliografische Werkhinweise sind nicht als durchgehend geprüfte Primärzitate ausgegeben. Die beiden textlich eingesehenen Manuskriptanker zur doppelten Kontingenz und Moral sind als begrenzte Nachweise ausgewiesen.
- Die integrierte Edition ersetzt die Redaktion `atlas-0.3-redaktion`, ohne die stabilen Artikel-IDs zu verändern. Technische Altversionen und Review-Unterlagen bleiben getrennt.
