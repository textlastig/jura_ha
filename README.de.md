# JURA-Kaffeevollautomaten für Home Assistant

[English](README.md) | **Deutsch**

Custom-Integration für [Home Assistant](https://www.home-assistant.io/), die JURA-Kaffeevollautomaten über das Bluetooth-Modul [JURA Smart Connect](https://us.jura.com/en/homeproducts/accessories/SmartConnect-Main-72167) einbindet: Statistik, Wartungsstand und Meldungen auslesen und auf Wunsch Produkte zubereiten.

Dies ist ein Fork von [AlexxIT/Jura](https://github.com/AlexxIT/Jura). Er führt Verbesserungen aus offenen Pull Requests und anderen Forks zusammen und ergänzt eine Option, die Maschine nur auszulesen.

![](demo.png)

## Was dieser Fork gegenüber dem Original ändert

| Änderung | Herkunft |
|---|---|
| Sauberes Entladen, erneuter Einrichtungsversuch statt Abbruch, aktuelles Bluetooth-Gerät bei jeder Verbindung, aktive Suche (das Modell steht nur in der Scan-Antwort) | [madAndroid, AlexxIT/Jura#77](https://github.com/AlexxIT/Jura/pull/77) |
| Sensoren „Descaling Needed“ und „Descaling Soon“, Wartungszähler und Wartungsstand in Prozent, Einrichtung bei ausgeschalteter Maschine mit den letzten Werten | [Andrei Marinache, AlexxIT/Jura#41](https://github.com/AlexxIT/Jura/pull/41) |
| Sensor „No Beans“, richtiger Schlüssel im Statistikbefehl, weniger Log-Rauschen | [tidalf, AlexxIT/Jura#59](https://github.com/AlexxIT/Jura/pull/59) |
| Option **Nur auslesen, keine Steuerung**, Entitätsnamen auf Deutsch und Englisch, Produkt- und Meldungsnamen wie in der JURA-App, Milchsystem-Meldungen nur bei Maschinen mit Milchsystem | neu in diesem Fork |

Die Steuerung bleibt vollständig enthalten und ist Standard. Die Entitäts-IDs sind dieselben wie beim Original; wer umsteigt, behält Verlauf und Statistik.

## Getestete Maschinen

Laut Original: [D4](https://github.com/AlexxIT/Jura/issues/49), [E4](https://github.com/AlexxIT/Jura/issues/47), [E6](https://github.com/AlexxIT/Jura/issues/13), E8, ENA8 (mit Tasten), [S8](https://github.com/AlexxIT/Jura/issues/20), [Z8](https://github.com/AlexxIT/Jura/issues/15). Dieser Fork läuft mit einer **WE6**. Andere Modelle sollten gehen, solange ihre Maschinendatei in `resources.zip` steht.

## Installation

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=textlastig&repository=jura_ha&category=Integration)

HACS bzw. Marketplace › Menü › *Benutzerdefinierte Repositories* › URL `https://github.com/textlastig/jura_ha`, Typ *Integration* › Hinzufügen › Herunterladen. Danach Home Assistant neu starten.

Ohne HACS: den Ordner `custom_components/jura` aus dem [neuesten Release](https://github.com/textlastig/jura_ha/releases/latest) nach `custom_components` im Konfigurationsordner kopieren.

**Umstieg vom Original:** Original und Fork nutzen beide die Domain `jura`, es darf nur eine davon installiert sein. Das Original in HACS entfernen, den Fork installieren, neu starten. Der vorhandene Eintrag läuft weiter, Entitäten und IDs bleiben.

## Einrichtung

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jura)

1. Die Bluetooth-Integration von Home Assistant einrichten.
2. *Einstellungen › Geräte & Dienste › Integration hinzufügen › JURA Coffee Machines*, MAC-Adresse wählen.

Für die erste Einrichtung muss die Maschine an sein. Steht keine MAC-Adresse zur Auswahl, sieht Home Assistant gerade keine Maschine: Ist sie an, funktioniert Bluetooth (verbindet sich die JURA-App?) und ist der Empfänger nah genug? Maschinen mit PIN-Schutz werden nicht unterstützt.

Danach darf die Maschine aus sein, auch beim Neustart von Home Assistant: Die Integration merkt sich Modell und Schlüssel und zeigt die letzten Werte, bis die Maschine wieder erreichbar ist.

### Option „Nur auslesen, keine Steuerung“

*Einstellungen › Geräte & Dienste › JURA Coffee Machines › Konfigurieren.* Standard ist aus.

Eingeschaltet legt die Integration nur Sensoren und Binärsensoren an. Tasten (Zubereiten, Statistik aktualisieren), Auswahlen, Zahlen und der Verbindungsschalter werden aus Home Assistant entfernt. Ausschalten legt sie mit denselben IDs wieder an. Sinnvoll, wenn niemand über Home Assistant Kaffee machen soll, etwa bei Sprachassistenten oder Dashboards für alle.

## Entitäten

| Art | Entitäten |
|---|---|
| Sensoren | Bezüge gesamt und je Produkt (z. B. „Kaffee Spezial“ 14 662 Bezüge, „2 x Kaffee“), Meldungen (`ok`/`alert` mit Liste der aktiven Meldungen) |
| Diagnose | Wartungszähler (Reinigung, Filterwechsel, Entkalken, Kaffeespülung, soweit die Maschine sie hat), Wartungsstand in Prozent, Verbindung |
| Binärsensoren | Restwasserschale fehlt, Kaffeesatzbehälter fehlt, Wassertank füllen, Kaffeesatzbehälter leeren, Restwasserschale leeren, Bohnen füllen, Gerät reinigen, Filter wechseln, Gerät entkalken, Gerät bald entkalken; bei Maschinen mit Milchprodukten zusätzlich Milchsystem spülen, Milchsystem reinigen |
| Steuerung | Kaffeespezialität (Namen wie in der JURA-App), Mahlwerk-Verhältnis (z. B. „50% / 50%“), Kaffeestärke, Temperatur (Niedrig, Normal, Hoch), Mengen (Wasser und Bypass in ml, Milch, Milchschaum und Milchpause in Sekunden), Taste Zubereiten, Taste Statistik aktualisieren, Verbindungsschalter |

Die Namen erscheinen in der Sprache von Home Assistant (Deutsch oder Englisch), die Entitäts-IDs sind davon unabhängig (`<gerät>_<mac>_<attribut>`). Produkte und Meldungen heißen wie in der JURA-App J.O.E. und am Display der Maschine: Die Maschinendatei nennt zu jedem Produkt eine Textnummer, die Namen dazu stammen aus der App (Version 4.6.16). Welche Entitäten erscheinen, hängt von der Maschinendatei des Modells ab. Statistik und Meldungen werden jede Minute gelesen, solange die Maschine an ist.

## Bluetooth

Ein guter Bluetooth-Empfänger ist wichtig, siehe die [Liste von Home Assistant](https://www.home-assistant.io/integrations/bluetooth/). AlexxIT hatte mit fünf Adaptern (*Unbranded CSR clone detected*) keine stabile Verbindung, erst ein Adapter mit `CSR8510A10` lief zuverlässig.

Gut geht ein [ESPHome-Bluetooth-Proxy](https://esphome.io/components/bluetooth_proxy.html) mit `active: true` nah an der Maschine, zum Beispiel ein M5Stack Atom Lite. Die Maschine sendet ihr Modell nur in der Scan-Antwort; ein Empfänger, der nur passiv mithört, reicht für die Einrichtung nicht.

## WLAN

Das [WLAN-Modul](https://us.jura.com/en/homeproducts/accessories/WiFi-Connect-24160) wird nicht unterstützt und ist auch nicht geplant.

## Dank

- **[AlexxIT](https://github.com/AlexxIT)** für die Integration, das Protokoll und die jahrelange Pflege, ohne die es diesen Fork nicht gäbe.
- **[madAndroid](https://github.com/madAndroid)** (Andrew Stangl) für die Fixes zu Einrichtung, Verbindung und aktiver Suche.
- **[Andrei Marinache](https://github.com/andrei-marinache)** für Entkalken, Wartungszähler und die Einrichtung bei ausgeschalteter Maschine.
- **[tidalf](https://github.com/tidalf)** (Cyril Leclerc) für „No Beans“ und die Korrekturen am Statistikbefehl.
- Allen, die im Original-Repo Maschinen getestet, Protokolle mitgeschnitten und Fehler gemeldet haben.

Zusammengeführt, ergänzt und getestet wurde der Fork von [textlastig](https://github.com/textlastig) mit Unterstützung von [Claude](https://claude.com/claude-code) (Anthropic). Übernommene Commits tragen ihre ursprünglichen Autoren, nachgebaute Teile nennen sie als Co-Autoren.

## Nützliche Links

- https://lunarius.fe80.eu/blog/tag/bluetooth.html
- https://github.com/Jutta-Proto/protocol-cpp
- https://github.com/Jutta-Proto/protocol-bt-cpp
- https://github.com/franfrancisco9/Jura-Python-BT

## Lizenz

Der Code steht unter der [MIT-Lizenz](LICENSE), wie das Original von AlexxIT. Die Beiträge aus den Pull Requests AlexxIT/Jura#41, #59 und #77 wurden in das MIT-lizenzierte Original-Repo eingereicht und stehen damit unter derselben Lizenz. Die Rechte an den übernommenen Beiträgen liegen bei ihren Autoren.

**Ausgenommen:** `custom_components/jura/core/resources.zip` enthält die Maschinendateien von JURA (Produkte, Einstellungen und Meldungen je Modell). Sie stammen von JURA, fallen nicht unter die MIT-Lizenz und sind nur zum Betrieb dieser Integration enthalten, wie im Original. Dasselbe gilt für die Produkt-, Einstellungs- und Meldungsnamen in `translations/*.json` und `core/texts.json`, die aus der JURA-App J.O.E. übernommen sind.

JURA und Smart Connect sind Marken der JURA Elektroapparate AG. Dieses Projekt ist nicht mit JURA verbunden.
