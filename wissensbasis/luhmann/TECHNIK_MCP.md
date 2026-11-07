# Die MCP-Wissensbrücke des Luhmann – Theorieatlas

Die Wissensbrücke erweitert das wissenschaftliche Analyseangebot um den lesenden Zugriff auf das öffentliche, fortlaufend bearbeitete Artikelregister. Der Quellcode ist unter [`worker/`](worker/) dokumentiert. Die wissenschaftlichen Beiträge stehen unabhängig davon im [`index.json`](index.json) und im Verzeichnis [`entries/`](entries/).

## Abruf- und Recherchefunktionen

Die Serverimplementierung definiert vier lesende MCP-Werkzeuge:

| Werkzeug | Funktion | Quelle |
|---|---|---|
| `luhmann_wissensindex` | Aktuellen Registerbestand und Editionsangabe lesen | `index.json` |
| `luhmann_wissenseintrag` | Einen registrierten Artikel nach seiner ID lesen | `entries/<id>.md` |
| `luhmann_themenrecherche` | Registrierte Artikel über eine nachvollziehbare, lexikalische Relevanzbewertung erschließen; Fundstellen und redaktionellen Nachweisstatus ausgeben | Register und Artikeltexte |
| `luhmann_bezugspfad` | Explizite `related_ids`-Verweise zwischen Artikeln beidseitig und höchstens zweistufig erschließen | Register |

**Betriebsnachweis vom 7. November 2026:** Die beiden zusätzlichen Werkzeuge `luhmann_themenrecherche` und `luhmann_bezugspfad` haben über den öffentlich angebundenen MCP Inspector produktive Ergebnisse geliefert. Die registrierten 17 Einträge stammen aus `atlas-0.3-redaktion`. Der produktive Stand ist unabhängig davon jederzeit anhand der Werkzeugliste und tatsächlicher Aufrufe am MCP-Endpunkt zu prüfen. Die Werkzeugbereitstellung in ChatGPT Work war beim letzten dokumentierten Test noch nicht verfügbar; dies ist kein Beleg für einen Ausfall des öffentlichen MCP-Servers. Einzelheiten stehen in [`MCP_ABNAHME_2026-11-07.md`](MCP_ABNAHME_2026-11-07.md).

## Wissenschaftliche Reichweite

Die Recherche durchsucht ausschließlich die jeweils im Register angegebenen Beiträge und ist keine freie Websuche. Das lexikalische Ranking zeigt Textübereinstimmungen, keine semantische Äquivalenz und keine Quellenvalidierung. Die Bezugspfade machen redaktionelle Lesebeziehungen sichtbar; aus einem Verweis folgt keine theoretische oder empirische Bestätigung. Quellenkritik und Interpretation erfolgen getrennt durch den Theorieatlas.

## Datengrundlage und technische Grenzen

Die Brücke liest öffentliche Markdown-Dateien und das öffentliche JSON-Register unter einem serverseitig konfigurierten GitHub-Raw-Stamm. Die Suche nimmt eine frei formulierte Suchfrage als MCP-Werkzeugparameter entgegen, die an den Cloudflare-Worker übermittelt wird; sie wird nicht als Suchquery an GitHub weitergereicht. Erforderliche Angaben zu Protokollierung und Aufbewahrung müssen vor einer öffentlichen App-Einreichung separat anhand der Betreiberkonfiguration geklärt werden. Der aktuelle Volltextpfad unterstützt höchstens 35 registrierte Artikel. Bei erheblich wachsendem Bestand wird ein indexgestützter Suchdienst erforderlich.

## Pflege

Die Registeredition ist unabhängig von der Plugin-Version und von der Codeversion des Cloudflare-Workers. Artikel und Links werden in GitHub gepflegt; die Worker-Bereitstellung erfolgt über den Cloudflare-Deployment-Prozess. Repository-Push und Cloudflare-Deployment sind nur dann gekoppelt, wenn eine entsprechende Build-Integration tatsächlich eingerichtet wurde.
