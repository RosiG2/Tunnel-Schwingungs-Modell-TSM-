# Ergänzende Datenschutzinformationen – Luhmann – Theorieatlas und MCP-Wissensbrücke

**Stand: 7. November 2026**

Diese Ergänzung gilt für die externe, lesende MCP-Anbindung des Plugins **Luhmann – Theorieatlas**. Sie ist zusammen mit den [allgemeinen Datenschutzinformationen](../../DATENSCHUTZ.md) zu lesen. Bei Abweichungen in der Beschreibung der hier genannten MCP-Verarbeitung ist diese Ergänzung maßgeblich. Herausgeberin, Kontakt, allgemeine Betroffenenrechte und die Verarbeitung freiwilliger Supportanfragen sind in der allgemeinen Erklärung beschrieben.

## 1. Zweck und Funktionsweise

Die MCP-Wissensbrücke unter `https://luhmann-knowledge-mcp.rosig2.workers.dev/mcp` ermöglicht den Abruf eines öffentlichen wissenschaftlich-redaktionellen Artikelregisters, einzelner Beiträge, die thematische Recherche in registrierten Beiträgen und die Anzeige dokumentierter Querverweise. Sie wird auf **Cloudflare Workers** betrieben und liest ausschließlich veröffentlichte Atlasdateien aus einem öffentlichen GitHub-Repository.

Die Brücke ist **lesend**: Sie ändert keine GitHub-Dateien, tätigt keine Käufe und führt keine Aktionen in persönlichen Konten aus. Für die MCP-Nutzung ist nach der derzeitigen Serverkonfiguration kein eigenes Nutzerkonto bei der Herausgeberin und keine persönliche Anmeldung am Worker erforderlich.

## 2. Welche Angaben an die Wissensbrücke gelangen

Wenn die verwendete KI-Plattform ein MCP-Werkzeug aufruft, werden dessen konkrete Eingabeargumente an den Cloudflare-Worker übermittelt:

- **Registerabruf (`luhmann_wissensindex`):** kein inhaltliches Eingabeargument;
- **Artikelabruf (`luhmann_wissenseintrag`):** eine Kennung eines registrierten Artikels;
- **Themensuche (`luhmann_themenrecherche`):** eine Suchformulierung mit maximal 180 Zeichen und gegebenenfalls die gewünschte Zahl von Treffern;
- **Bezugspfad (`luhmann_bezugspfad`):** eine Artikelkennung und gegebenenfalls die Suchtiefe.

Die KI-Plattform entscheidet im Rahmen ihrer Funktionen, welche zur Bearbeitung der Frage erforderlichen Argumente sie an das Werkzeug übergibt. **Es wird nicht allein durch die Installation des Plugins der gesamte private Chat an die Herausgeberin oder an GitHub übertragen.** Eine an den Worker übermittelte Suchformulierung kann jedoch Teile einer Nutzereingabe enthalten, darunter unter Umständen personenbezogene Angaben, wenn solche in die Suche aufgenommen werden.

Bei einem Verbindungsaufbau können ferner technische Metadaten verarbeitet werden, etwa Zeitpunkt, angefragter Endpunkt, HTTP-Methode, Status, Verbindungs- und Sicherheitsinformationen sowie die IP-Adresse des tatsächlich anfragenden Systems. Bei einem über ChatGPT ausgeführten Werkzeugaufruf ist dieses System nicht notwendig das Endgerät der Nutzerin oder des Nutzers.

## 3. Verarbeitung und Weitergabe

Der Worker verarbeitet die Werkzeugargumente, um die passende Antwort aus dem veröffentlichten Artikelbestand zu berechnen und an die aufrufende Plattform zurückzugeben. Der derzeit veröffentlichte Anwendungscode enthält **keine eigene Datenbank zur Speicherung von individuellen Suchanfragen oder Chatverläufen** und keine eigens programmierten `console.log`-Ausgaben von Suchtexten.

Die öffentlichen Artikel und das Register werden serverseitig von `raw.githubusercontent.com` bezogen. Die frei formulierte Suchfrage wird nach der derzeitigen Implementierung **nicht als Suchargument oder URL-Parameter an GitHub weitergereicht**. GitHub verarbeitet im Zuge der Dateiabrufe gleichwohl technische Informationen über die Verbindung des anfragenden Systems. Die öffentlichen Quelldokumente können unabhängig davon über GitHub direkt eingesehen werden.

Empfänger bzw. beteiligte Dienste sind insbesondere die **genutzte KI-Plattform** (zur Ausführung der Anfrage), **Cloudflare** (Hosting und technischer Betrieb des MCP-Servers) und **GitHub** (Bereitstellung der veröffentlichten Quelldateien). Die allgemeinen Datenverarbeitungen dieser Anbieter richten sich nach deren jeweils geltenden Datenschutzhinweisen und den anwendbaren Vereinbarungen.

## 4. Protokolle, Speicherung und Aufbewahrung

Der veröffentlichte Worker-Anwendungscode enthält keine eigene Datenbank für Chatverläufe oder individuelle Suchanfragen und keine eigens programmierten `console.log`-Ausgaben von Suchtexten. **Nach Angabe der Betreiberin vom 7. November 2026 ist die Funktion „Workers Logs“ unter Cloudflare Workers → Observability für `luhmann-knowledge-mcp` deaktiviert.** Für diesen Worker ist damit die Sammlung über das Produkt *Workers Logs* nach dem dokumentierten Betriebsstand nicht eingeschaltet. Die tarifabhängigen Aufbewahrungsfristen dieses **deaktivierten** Produkts werden daher nicht als tatsächliche Speicherfristen des Theorieatlas angegeben.

**Zusätzliche Exporte (Betreiberprüfung vom 7. November 2026):** Nach Kontrolle des Cloudflare-Dashboards ist **Logpush für das betreffende Konto nicht aktiviert beziehungsweise nicht abonniert**. Für **OpenTelemetry-Exporte sind keine Ziele eingerichtet**; zudem werden **Logpush und OpenTelemetry in den Einstellungen des Workers als deaktiviert** angezeigt. Somit wurde bei dieser Prüfung **kein von der Betreiberin konfigurierter Export über Logpush oder OpenTelemetry** festgestellt. Diese Angaben beruhen auf der Kontrolle durch die Betreiberin und nicht auf einer unabhängigen Prüfung sämtlicher Cloudflare-Kontoeinstellungen per API. Im veröffentlichten Worker-Code sind außerdem keine eigenen Exportziele und keine Tail-Worker-Konfiguration enthalten; eine gesonderte, außerhalb des veröffentlichten Quellcodes eingerichtete Anbindung wird dadurch allein nicht generell ausgeschlossen.

**Davon zu unterscheiden sind** technisch erforderliche Verbindungs-, Sicherheits- und gegebenenfalls aggregierte Nutzungsdaten, die Cloudflare unabhängig von *Workers Logs*, Logpush oder OpenTelemetry verarbeiten kann. Aus den deaktivierten Funktionen folgt weder die Aussage „Cloudflare speichert keinerlei Daten“ noch eine Null-Tage-Aufbewahrungsfrist. Cloudflare kann außerdem aggregierte Worker-Metriken bereitstellen. Die konkrete Speicher- und Löschpraxis der Cloudflare-eigenen technischen Daten wird hier nicht als von der Herausgeberin steuerbar dargestellt.

Der Worker übermittelt die jeweiligen Werkzeugantworten an die aufrufende KI-Plattform. Der öffentlich bereitgestellte Atlasbestand auf GitHub ist kein Speicherort für private Chatverläufe. Für Gesprächsverläufe und Dateien innerhalb der KI-Plattform gelten deren eigenen Speicher-, Lösch- und Kontoeinstellungen; für freiwillige E-Mail-Anfragen die allgemeinen Datenschutzinformationen.

Die Angabe „Workers Logs deaktiviert“ beschreibt den von der Betreiberin kontrollierten Stand vom 7. November 2026. Sie wird bei wesentlichen Änderungen der produktiven Konfiguration aktualisiert.

## 5. Rechtsgrundlage und berechtigte Interessen

Soweit die Herausgeberin für den Betrieb der Wissensbrücke datenschutzrechtlich verantwortlich ist, erfolgt die zur Bearbeitung des angeforderten Werkzeugaufrufs erforderliche Verarbeitung auf Grundlage von **Art. 6 Abs. 1 Buchst. f DSGVO**: berechtigtes Interesse an der Bereitstellung eines funktionierenden, frei zugänglichen, lesenden wissenschaftlichen Informationsdienstes und an dessen sicherem technischen Betrieb. Die Verarbeitung ist auf die jeweiligen Werkzeugparameter und erforderliche technische Vorgänge begrenzt. Personenbezogene Inhalte sind für eine gewöhnliche Atlasrecherche nicht erforderlich und sollen nicht in Suchanfragen aufgenommen werden.

Die unabhängig davon stattfindende Datenverarbeitung durch den Anbieter der KI-Plattform oder durch Drittanbieter für eigene Zwecke wird durch diese Erklärung nicht stellvertretend rechtlich bewertet.

## 6. Internationale Verarbeitung, Cloudflare-Vertrag und Dienstleister

Cloudflare betreibt eine weltweit verteilte Infrastruktur. **Eine ausschließlich innerhalb der Europäischen Union stattfindende Verarbeitung wird für die hier verwendete `workers.dev`-Adresse nicht zugesagt.** Auch GitHub und die verwendete KI-Plattform können Daten international verarbeiten. Die datenschutzrechtlichen Rollen und die jeweils einschlägigen Vertragsgrundlagen sind für jeden Dienst getrennt zu betrachten.

**Cloudflare als Auftragsverarbeiter:** Soweit Cloudflare im Rahmen des Workers personenbezogene Daten im Auftrag der Betreiberin verarbeitet, ist das [Cloudflare Data Processing Addendum (DPA)](https://www.cloudflare.com/cloudflare-customer-dpa/) maßgeblich. Das DPA beschreibt unter anderem die Datenverarbeitung zu Zwecken der Diensterbringung, technische und organisatorische Maßnahmen, Unterauftragsverarbeiter und Regelungen zu Übermittlungen außerhalb des EWR. Nach dem veröffentlichten [Self-Serve Subscription Agreement](https://www.cloudflare.com/terms/), Abschnitt 6.1, ist das DPA **ausdrücklich durch Verweis Bestandteil des Self-Serve-Vertrags**, sofern personenbezogene Daten unter die dort beschriebenen Voraussetzungen fallen. Eine zusätzliche handschriftliche Unterzeichnung ist bei dieser Vertragsform grundsätzlich nicht vorgesehen. Die hier geprüfte öffentlich veröffentlichte DPA-Fassung ist **Version 6.4 vom 3. April 2026** (Prüfdatum 7. November 2026).

Die vorgenannte Einbeziehung gilt **unter der Voraussetzung, dass das verwendete Cloudflare-Konto dem üblichen Self-Serve-Vertrag unterliegt und keine abweichende individuelle Vereinbarung geschlossen wurde**. Die kontospezifischen Vertragsunterlagen wurden bei der Erstellung dieser Erklärung nicht unabhängig eingesehen; eine besondere individuelle Annahme oder ein konkretes historisches Vertragsabschlussdatum wird daher nicht behauptet.

**Internationale Transfers:** Das DPA sieht für einschlägige internationale Übermittlungen unter anderem EU-Standardvertragsklauseln (insbesondere Modul 2, wenn die Betreiberin Verantwortliche ist) sowie Regelungen zum EU-US Data Privacy Framework vor. Diese Vertragsmechanismen sind **kein Nachweis ausschließlich europäischer Verarbeitung**. Cloudflare veröffentlicht außerdem eine [Liste seiner Unterauftragsverarbeiter](https://www.cloudflare.com/gdpr/subprocessors/).

Für die Verarbeitung innerhalb der KI-Plattform und für die Bereitstellung öffentlich zugänglicher Quellen durch GitHub gelten deren jeweiligen Datenschutzinformationen und Vertragsbedingungen. Die Cloudflare-Vereinbarung ersetzt diese nicht.

## 7. Grenzen und Nutzerkontrollen

Für die normale Nutzung der Wissensbrücke sind keine eigenen Kontodaten bei der Herausgeberin nötig. Das Plugin fordert keine Passwörter, API-Schlüssel, Zahlungsdaten oder amtlichen Identifikationsnummern an. Bitte geben Sie solche Informationen – ebenso wie sensible persönliche Einzelheiten – nicht in Atlas-Suchanfragen ein.

Die Verbindung kann über die jeweils unterstützten Plugin- und Verbindungseinstellungen der KI-Plattform verwaltet oder getrennt werden. Eine rückwirkende Löschung der bei einem anderen Anbieter bereits verarbeiteten technischen Daten kann dadurch nicht pauschal zugesagt werden. Für Auskunft, Berichtigung, Löschung und weitere Rechte wenden Sie sich hinsichtlich der hier beschriebenen Verarbeitung an den in der [allgemeinen Erklärung](../../DATENSCHUTZ.md) angegebenen Kontakt; für Plattformkonten und dort gespeicherte Chats an den jeweiligen Plattformanbieter.

## 8. Weiterführende Informationen

- [Technische Funktionsbeschreibung der Wissensbrücke](./TECHNIK_MCP.md)
- [Cloudflare – Datenschutzhinweise](https://www.cloudflare.com/privacypolicy/)
- [Cloudflare – Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Cloudflare – Logpush](https://developers.cloudflare.com/logs/logpush/)
- [Cloudflare – OpenTelemetry Export](https://developers.cloudflare.com/workers/observability/opentelemetry-export/)
- [Cloudflare – Tail Workers](https://developers.cloudflare.com/workers/observability/logs/tail-workers/)
- [Cloudflare – Data Processing Addendum](https://www.cloudflare.com/cloudflare-customer-dpa/)
- [GitHub – Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)
- [OpenAI – EU-Datenschutzrichtlinie](https://openai.com/policies/eu-privacy-policy/)

Die Angaben werden bei wesentlichen Änderungen des Datenflusses, der Werkzeugfunktionen oder der Betriebsweise überprüft und erforderlichenfalls aktualisiert.
