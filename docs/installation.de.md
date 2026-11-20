# Installation und Einrichtung

[English](installation.md) | **Deutsch** · [Zurück zur Übersicht](../README.de.md)

Vorher die [Voraussetzungen](../README.de.md#voraussetzungen) prüfen: Smart-Connect-Modul an der Maschine, Bluetooth in Home Assistant (direkt oder über einen ESPHome-Bluetooth-Proxy).

## Installieren

### Mit HACS (Marketplace)

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=textlastig&repository=jura_ha&category=Integration)

1. HACS bzw. Marketplace › Menü › *Benutzerdefinierte Repositories*.
2. URL `https://github.com/textlastig/jura_ha`, Typ *Integration* › *Hinzufügen*.
3. „JURA Coffee Machines“ öffnen › *Herunterladen*.
4. Home Assistant neu starten.

Neue Versionen erscheinen danach in Home Assistant wie jedes andere Update.

### Ohne HACS

Den Ordner `custom_components/jura` aus dem [neuesten Release](https://github.com/textlastig/jura_ha/releases/latest) nach `custom_components` im Konfigurationsordner kopieren und Home Assistant neu starten.

### Umstieg vom Original (AlexxIT/Jura)

Original und Fork nutzen beide die Domain `jura`, es darf nur eine davon installiert sein.

1. Das Original in HACS entfernen (den Integrationseintrag **nicht** löschen).
2. Den Fork wie oben installieren.
3. Home Assistant neu starten.

Der vorhandene Eintrag läuft weiter. Entitäten und Entitäts-IDs bleiben gleich, Verlauf und Statistik bleiben also erhalten.

## Einrichten

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jura)

1. Die Maschine einschalten.
2. *Einstellungen › Geräte & Dienste › Integration hinzufügen › JURA Coffee Machines*.
3. Die MAC-Adresse der Maschine wählen.

Steht keine MAC-Adresse zur Auswahl, sieht Home Assistant gerade keine Maschine. Dann prüfen:

- Ist die Maschine an?
- Ist die JURA-App auf dem Handy geschlossen? Solange ein Handy oder Home Assistant verbunden ist, sendet die Maschine nicht und ist nicht zu finden.
- Ist ein Bluetooth-Empfänger nah genug? Siehe [Bluetooth-Fehlersuche](troubleshooting.de.md).

Maschinen mit PIN-Schutz werden nicht unterstützt.

Nach der ersten Einrichtung darf die Maschine aus sein, auch beim Neustart von Home Assistant. Die Integration merkt sich Modell und Schlüssel und zeigt die letzten Werte, bis die Maschine wieder erreichbar ist.

## Option „Nur auslesen, keine Steuerung“

*Einstellungen › Geräte & Dienste › JURA Coffee Machines › Konfigurieren.* Standard ist aus.

Eingeschaltet legt die Integration nur Sensoren und Binärsensoren an. Tasten (Zubereiten, Statistik aktualisieren), Auswahlen, Zahlen und der Verbindungsschalter werden aus Home Assistant entfernt. Wird die Option wieder ausgeschaltet, legt die Integration sie mit denselben IDs neu an.

Sinnvoll, wenn niemand über Home Assistant Kaffee machen soll, etwa bei Sprachassistenten oder Dashboards, die andere mitbenutzen.

## Weiter

- [Entitäten](entities.de.md): was die Integration anlegt
- [Dashboard](dashboard.de.md): fertiges Dashboard und Tageszähler
