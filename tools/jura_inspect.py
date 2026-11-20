"""Inspect a JURA coffee machine over Bluetooth from a computer (macOS, Linux, Windows).

Uses the machine file and the protocol code of this integration, so the results
match what Home Assistant sees. See docs/analysis.md (English) and
docs/analysis.de.md (German).

Setup (once):
    python3 -m venv .venv && .venv/bin/pip install bleak xmltodict

Commands (run from the repository root, machine switched on, Home Assistant
disconnected from the machine, see the docs):
    .venv/bin/python tools/jura_inspect.py info       machine file: products, alerts, maintenance
    .venv/bin/python tools/jura_inspect.py services   Bluetooth services and characteristics
    .venv/bin/python tools/jura_inspect.py read       alerts, statistics, maintenance
    .venv/bin/python tools/jura_inspect.py settings [FROM] [TO]
                                                      read setting registers, default 00..FF (hex)
    .venv/bin/python tools/jura_inspect.py write REGISTER VALUE
                                                      write a setting register (hex), AT YOUR OWN RISK

The encryption key byte and other secrets are never printed. Reading does not
change the machine; "write" does and asks for confirmation first.
"""

import asyncio
import sys
from pathlib import Path

# the integration's core package (protocol, machine files); appended so that
# the integration's select.py does not shadow Python's own select module
sys.path.append(str(Path(__file__).resolve().parent.parent / "custom_components" / "jura"))

try:
    from bleak import BleakClient, BleakScanner
    from bleak.exc import BleakError
    from core.device import MAINTENANCE_PAGES, get_machine, load_texts, make_labels
    from core.encryption import encdec
except ImportError as ex:  # pragma: no cover
    sys.exit(f"{ex}. Install the requirements: pip install bleak xmltodict")

JURA_COMPANY_ID = 171
START_PRODUCT = "5a401525-ab2e-2548-c435-08c300000710"
MACHINE_STATUS = "5a401524-ab2e-2548-c435-08c300000710"
P_MODE = "5a401529-ab2e-2548-c435-08c300000710"
P_MODE_READ = "5a401538-ab2e-2548-c435-08c300000710"
STATS_COMMAND = "5a401533-ab2e-2548-c435-08c300000710"
STATS_DATA = "5a401534-ab2e-2548-c435-08c300000710"
HEARTBEAT = [0x00, 0x7F, 0x80]
LANGUAGE = "en"


def hexdump(data: bytes) -> str:
    return data.hex(" ") if data else "-"


async def find_machine(timeout: float = 30):
    """First device that advertises JURA manufacturer data."""
    print("Searching for a JURA machine (switch it on, disconnect Home Assistant) ...")
    found: dict = {}

    def on_adv(device, adv):
        if JURA_COMPANY_ID in adv.manufacturer_data and "device" not in found:
            found.update(device=device, adv=adv.manufacturer_data[JURA_COMPANY_ID], rssi=adv.rssi)

    async with BleakScanner(on_adv):
        for _ in range(int(timeout * 2)):
            if found:
                break
            await asyncio.sleep(0.5)
    if not found:
        sys.exit(f"No JURA machine found within {timeout:.0f} s.")
    machine = get_machine(found["adv"])
    print(f"Found {found['device'].name or 'JURA'}: model {machine['model']}, signal {found['rssi']} dBm")
    return found["device"], machine


def print_machine_file(machine: dict) -> None:
    texts = load_texts(LANGUAGE)
    labels = make_labels(machine["products"], texts)
    print("\nProducts (code, name in the machine file, name in the JURA app, active):")
    for p in machine["products"]:
        active = "inactive" if p.get("@Active") == "false" else "active"
        print(f"  {p['@Code']:>3}  {p['@Name']:<28} {labels[p['@Name']]:<28} {active}")
    print("\nAlerts (bit: name):")
    for bit, name in sorted(machine["alerts"].items()):
        print(f"  {bit:>3}: {name}")
    print("\nMaintenance pages:")
    for kind, types in machine["maintenance"].items():
        print(f"  {kind}: {', '.join(types) or '-'}")


class Session:
    """One Bluetooth connection with heartbeat, like the integration."""

    def __init__(self, client: BleakClient, key: int):
        self.client = client
        self.key = key
        self.task: asyncio.Task | None = None

    def start_heartbeat(self) -> None:
        """The machine disconnects after about 10 s without a heartbeat."""

        async def loop():
            while self.client.is_connected:
                await asyncio.sleep(5)
                try:
                    await self.heartbeat()
                except Exception:  # noqa: BLE001 - the main task reports errors
                    return

        self.task = asyncio.create_task(loop())

    async def close(self) -> None:
        if self.task:
            self.task.cancel()
        if self.client.is_connected:
            await self.client.disconnect()

    def enc(self, data) -> bytes:
        data = bytearray(data)
        data[0] = self.key
        return encdec(data, self.key)

    async def heartbeat(self) -> None:
        await self.client.write_gatt_char(P_MODE, self.enc(HEARTBEAT), response=True)

    async def read(self, uuid: str) -> bytes:
        return bytes(encdec(list(await self.client.read_gatt_char(uuid)), self.key))

    async def product_counters(self) -> bytes | None:
        """Statistics page 1 (total and per product), as the integration reads it."""
        await self.client.write_gatt_char(
            STATS_COMMAND, self.enc([0, 0x00, 0x01, 0xFF, 0xFF]), response=True
        )
        for _ in range(60):  # can take 20 s and more
            if (await self.client.read_gatt_char(STATS_COMMAND))[1] != 225:  # 225: not ready
                return await self.read(STATS_DATA)
            await asyncio.sleep(0.8)
        return None

    async def statistics_page(self, page: int, arg: int) -> bytes | None:
        await self.client.write_gatt_char(
            STATS_COMMAND, self.enc([0, 0x00, page, arg >> 8, arg & 0xFF]), response=True
        )
        for _ in range(60):
            if (await self.read(STATS_COMMAND))[0] != self.key:
                return await self.read(STATS_DATA)
            await asyncio.sleep(0.8)
        return None

    async def register(self, reg: int) -> bytes:
        await self.heartbeat()
        await self.client.write_gatt_char(P_MODE, self.enc([0x00, 0x4D, reg]), response=True)
        await asyncio.sleep(0.5)
        return (await self.read(P_MODE_READ))[1:]  # first byte echoes the key


async def connect(device, machine):
    client = BleakClient(device, timeout=30)
    await client.connect()
    session = Session(client, machine["key"])
    await session.heartbeat()
    session.start_heartbeat()
    print("Connected.")
    return session


async def cmd_read(device, machine) -> None:
    s = await connect(device, machine)
    loop = asyncio.get_running_loop()
    connected_at = loop.time()
    try:
        print("Reading statistics (this can take half a minute) ...", flush=True)
        data = await s.product_counters()
        if data:
            counts = [int.from_bytes(data[i : i + 3], "big") for i in range(0, len(data) - 2, 3)]
            counts = [0 if c == 0xFFFF else c for c in counts]
            print(f"\nTotal products: {counts[0]}")
            names = {int(p["@Code"], 16): p["@Name"] for p in machine["products"]}
            for code, count in enumerate(counts[1:], start=1):
                if code in names or count:
                    print(f"  {code:02X}  {names.get(code, '(not in machine file)'):<28} {count}")
        else:
            print("\nStatistics: no answer")

        # right after connecting the machine reports a placeholder status for a
        # few seconds; after the statistics it is valid
        await asyncio.sleep(max(0.0, 8 - (loop.time() - connected_at)))
        status = await s.read(MACHINE_STATUS)
        active = [
            f"{bit} {machine['alerts'].get(bit, '(not in machine file)')}"
            for bit in range((len(status) - 1) * 8)
            if (status[(bit >> 3) + 1] >> (7 - (bit & 7))) & 1
        ]
        print("\nActive alerts:", ", ".join(active) or "none")

        for kind, types in machine["maintenance"].items():
            if not types:
                continue
            page = await s.statistics_page(*MAINTENANCE_PAGES[kind])
            if not page:
                print(f"\nMaintenance {kind}: no answer")
                continue
            if kind == "counters":
                values = [int.from_bytes(page[2 * i : 2 * i + 2], "big") for i in range(len(types))]
            else:
                values = ["not used (0xFF)" if v == 255 else f"{v} %" for v in page[: len(types)]]
            print(f"\nMaintenance {kind}:")
            for t, v in zip(types, values):
                print(f"  {t:<14} {v}")
    finally:
        await s.close()


async def cmd_services(device, machine) -> None:
    s = await connect(device, machine)
    try:
        for service in s.client.services:
            print("service", service.uuid)
            for ch in service.characteristics:
                print("   ", ch.uuid, ",".join(ch.properties))
    finally:
        await s.close()


async def cmd_settings(device, machine, start: int, end: int) -> None:
    s = await connect(device, machine)
    last = None
    try:
        for reg in range(start, end + 1):
            answer = await s.register(reg)
            same = " (same as before)" if answer == last else ""
            print(f"M {reg:02X}: {hexdump(answer[:16])}{same}", flush=True)
            last = answer
    finally:
        await s.close()


async def cmd_write(device, machine, reg: int, value: int) -> None:
    text = f"{reg:02X}{value:02X}"
    checksum = 255 - (ord(",") + sum(map(ord, text))) % 256
    command = bytes([0x00, 0x4D]) + bytes.fromhex(text) + bytes([checksum])
    print(
        "\nWARNING: this writes setting register "
        f"{reg:02X} = {value:02X} to the machine ({command[1:].hex(' ')}).\n"
        "Wrong values can change settings you cannot see or reset without the JURA app "
        "or a service visit. Nobody knows the registers of every model. "
        "You use this at your own risk; there is no warranty."
    )
    if input('Type "yes, at my own risk" to continue: ').strip().lower() != "yes, at my own risk":
        print("Cancelled, nothing written.")
        return
    s = await connect(device, machine)
    try:
        before = await s.register(reg)
        print(f"before: {hexdump(before[:16])}")
        await s.heartbeat()
        await s.client.write_gatt_char(P_MODE, s.enc(command), response=True)
        await asyncio.sleep(0.6)
        print(f"answer: {hexdump((await s.read(P_MODE_READ))[1:17])}")
        print(f"after:  {hexdump((await s.register(reg))[:16])}")
    finally:
        await s.close()


async def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[1] not in ("info", "services", "read", "settings", "write"):
        sys.exit(__doc__)
    for attempt in range(1, 4):
        try:
            await run(argv)
            return
        except BleakError as ex:
            # the machine drops weak connections; reading is safe to repeat
            if argv[1] == "write" or attempt == 3:
                sys.exit(f"Bluetooth error: {ex}. Move the computer closer to the machine.")
            print(f"Connection lost ({ex}), trying again ...")
            await asyncio.sleep(3)


async def run(argv: list[str]) -> None:
    device, machine = await find_machine()
    command = argv[1]
    if command == "info":
        print_machine_file(machine)
    elif command == "services":
        await cmd_services(device, machine)
    elif command == "read":
        await cmd_read(device, machine)
    elif command == "settings":
        start = int(argv[2], 16) if len(argv) > 2 else 0
        end = int(argv[3], 16) if len(argv) > 3 else 0xFF
        await cmd_settings(device, machine, start, end)
    elif command == "write":
        if len(argv) != 4:
            sys.exit("usage: jura_inspect.py write REGISTER VALUE (both hex, e.g. 13 1E)")
        await cmd_write(device, machine, int(argv[2], 16), int(argv[3], 16))


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
