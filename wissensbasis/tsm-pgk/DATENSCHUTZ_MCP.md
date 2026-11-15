# Ergänzende Datenschutzinformationen – Tunnel-Schwingungs-Modell und PGK-Forschungsbrücke

**Stand: 15. November 2026**

Diese Informationen gelten für die externe MCP-Anbindung der öffentlichen **TSM–PGK-Forschungsbrücke**. Sie ergänzen die [allgemeinen Datenschutzinformationen für KI-Plugins und Assistenten](../../DATENSCHUTZ.md). Für die hier beschriebene PGK-Anbindung sind beide Texte gemeinsam zu lesen. Herausgeberin, Kontakt, allgemeine Betroffenenrechte und die Verarbeitung freiwilliger Supportanfragen werden in der allgemeinen Datenschutzerklärung erläutert.

## 1. Zweck und angebotene Funktionen

Die TSM–PGK-Forschungsbrücke ist über `https://tsm-pgk-public-essence-mcp.rosig2.workers.dev/mcp` erreichbar. Sie stellt einer unterstützten KI-Plattform öffentlich freigegebene PGK-Forschungsinformationen aus einem GitHub-Repository zur Verfügung. Die Werkzeuge ermöglichen insbesondere den Abruf von Forschungsständen, Modulen, Aussagen und Relationen, Quellenangaben, Modellbefunden, negativen Ergebnissen, offenen Fragen und explorativen Vergleichen.

Die Schnittstelle ist auf **lesende und prüfende Funktionen** beschränkt. Sie ändert keine GitHub-Forschungsdateien und nimmt keine Buchungen, Käufe oder Änderungen an persönlichen Nutzerkonten vor. Für den regulären öffentlichen Zugriff ist kein eigenes Nutzerkonto bei der Herausgeberin vorgesehen.

## 2. Welche Angaben an die Forschungsbrücke übertragen werden

Eine Übertragung an den Cloudflare-Worker erfolgt, wenn die KI-Plattform ein PGK-Werkzeug tatsächlich aufruft. Dabei werden die für den jeweiligen Aufruf verwendeten Argumente übertragen. Hierzu können insbesondere gehören:

- Suchbegriffe, Forschungsfragen oder Teile einer Anfrage, soweit sie als Suchargument verwendet werden;
- Modul-, Aussage-, Quellen-, Forschungsdatensatz- und Dokumentkennungen;
- Filter, Seitenbegrenzungen, Vergleichsparameter und angeforderte Forschungsrevisionen;
- bei einer freiwilligen Nutzung der Funktion `pgk_validate_draft` strukturierte Entwurfsinhalte, die zur formalen Plausibilitäts- und Referenzprüfung übergeben werden.

Eine solche Werkzeugabfrage ist von der Verarbeitung des gesamten Gesprächs durch die verwendete KI-Plattform zu unterscheiden. **Allein durch die Nutzung oder Aktivierung des Plugins wird nicht automatisch der vollständige private Chat an die Forschungsbrücke oder GitHub übertragen.** Einzelne übermittelte Werkzeugargumente können jedoch Ausschnitte aus Nutzereingaben enthalten. Auch personenbezogene Informationen können darin enthalten sein, wenn sie in die Argumente aufgenommen werden.

Bitte übermitteln Sie an diese öffentlich erreichbare Forschungsbrücke **keine Passwörter, vertraulichen Forschungsoriginale, unveröffentlichten personenbezogenen Informationen oder anderen sensiblen Angaben**. Dies gilt besonders für die Entwurfsprüffunktion.

Beim technischen Verbindungsaufbau können außerdem Informationen wie angefragter Endpunkt, Zeitpunkt, HTTP-Methode, Antwortstatus und Verbindungs- oder Sicherheitsmerkmale verarbeitet werden. Die Verbindung wird bei einer Werkzeugnutzung über eine KI-Plattform nicht zwingend direkt vom Endgerät der nutzenden Person hergestellt.

## 3. Verarbeitung, Datenquellen und Weitergabe

Die Forschungsbrücke wird mit **Cloudflare Workers** betrieben. Der Worker verarbeitet die erhaltenen Werkzeugparameter zur Auswahl und Aufbereitung freigegebener Forschungsinformationen und übermittelt die Werkzeugantwort an die aufrufende KI-Plattform.

Als Datenquelle dienen veröffentlichte Forschungsdateien auf **GitHub**. Der Worker lädt hierfür ein Veröffentlichungsmanifest und ein zugehöriges Datenpaket aus einer festgelegten GitHub-Revision. Die Integrität des freigegebenen Datenpakets wird technisch überprüft. Die eingegebene Suchformulierung wird nach dem veröffentlichten Anwendungscode nicht als eigenständige Suchanfrage an GitHub weitergeleitet. Beim Abruf der öffentlichen Quelldateien können GitHub gleichwohl technische Verbindungsdaten des Workers erreichen.

Der Worker verarbeitet Such- und Prüfargumente innerhalb des Aufrufs. Die öffentliche Forschungsdatenbasis enthält keine für diesen Zweck angelegten privaten Nutzerchats. Technische Caches im Anwendungscode betreffen öffentliche Publikationsdateien und Forschungsrevisionen, nicht das dauerhafte Speichern individueller Gesprächsverläufe.

An der Bereitstellung beteiligt sind insbesondere die jeweils genutzte **KI-Plattform**, **Cloudflare** als Betreiber der Worker-Infrastruktur und **GitHub** als Bereitsteller der öffentlichen Forschungsdateien. Die jeweils eigenen Verarbeitungsvorgänge dieser Dienste richten sich nach den dafür geltenden Informationen und Vereinbarungen.

## 4. Protokollierung und Speicherdauer

Der veröffentlichte Worker-Anwendungscode enthält keine eigene Datenbank zur Speicherung vollständiger Chatverläufe und keine eigens eingebauten Ausgaben persönlicher Suchformulierungen in ein Anwendungsprotokoll. Die Nutzung des Workers ist jedoch nicht gleichbedeutend mit einem protokollierungsfreien Betrieb der beteiligten Plattformen.

Cloudflare kann für den sicheren technischen Betrieb, die Abwehr missbräuchlicher Zugriffe, die Fehleranalyse und die Dienstbereitstellung Verbindungs-, Sicherheits- und gegebenenfalls Nutzungsmetadaten verarbeiten. Umfang und Aufbewahrung solcher Daten hängen von den tatsächlich verwendeten Diensten und Einstellungen sowie den jeweiligen Vertrags- und Datenschutzbedingungen ab. Aus dem öffentlich einsehbaren Anwendungscode allein lassen sich weder der Aktivierungszustand sämtlicher Cloudflare-Observability- und Exportfunktionen noch bestimmte Speicherdauern ableiten. Es wird deshalb **keine vollständige Unterdrückung von Cloudflare-Protokollen und keine feste Null-Tage-Aufbewahrung zugesagt**.

Die Verarbeitung von Gesprächen und hochgeladenen Materialien innerhalb der KI-Plattform ist davon unabhängig. Für deren Speicherung und Löschmöglichkeiten gelten die dort bereitgestellten Datenschutzhinweise und Kontofunktionen. Für freiwillige Kontaktanfragen gelten die Regelungen der [allgemeinen Datenschutzerklärung](../../DATENSCHUTZ.md).

## 5. Rechtsgrundlagen und Verantwortlichkeit

Soweit die Herausgeberin für die Verarbeitung durch die von ihr betriebene Forschungsbrücke datenschutzrechtlich verantwortlich ist, dient die Verarbeitung der erforderlichen Werkzeugargumente und technischen Verbindungsdaten der Bereitstellung eines frei zugänglichen wissenschaftlichen Informationsdienstes sowie seinem sicheren Betrieb. Als Rechtsgrundlage kommt hierfür, soweit einschlägig, **Art. 6 Abs. 1 Buchst. f DSGVO** (berechtigtes Interesse) in Betracht. Für gewöhnliche Forschungsabfragen sind personenbezogene Angaben nicht erforderlich und sollen nicht in Werkzeugargumenten enthalten sein.

Die Datenschutzverantwortung für Gesprächsverläufe, Konten und weitere Funktionen der genutzten KI-Plattform sowie für eigenständige Verarbeitungen anderer Anbieter wird dadurch nicht pauschal übernommen. Informationen zu Auskunfts-, Berichtigungs-, Löschungs- und Widerspruchsrechten sowie die Kontaktdaten stehen in den [allgemeinen Datenschutzinformationen](../../DATENSCHUTZ.md).

## 6. Internationale Datenverarbeitung und Dienstleister

Cloudflare betreibt eine international verteilte Infrastruktur. Ebenso können die genutzte KI-Plattform und GitHub internationale Datenübermittlungen vorsehen. Für die verwendete `workers.dev`-Adresse wird keine ausschließlich innerhalb der Europäischen Union stattfindende Verarbeitung zugesichert.

Cloudflare stellt für die datenschutzrechtliche Einordnung seines Angebots ein [Data Processing Addendum](https://www.cloudflare.com/cloudflare-customer-dpa/) und [Vertragsbedingungen](https://www.cloudflare.com/terms/) zur Verfügung. Ob und in welchem Umfang einzelne Vertragsregelungen im jeweiligen Kontoverhältnis gelten, richtet sich nach dem tatsächlich bestehenden Vertrag und der datenschutzrechtlichen Rollenverteilung. Die Vereinbarungen anderer beteiligter Dienste sind gesondert zu betrachten.

## 7. Nutzerkontrollen und Grenzen

Die PGK-Forschungsbrücke ist auf öffentlich freigegebene Forschungsinformationen ausgerichtet. Die technische Möglichkeit, einen Entwurf formal prüfen zu lassen, bedeutet weder eine Veröffentlichung dieses Entwurfs im GitHub-Repository noch eine wissenschaftliche Freigabe. Sie ist kein geeigneter Übertragungsweg für vertrauliche oder nicht zur Weitergabe bestimmte Materialien.

Die Plattform stellt gegebenenfalls Möglichkeiten bereit, eine App- oder Plugin-Verbindung zu verwalten beziehungsweise zu trennen. Das Trennen der Verbindung führt nicht automatisch dazu, dass bei beteiligten Dienstleistern bereits angefallene technische Daten rückwirkend gelöscht werden.

Forschungsinformationen der PGK können theoretische Hypothesen, begrenzte Modellnachweise, negative Ergebnisse und explorative Vergleiche umfassen. Die Veröffentlichung eines solchen Ergebnisses ist nicht mit einer empirischen Bestätigung der Natur gleichzusetzen.

## 8. Weiterführende Informationen

- [Allgemeine Datenschutzinformationen](../../DATENSCHUTZ.md)
- [Support und Kontakt](../../SUPPORT.md)
- [Allgemeine Nutzungsbedingungen](../../NUTZUNGSBEDINGUNGEN.md)
- [Öffentliche PGK-Forschungswissensbasis](./README.md)
- [Beschreibung der PGK-MCP-Forschungsbrücke](./worker/README.md)
- [Cloudflare – Datenschutzhinweise](https://www.cloudflare.com/privacypolicy/)
- [Cloudflare – Data Processing Addendum](https://www.cloudflare.com/cloudflare-customer-dpa/)
- [GitHub – Datenschutzhinweise](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement)

Diese Informationen werden bei wesentlichen Änderungen der Werkzeugfunktionen, Datenübermittlungen und Betriebsweise angepasst.
