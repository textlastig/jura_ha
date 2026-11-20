# Analysis: read the machine from a computer

**English** | [Deutsch](analysis.de.md) · [Back to the overview](../README.md)

With [`tools/jura_inspect.py`](../tools/jura_inspect.py) you can read a JURA machine over Bluetooth from a Mac (or a Linux/Windows computer) and find out what it can do: products, alerts, maintenance, statistics, setting registers and Bluetooth services. The tool uses the machine files and the protocol code of this integration, so it sees exactly what Home Assistant sees.

This page also documents what we found out about our WE6 and its "BlueFrog" Bluetooth module.

## Before you start

- **Machine:** switched on (not in standby), Smart Connect module plugged in.
- **Home Assistant disconnected:** the machine accepts only one connection. Disable the integration entry (*Settings › Devices & services › JURA Coffee Machines* › ⋮ › *Disable*), and enable it again afterwards. The connection switch is not enough: Home Assistant reconnects within a minute. Close the JURA app too.
- **Computer close to the machine:** a few metres. Below about −80 dBm the connection drops more often; the tool then tries again for reading.
- **Python 3.10 or newer** with `bleak` and `xmltodict`.

Tested on macOS with Python 3.15 and bleak. Linux and Windows should work, because bleak supports them, but are not tested.

## Setup (once)

```bash
git clone https://github.com/textlastig/jura_ha.git
cd jura_ha
python3 -m venv .venv
.venv/bin/pip install bleak xmltodict
```

**macOS:** the terminal app needs Bluetooth access: *System Settings › Privacy & Security › Bluetooth*, add Terminal (or iTerm, …). macOS asks on the first start. Without the permission Python aborts at once (`abort trap`, exit code 134) without an error message. Scripts started from tools without their own Bluetooth permission (e.g. background jobs) abort the same way; start them in a normal terminal window.

## Commands

All commands are run from the repository folder. Each one searches for the machine first (up to 30 s), then connects.

| Command | What it does | Changes the machine? |
|---|---|---|
| `.venv/bin/python tools/jura_inspect.py info` | Machine file: products (code, internal name, name in the JURA app, active), alert bits, maintenance pages | no |
| `.venv/bin/python tools/jura_inspect.py read` | Product counters, active alerts, maintenance counters and percentages | no |
| `.venv/bin/python tools/jura_inspect.py settings [FROM] [TO]` | Setting registers `M 00` to `M FF` (hex), e.g. `settings 00 20` | no |
| `.venv/bin/python tools/jura_inspect.py services` | Bluetooth services and characteristics with their properties | no |
| `.venv/bin/python tools/jura_inspect.py write REGISTER VALUE` | Writes one setting register, see [below](#write-mode-at-your-own-risk) | **yes** |

The encryption key is taken from the machine's advertisement and never printed.

### Example (our WE6)

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

## How the machine talks

### Advertisement

- Name of our module: `TT214H BlueFrog`.
- Manufacturer data with company ID 171 (JURA). Byte 0 is the encryption key for the session, bytes 4–5 (little endian) are the model ID.
- The model ID leads via `JOE_MACHINES.TXT` in `resources.zip` to the machine file (WE6: `15114;WE6;EF534` → `documents/xml/EF534/…xml`).
- The model is only in the scan response, so active scanning is needed.

### Services of the WE6 module

| Service | Characteristics | Use |
|---|---|---|
| `5a401523-…` (JURA) | `1524` read: machine status (alert bits) · `1525` write: make product · `1529` write: P mode (heartbeat, setting commands) · `1538` read: P mode answer · `1533` read/write: statistics command · `1534` read: statistics data · further: `1527`, `1528`, `1530`, `1531`, `1532`, `1535`, `1536`, `1537` | everything the integration uses |
| `5a401623-…` | `1624` read · `1625` write | part of the newer text protocol, see [BlueFrog](#bluefrog-and-the-newer-text-protocol) |
| `00001530-1212-efde-1523-785feabcd123` | `1531` notify/write · `1532` write without response | Nordic DFU (firmware update). **Do not touch.** |

All JURA characteristics end in `-ab2e-2548-c435-08c300000710`.

### Protocol

- **Encryption:** every value is encrypted with the key byte from the advertisement (`core/encryption.py`, `encdec`). Commands start with the key as byte 0.
- **Heartbeat:** `00 7F 80` to `1529`. Without it the machine disconnects after about 10 s.
- **Status:** `1524`, decrypted, byte 0 echoes the key, from byte 1 one bit per alert (bit 0 = highest bit of byte 1). Right after connecting the machine reports a placeholder for a few seconds; only after that are the bits valid.
- **Statistics:** write `00 00 <page> <arg>` to `1533`, wait, read `1534`.
  - Page `01`, arg `FFFF`: total and one 3-byte counter per product code. Ready when byte 1 of the raw `1533` value is no longer 225. Takes up to about 20 s.
  - Page `04`, arg `0100`: maintenance counters, 2 bytes each.
  - Page `08`, arg `0100`: maintenance percentages, 1 byte each, `FF` = not used.
  - Pages 4 and 8 are ready when byte 0 of the decrypted `1533` value differs from the key.
  - Which maintenance types are on the pages, and in which order, comes from the machine file.
- **Settings:** `00 4D <register>` to `1529` ("M" + register), answer from `1538` (byte 0 echoes the key). Writing: `00 4D` + ASCII hex of register and value + checksum, as the JURA app does it.

## Results for the WE6

Tested on 20.11.2026 with a WE6 (machine file EF534) and its Smart Connect module "TT214H BlueFrog".

| What | Result |
|---|---|
| Product counters, maintenance counters, maintenance percentages, alerts | readable, same values as in Home Assistant |
| Filter | percentage `FF` = not used (no filter in the tank) |
| Daily counter | not readable: statistics page 2 is all zeros, even right after making a product. The display shows more than 22 000. |
| Setting registers `M 00`–`M 56` | every answer is only zeros, also 02 (water hardness on other models) and 13 (auto-off timer on other models) |
| Auto-off timer, write `M 13 1E` (30 min) | accepted without an error, but the timer stayed at 1 h |
| Alert bits 36, 148, 150 | set on our machine; 36 is "energy safe", 148 and 150 are not in the machine file. Meaning unknown. |
| Newer text protocol (`@TM:13`) | not offered: writing to `5a401625` is rejected with "Write Not Permitted" |

The WE6 machine file has no settings section at all, so the JURA app does not offer machine settings for the WE6 either. Water hardness, auto-off timer and daily counter, which the machine shows on its display, cannot be read over Bluetooth on the WE6.

## BlueFrog and the newer text protocol

The JURA J.O.E. app (version 4.6.16) has two ways to talk to Bluetooth modules:

- **`CoffeeMachineAdapterBle`:** the protocol described above. Our module uses this one, and so does the integration.
- **`frog/CoffeeMachineAdapterBle2` ("Ble2"):** a text protocol, as on the serial interface of JURA machines (`@TM:13` read setting 13, `@TM:13,1E…` write it, `@TG`, `@TS`, …). Lines are encrypted, start with `0x2B` and end with `\r\n`. The app logs in first with `@HP:<token>,<app ID>,<PIN>`; the machine answers `@hp4:<token>` (accepted) or `@hp5…` (rejected). The service `5a401623` is expected to have the characteristics `1627` (login), `1625` (commands), `1626` and `1624` (answers as notifications).

Our WE6 module is called "BlueFrog", but offers only `1624` (read) and `1625` (write) in that service, and rejects writes to `1625`. So the text protocol is not available on it, probably only with a newer module firmware. We sent nothing to the firmware update service.

The app also knows a daily counter field (`DAILYCOUNTER` in the machine file), but never queries it over Bluetooth. A reset command for it does not exist in the app.

## Write mode: at your own risk

> **Warning.** `write` changes settings in the machine. Nobody knows the registers of every model. A wrong value can change settings that you cannot see or reset without the JURA app or a service visit, or make the machine behave unexpectedly. You use this **entirely at your own risk**. There is no warranty, and the authors are not liable for any damage to the machine. Only use it if you know what the register does on your model.

```bash
.venv/bin/python tools/jura_inspect.py write 13 1E
```

- Register and value are hex (here: register 13 = auto-off timer on other models, value 1E = 30 min).
- The tool shows what it will send and asks you to type `yes, at my own risk`. Anything else cancels without writing.
- It reads the register before and after, and shows the machine's direct answer.
- On a connection error the tool does not repeat a write.

On our WE6 the write was accepted but had no effect (see results).

## Writing your own scripts

You can use the tool as a library for your own experiments. The building blocks are in `tools/jura_inspect.py`:

- `find_machine()` searches the machine and loads its machine file. It returns the Bluetooth device and a dict with `model`, `products`, `alerts`, `maintenance` and `key`.
- `connect(device, machine)` connects, sends the first heartbeat and keeps the connection alive in the background. It returns a `Session`.
- `Session.read(uuid)` reads and decrypts a characteristic, `Session.enc(data)` encrypts a command, `Session.register(reg)` reads a setting register, `Session.statistics_page(page, arg)` reads a statistics page, `Session.close()` disconnects.

Example: read the status every 10 seconds and print the active alerts.

```python
# my_status.py, in the repository folder; run with: .venv/bin/python my_status.py
import asyncio
import sys

sys.path.insert(0, "tools")
import jura_inspect as ji


async def main():
    device, machine = await ji.find_machine()
    s = await ji.connect(device, machine)
    try:
        await asyncio.sleep(8)  # the first status values are placeholders
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

Rules that kept us safe:

- **Read first.** Reading commands do not change the machine. Write only when you know what a command does.
- **Do not print the key** (byte 0 of the manufacturer data) or tokens. They are not needed for output.
- **Never touch the firmware update service** (`00001530-1212-…`).
- **One thing at a time.** Never write while someone is using the machine or while another device is connected.
- **Enable Home Assistant again** when you are done.

The same warning applies as for the write mode: own scripts that write to the machine are entirely **at your own risk**.

## Further reading

- [Jutta-Proto/protocol-bt-cpp](https://github.com/Jutta-Proto/protocol-bt-cpp): description of the Bluetooth protocol
- [Jutta-Proto/protocol-cpp](https://github.com/Jutta-Proto/protocol-cpp): the serial text protocol (`@T…` commands)
- [franfrancisco9/Jura-Python-BT](https://github.com/franfrancisco9/Jura-Python-BT)
- [lunarius.fe80.eu](https://lunarius.fe80.eu/blog/tag/bluetooth.html): blog posts on JURA Bluetooth
