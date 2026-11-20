# Bluetooth-Fehlersuche

[English](troubleshooting.md) | **Deutsch** · [Zurück zur Übersicht](../README.de.md)

## Grundlagen

- **Nur eine Verbindung gleichzeitig.** Das Smart-Connect-Modul nimmt nur eine Bluetooth-Verbindung an. Solange Home Assistant verbunden ist, kommt die JURA-App nicht an die Maschine, und umgekehrt.
- **Keine Werbung während einer Verbindung.** Solange ein Gerät verbunden ist, sendet die Maschine nicht und ist für andere nicht zu finden.
- **Aktive Suche nötig für die Einrichtung.** Die Maschine sendet ihr Modell nur in der Scan-Antwort. Ein Empfänger, der nur passiv mithört, reicht nicht.
- **Lebenszeichen.** Ohne Lebenszeichen (Heartbeat) trennt die Maschine eine Verbindung nach etwa 10 Sekunden. Die Integration schickt alle 9 Sekunden eins.

## Empfänger

Ein guter Empfänger nah an der Maschine ist wichtiger als alles andere.

- **ESPHome-Bluetooth-Proxy (empfohlen):** ein ESP32 mit [`bluetooth_proxy`](https://esphome.io/components/bluetooth_proxy.html) und `active: true`, nah an der Maschine. Wir nutzen einen M5Stack AtomS3U (ESP32-S3 als USB-Stick) in einer Steckdose mit USB neben der Maschine. Jeder ESP32 mit Bluetooth sollte gehen.
  ```yaml
  esp32_ble_tracker:
    scan_parameters:
      active: true
  bluetooth_proxy:
    active: true
  ```
- **Bluetooth-Adapter am Home-Assistant-Rechner:** siehe die [Liste von Home Assistant](https://www.home-assistant.io/integrations/bluetooth/). AlexxIT hatte mit fünf Adaptern (*Unbranded CSR clone detected*) keine stabile Verbindung, erst ein Adapter mit `CSR8510A10` lief zuverlässig.

Zum Vergleich: Ein MacBook wenige Meter von unserer WE6 entfernt sah die Maschine mit −72 bis −84 dBm und konnte alles lesen, verlor die Verbindung bei −84 dBm aber öfter.

## Die Maschine erscheint bei der Einrichtung nicht

1. Ist die Maschine an? Sie sendet nur, solange sie an ist.
2. Die JURA-App ganz schließen (auch aus der App-Übersicht wischen) oder Bluetooth am Handy ausschalten.
3. Ist ein Empfänger mit aktiver Suche nah genug?
4. Hilft nichts: die Maschine ganz aus- und wieder einschalten. Das setzt das Modul zurück.

## Werte ändern sich nicht, Verbindung steht auf „aus“

- Die Maschine ist aus oder im Standby: normal. Die Entitäten behalten ihre letzten Werte.
- Ein anderes Gerät ist verbunden, meistens die JURA-App.
- Der Empfänger ist zu weit weg oder der Proxy ist offline: das Gerät des Proxys in Home Assistant prüfen.
- Debug-Log einschalten (*Einstellungen › Geräte & Dienste › JURA Coffee Machines › Debug-Protokollierung aktivieren*) und nach `heartbeat error` oder `ping error` suchen.

## Ein anderes Gerät kann sich nicht verbinden

Der Verbindungsschalter der Integration trennt nur kurz: Die nächste Abfrage (innerhalb einer Minute) verbindet wieder. Soll die Maschine frei bleiben, etwa für die JURA-App oder das [Analyse-Werkzeug](analysis.de.md):

1. *Einstellungen › Geräte & Dienste › JURA Coffee Machines* › Menü (⋮) › *Deaktivieren*.
2. Das andere Gerät benutzen.
3. Den Eintrag wieder aktivieren. Die Integration verbindet sich innerhalb einer Minute und liest alle Werte neu.

## Die Statistik dauert lange

Bis die Produktzähler bereitstehen, können nach der Anfrage 20 Sekunden und mehr vergehen. Das liegt an der Maschine, nicht am Empfänger. Die Wartungswerte liest die Integration direkt nach den Produktzählern.
