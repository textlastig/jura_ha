import asyncio

from bleak import BLEDevice

from custom_components.jura.core.client import Client
from custom_components.jura.core.device import MAX_REJECTED, Device

# WE6, 2026-11-25: a maintenance page was decoded as product counters
GOOD = {None: 22443, "Coffee": 6984, "Espresso": 65, "Ristretto": 17, "Special": 14693}
BAD = {None: 53248, "Coffee": 12517376, "Espresso": 131, "Ristretto": 30, "Special": 0}


def make_device(known=None) -> Device:
    device = Device.__new__(Device)
    device.known_counts = dict(known or {})
    device.rejected_counts = []
    return device


def test_maintenance_page_rejected():
    device = make_device(GOOD)
    assert not device._accept_counts(BAD)
    assert device.known_counts == GOOD
    assert device._accept_counts({**GOOD, None: 22444, "Special": 14694})
    assert device.rejected_counts == []


def test_first_read_without_baseline():
    assert not make_device()._accept_counts(BAD)
    assert make_device()._accept_counts(GOOD)


def test_single_counter_back():
    assert not make_device(GOOD)._accept_counts({**GOOD, "Espresso": 64})


def test_no_upper_limit():
    # busy machine, not read for a long time
    counts = {**GOOD, None: 322443, "Special": 314693}
    assert make_device(GOOD)._accept_counts(counts)


def test_lasting_reset_accepted():
    device = make_device(GOOD)
    new = {None: 3, "Coffee": 3, "Espresso": 0, "Ristretto": 0, "Special": 0}
    for _ in range(MAX_REJECTED - 1):
        assert not device._accept_counts(new)
    assert device._accept_counts(new)
    assert device.known_counts == new


def test_client_waits_for_page(monkeypatch):
    async def main():
        client = Client(BLEDevice("AA:BB:CC:DD:EE:FF", None, None), key=42)
        pages = []

        async def page(*args):
            pages.append(args[:2])
            return b"data"

        monkeypatch.setattr(client, "read_statistics_page", page)
        assert await client.read_statistics_data() == b"data"
        assert pages == [(0x01, 0xFFFF)]

        async def no_page(*args):
            return None

        monkeypatch.setattr(client, "read_statistics_page", no_page)
        # no connection: no fallback to possibly stale data
        assert await client.read_statistics_data() is None

    asyncio.run(main())
