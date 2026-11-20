# Analyse: die Maschine vom Rechner aus lesen

[English](analysis.md) | **Deutsch** · [Zurück zur Übersicht](../README.de.md)

Mit [`tools/jura_inspect.py`](../tools/jura_inspect.py) liest man eine JURA-Maschine über Bluetooth von einem Mac (oder einem Linux-/Windows-Rechner) aus und findet heraus, was sie kann: Produkte, Meldungen, Wartung, Statistik, Einstellungsregister und Bluetooth-Dienste. Das Werkzeug nutzt die Maschinendateien und den Protokollcode dieser Integration und sieht deshalb genau das, was Home Assistant sieht.

Auf dieser Seite steht außerdem, was wir über unsere WE6 und ihr Bluetooth-Modul „BlueFrog“ herausgefunden haben.

## Vorher

- **Maschine:** eingeschaltet (nicht im Standby), Smart-Connect-Modul gesteckt.
- **Home Assistant getrennt:** Die Maschine nimmt nur eine Verbindung an. Den Integrationseintrag deaktivieren (*Einstellungen › Geräte & Dienste › JURA Coffee Machines* › ⋮ › *Deaktivieren*) und danach wieder aktivieren. Der Verbindungsschalter reicht nicht, Home Assistant verbindet sich innerhalb einer Minute neu. Die JURA-App ebenfalls schließen.
- **Rechner nah an der Maschine:** wenige Meter. Unter etwa −80 dBm bricht die Verbindung öfter ab; beim Lesen versucht es das Werkzeug dann erneut.
- **Python 3.10 oder neuer** mit `bleak` und `xmltodict`.

Getestet unter macOS mit Python 3.15 und bleak. Linux und Windows sollten gehen, weil bleak sie unterstützt, sind aber nicht getestet.

## Einrichten (einmalig)

```bash
git clone https://github.com/textlastig/jura_ha.git
cd jura_ha
python3 -m venv .venv
.venv/bin/pip install bleak xmltodict
```

**macOS:** Das Terminal-Programm braucht Bluetooth-Zugriff: *Systemeinstellungen › Datenschutz & Sicherheit › Bluetooth*, Terminal (oder iTerm, …) hinzufügen. macOS fragt beim ersten Start. Ohne die Berechtigung bricht Python sofort ab (`abort trap`, Exit-Code 134), ohne Fehlermeldung. Skripte, die aus Programmen ohne eigene Bluetooth-Berechtigung gestartet werden (etwa Hintergrundjobs), brechen genauso ab; dann in einem normalen Terminalfenster starten.

## Befehle

Alle Befehle laufen im Repository-Ordner. Jeder sucht zuerst die Maschine (bis zu 30 s) und verbindet sich dann.

| Befehl | Was er tut | Ändert die Maschine? |
|---|---|---|
| `.venv/bin/python tools/jura_inspect.py info` | Maschinendatei: Produkte (Code, interner Name, Name in der JURA-App, aktiv), Meldungs-Bits, Wartungsseiten | nein |
| `.venv/bin/python tools/jura_inspect.py read` | Produktzähler, aktive Meldungen, Wartungszähler und Wartungsstand in Prozent | nein |
| `.venv/bin/python tools/jura_inspect.py settings [VON] [BIS]` | Einstellungsregister `M 00` bis `M FF` (hex), z. B. `settings 00 20` | nein |
| `.venv/bin/python tools/jura_inspect.py services` | Bluetooth-Dienste und Charakteristiken mit ihren Eigenschaften | nein |
| `.venv/bin/python tools/jura_inspect.py write REGISTER WERT` | Schreibt ein Einstellungsregister, siehe [unten](#schreibmodus-auf-eigene-gefahr) | **ja** |

Den Verschlüsselungsschlüssel holt das Werkzeug aus der Bluetooth-Werbung der Maschine, ausgegeben wird er nie.

### Beispiel (unsere WE6)

```text
$ .venv/bin/python tools/jura_inspect.py read
Searching for a JURA machine (switch it on, disconnect Home Assistant) ...
Found TT214H BlueFrog: model WE6, signal -73 dBm
Connected.
Reading statistics (this can take half a minute) ...

Total products: 22417
  01  Ristretto                    17
  02  Espresso                     65
  03  Coffee                       6984
  0D  Hotwater Portion(normal)     639
  11  2 Ristretti                  7
  12  2 Espressi                   11
  13  2 Coffee                     27
  33  1 coffee special             14667

Active alerts: 1 fill water, 33 decalc alert, 36 energy safe, 148 (not in machine file), 150 (not in machine file)

Maintenance counters:
  Cleaning       208
  FilterChange   0
  Decalc         29
  CoffeeRinse    0

Maintenance percents:
  Cleaning       70 %
  FilterChange   not used (0xFF)
  Decalc         100 %
```

Die Ausgabe ist englisch, die Namen stammen aus der Maschinendatei.

## Wie die Maschine spricht

### Werbung (Advertisement)

- Name unseres Moduls: `TT214H BlueFrog`.
- Herstellerdaten mit Firmenkennung 171 (JURA). Byte 0 ist der Schlüssel für die Sitzung, Byte 4–5 (Little Endian) die Modellnummer.
- Über `JOE_MACHINES.TXT` in `resources.zip` führt die Modellnummer zur Maschinendatei (WE6: `15114;WE6;EF534` → `documents/xml/EF534/…xml`).
- Das Modell steht nur in der Scan-Antwort, deshalb ist eine aktive Suche nötig.

### Dienste des WE6-Moduls

| Dienst | Charakteristiken | Zweck |
|---|---|---|
| `5a401523-…` (JURA) | `1524` lesen: Maschinenstatus (Meldungs-Bits) · `1525` schreiben: Produkt zubereiten · `1529` schreiben: P-Modus (Lebenszeichen, Einstellungsbefehle) · `1538` lesen: Antwort im P-Modus · `1533` lesen/schreiben: Statistikbefehl · `1534` lesen: Statistikdaten · weitere: `1527`, `1528`, `1530`, `1531`, `1532`, `1535`, `1536`, `1537` | alles, was die Integration nutzt |
| `5a401623-…` | `1624` lesen · `1625` schreiben | Teil des neueren Textprotokolls, siehe [BlueFrog](#bluefrog-und-das-neuere-textprotokoll) |
| `00001530-1212-efde-1523-785feabcd123` | `1531` melden/schreiben · `1532` schreiben ohne Antwort | Nordic DFU (Firmware-Update). **Nicht anfassen.** |

Alle JURA-Charakteristiken enden auf `-ab2e-2548-c435-08c300000710`.

### Protokoll

- **Verschlüsselung:** Jeder Wert ist mit dem Schlüsselbyte aus der Werbung verschlüsselt (`core/encryption.py`, `encdec`). Befehle tragen den Schlüssel als Byte 0.
- **Lebenszeichen:** `00 7F 80` an `1529`. Ohne Lebenszeichen trennt die Maschine nach etwa 10 s.
- **Status:** `1524`, entschlüsselt. Byte 0 wiederholt den Schlüssel, ab Byte 1 ein Bit pro Meldung (Bit 0 = höchstes Bit von Byte 1). Direkt nach dem Verbinden meldet die Maschine einige Sekunden lang einen Platzhalter; erst danach stimmen die Bits.
- **Statistik:** `00 00 <Seite> <Argument>` an `1533` schreiben, warten, `1534` lesen.
  - Seite `01`, Argument `FFFF`: Gesamtzähler und je Produktcode ein Zähler mit 3 Byte. Bereit, wenn Byte 1 des unverschlüsselten `1533`-Werts nicht mehr 225 ist. Dauert bis zu etwa 20 s.
  - Seite `04`, Argument `0100`: Wartungszähler, je 2 Byte.
  - Seite `08`, Argument `0100`: Wartungsstand in Prozent, je 1 Byte, `FF` = nicht benutzt.
  - Seite 4 und 8 sind bereit, wenn Byte 0 des entschlüsselten `1533`-Werts vom Schlüssel abweicht.
  - Welche Wartungsarten auf den Seiten stehen und in welcher Reihenfolge, steht in der Maschinendatei.
- **Einstellungen:** `00 4D <Register>` an `1529` („M“ + Register), Antwort von `1538` (Byte 0 wiederholt den Schlüssel). Schreiben: `00 4D` + Register und Wert als ASCII-Hex + Prüfsumme, so wie die JURA-App es macht.

## Ergebnisse für die WE6

Geprüft am 20.11.2026 mit einer WE6 (Maschinendatei EF534) und ihrem Smart-Connect-Modul „TT214H BlueFrog“.

| Was | Ergebnis |
|---|---|
| Produktzähler, Wartungszähler, Wartungsstand, Meldungen | lesbar, dieselben Werte wie in Home Assistant |
| Filter | Wartungsstand `FF` = nicht benutzt (kein Filter im Tank) |
| Tageszähler | nicht lesbar: Statistikseite 2 ist nur Nullen, auch direkt nach einem Bezug. Am Display stehen über 22 000. |
| Einstellungsregister `M 00`–`M 56` | jede Antwort nur Nullen, auch 02 (Wasserhärte bei anderen Modellen) und 13 (Abschalt-Timer bei anderen Modellen) |
| Abschalt-Timer, Schreiben `M 13 1E` (30 min) | ohne Fehler angenommen, der Timer blieb aber auf 1 h |
| Meldungs-Bits 36, 148, 150 | bei unserer Maschine gesetzt; 36 ist „energy safe“ (Energiesparen), 148 und 150 stehen nicht in der Maschinendatei. Bedeutung unbekannt. |
| Neueres Textprotokoll (`@TM:13`) | nicht angeboten: Schreiben auf `5a401625` lehnt die Maschine mit „Write Not Permitted“ ab |

Die Maschinendatei der WE6 hat gar keinen Einstellungsblock. Die JURA-App bietet bei der WE6 also auch keine Maschineneinstellungen an. Wasserhärte, Abschalt-Timer und Tageszähler, die die Maschine am Display zeigt, sind bei der WE6 über Bluetooth nicht lesbar.

## BlueFrog und das neuere Textprotokoll

Die JURA-App J.O.E. (Version 4.6.16) kennt zwei Wege zu Bluetooth-Modulen:

- **`CoffeeMachineAdapterBle`:** das oben beschriebene Protokoll. Unser Modul nutzt es, die Integration auch.
- **`frog/CoffeeMachineAdapterBle2` („Ble2“):** ein Textprotokoll wie an der seriellen Schnittstelle der JURA-Maschinen (`@TM:13` Einstellung 13 lesen, `@TM:13,1E…` sie schreiben, `@TG`, `@TS`, …). Die Zeilen sind verschlüsselt, beginnen mit `0x2B` und enden mit `\r\n`. Die App meldet sich zuerst mit `@HP:<Token>,<App-Kennung>,<PIN>` an; die Maschine antwortet mit `@hp4:<Token>` (angenommen) oder `@hp5…` (abgelehnt). Im Dienst `5a401623` erwartet die App die Charakteristiken `1627` (Anmeldung), `1625` (Befehle), `1626` und `1624` (Antworten als Meldungen).

Unser WE6-Modul heißt zwar „BlueFrog“, bietet in diesem Dienst aber nur `1624` (lesen) und `1625` (schreiben) und lehnt Schreiben auf `1625` ab. Das Textprotokoll gibt es darauf also nicht, vermutlich erst mit einer neueren Modul-Firmware. An den Firmware-Update-Dienst haben wir nichts gesendet.

Die App kennt außerdem ein Feld für den Tageszähler (`DAILYCOUNTER` in der Maschinendatei), fragt es über Bluetooth aber nie ab. Einen Befehl zum Zurücksetzen gibt es in der App nicht.

## Schreibmodus: auf eigene Gefahr

> **Warnung.** `write` ändert Einstellungen in der Maschine. Niemand kennt die Register aller Modelle. Ein falscher Wert kann Einstellungen ändern, die man nicht sieht und ohne JURA-App oder Service nicht zurücksetzen kann, oder die Maschine unerwartet reagieren lassen. Die Benutzung erfolgt **vollständig auf eigene Gefahr**. Es gibt keine Gewährleistung, und die Autoren haften nicht für Schäden an der Maschine. Nur benutzen, wenn man weiß, was das Register beim eigenen Modell bewirkt.

```bash
.venv/bin/python tools/jura_inspect.py write 13 1E
```

- Register und Wert sind hex (hier: Register 13 = Abschalt-Timer bei anderen Modellen, Wert 1E = 30 min).
- Das Werkzeug zeigt, was es senden wird, und verlangt die Eingabe `yes, at my own risk`. Alles andere bricht ohne Schreiben ab.
- Es liest das Register vorher und nachher und zeigt die direkte Antwort der Maschine.
- Bei einem Verbindungsfehler wiederholt es einen Schreibbefehl nicht.

Bei unserer WE6 wurde der Schreibbefehl angenommen, hatte aber keine Wirkung (siehe Ergebnisse).

## Eigene Skripte schreiben

Das Werkzeug lässt sich als Bibliothek für eigene Versuche nutzen. Die Bausteine stehen in `tools/jura_inspect.py`:

- `find_machine()` sucht die Maschine und lädt ihre Maschinendatei. Zurück kommen das Bluetooth-Gerät und ein Dict mit `model`, `products`, `alerts`, `maintenance` und `key`.
- `connect(device, machine)` verbindet, schickt das erste Lebenszeichen und hält die Verbindung im Hintergrund am Leben. Zurück kommt eine `Session`.
- `Session.read(uuid)` liest und entschlüsselt eine Charakteristik, `Session.enc(data)` verschlüsselt einen Befehl, `Session.register(reg)` liest ein Einstellungsregister, `Session.statistics_page(page, arg)` liest eine Statistikseite, `Session.close()` trennt.

Beispiel: alle 10 Sekunden den Status lesen und die aktiven Meldungen ausgeben.

```python
# my_status.py, im Repository-Ordner; starten mit: .venv/bin/python my_status.py
import asyncio
import sys

sys.path.insert(0, "tools")
import jura_inspect as ji


async def main():
    device, machine = await ji.find_machine()
    s = await ji.connect(device, machine)
    try:
        await asyncio.sleep(8)  # die ersten Statuswerte sind Platzhalter
        for _ in range(6):
            status = await s.read(ji.MACHINE_STATUS)
            bits = [b for b in range((len(status) - 1) * 8)
                    if (status[(b >> 3) + 1] >> (7 - (b & 7))) & 1]
            print([machine["alerts"].get(b, b) for b in bits])
            await asyncio.sleep(10)
    finally:
        await s.close()


asyncio.run(main())
```

Regeln, die sich bei uns bewährt haben:

- **Erst lesen.** Lesebefehle ändern die Maschine nicht. Schreiben nur, wenn klar ist, was ein Befehl bewirkt.
- **Den Schlüssel nicht ausgeben** (Byte 0 der Herstellerdaten), Tokens auch nicht. Für die Ausgabe braucht man sie nicht.
- **Den Firmware-Update-Dienst nie anfassen** (`00001530-1212-…`).
- **Eins nach dem anderen.** Nie schreiben, während jemand die Maschine benutzt oder ein anderes Gerät verbunden ist.
- **Home Assistant danach wieder aktivieren.**

Es gilt dieselbe Warnung wie beim Schreibmodus: Eigene Skripte, die in die Maschine schreiben, laufen **vollständig auf eigene Gefahr**.

## Weiterlesen

- [Jutta-Proto/protocol-bt-cpp](https://github.com/Jutta-Proto/protocol-bt-cpp): Beschreibung des Bluetooth-Protokolls
- [Jutta-Proto/protocol-cpp](https://github.com/Jutta-Proto/protocol-cpp): das serielle Textprotokoll (`@T…`-Befehle)
- [franfrancisco9/Jura-Python-BT](https://github.com/franfrancisco9/Jura-Python-BT)
- [lunarius.fe80.eu](https://lunarius.fe80.eu/blog/tag/bluetooth.html): Blogbeiträge zu JURA und Bluetooth
