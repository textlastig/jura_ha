# Entitäten

[English](entities.md) | **Deutsch** · [Zurück zur Übersicht](../README.de.md)

Welche Entitäten erscheinen, hängt von der Maschinendatei des Modells in `resources.zip` ab. Die Integration legt nur an, was die Maschinendatei kennt.

| Art | Entitäten |
|---|---|
| Sensoren | Bezüge gesamt und je Produkt (z. B. „Kaffee Spezial“, „2 x Kaffee“), Meldungen (`ok`/`alert` mit Liste der aktiven Meldungen). Produkte, die die Maschinendatei als inaktiv führt (z. B. Heißwasser bei der WE6), bekommen ebenfalls einen Zähler. Er ist standardmäßig deaktiviert und lässt sich am Gerät aktivieren, wenn die Maschine das Produkt hat. |
| Diagnose | Wartungszähler (Reinigung, Filterwechsel, Entkalken, Kaffeespülung, soweit die Maschine sie hat), Wartungsstand in Prozent, Verbindung |
| Binärsensoren | Restwasserschale fehlt, Kaffeesatzbehälter fehlt, Wassertank füllen, Kaffeesatzbehälter leeren, Restwasserschale leeren, Bohnen füllen, Gerät reinigen, Gerät bald reinigen, Filter wechseln, Filter bald wechseln, Filter aktiv, Gerät entkalken, Gerät bald entkalken. Maschinen mit Milchprodukten bekommen zusätzlich Milchsystem spülen, Milchsystem reinigen, Milchsystem bald reinigen. |
| Steuerung | Kaffeespezialität (Namen wie in der JURA-App), Mahlwerk-Verhältnis (z. B. „50% / 50%“), Kaffeestärke, Temperatur (Niedrig, Normal, Hoch), Mengen (Wasser und Bypass in ml, Milch, Milchschaum und Milchpause in Sekunden), Taste *Zubereiten*, Taste *Statistik aktualisieren*, Verbindungsschalter. Mit der Option [„Nur auslesen“](installation.de.md#option-nur-auslesen-keine-steuerung) nicht vorhanden. |

## Namen und IDs

- Die Namen erscheinen in der Sprache von Home Assistant (Deutsch oder Englisch).
- Die Entitäts-IDs sind davon unabhängig: `<gerät>_<mac>_<attribut>`, wie beim Original.
- Produkte und Meldungen heißen wie in der JURA-App J.O.E. und am Display der Maschine. Die Maschinendatei nennt zu jedem Produkt eine Textnummer, die Namen dazu stammen aus der App (Version 4.6.16).

## Wann Werte gelesen werden

- Statistik, Wartung und Meldungen werden jede Minute gelesen, solange die Maschine an und verbunden ist.
- Ist die Maschine aus, behalten die Entitäten ihre letzten Werte.
- Der Verbindungsschalter trennt Home Assistant nur kurz: Die nächste Abfrage (innerhalb einer Minute) verbindet wieder. Soll die Maschine für ein anderes Gerät frei bleiben, den Integrationseintrag deaktivieren, siehe [Fehlersuche](troubleshooting.de.md#ein-anderes-gerät-kann-sich-nicht-verbinden).

## Filter

„Filter aktiv“ ist die eigene Meldung der Maschine, dass sie eine Filterpatrone erkannt hat. Die WE6 erkennt eine CLARIS Pro Smart per RFID.

- Ohne Filter meldet die Maschine den Filterstand als „nicht benutzt“ (0xFF). Der Sensor Filterstand in Prozent ist dann nicht verfügbar.
- Mit Filter ist es beim Entkalken umgekehrt: Laut Anleitung der WE6 fordert die Maschine mit CLARIS Pro Smart kein Entkalken mehr an.
- Die RF-Filtereinträge stehen in jeder Maschinendatei und sagen deshalb nicht, ob ein Modell Filter erkennt. Das sagt nur die Meldung der Maschine.
- Geprüft an einer WE6 ohne Filter: „Filter aktiv“ ist aus, der Filterstand in Prozent ist nicht verfügbar.

## Ausgeblendet, solange nicht benutzt

Was die Maschine als „nicht benutzt“ meldet (Prozent 0xFF), blendet die Integration in der Geräteansicht aus, zusammen mit Zähler, Meldung und Vorwarnung. Ohne Filter sind das: Filterstand, Filterwechsel, „Filter wechseln“, „Filter bald wechseln“.

- Sobald die Maschine wieder einen Wert meldet, erscheinen sie wieder.
- Selbst ausgeblendete Entitäten bleiben ausgeblendet.
- Ausgeblendete Entitäten funktionieren weiter, etwa in Automationen.

## Was sich nicht lesen lässt

Einige Werte, die die Maschine am Display zeigt, gibt die WE6 über Bluetooth nicht heraus: Wasserhärte, Abschalt-Timer, Tageszähler. Einzelheiten unter [Analyse](analysis.de.md#ergebnisse-für-die-we6).
