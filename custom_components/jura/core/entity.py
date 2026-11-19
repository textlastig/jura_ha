import re

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo, Entity

from . import DOMAIN
from .device import Device


def sanitize(entity_id: str) -> str:
    return re.sub(r"[^0-9a-z_]+", "", entity_id.lower())


class JuraEntity(Entity):
    _attr_should_poll = False

    def __init__(self, device: Device, attr: str):
        self.device = device
        self.attr = attr

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            identifiers={(DOMAIN, device.mac)},
            manufacturer="Jura",
            model=device.model,
            name=device.name or "Jura",
        )
        self._attr_unique_id = device.mac.replace(":", "") + "_" + attr

        # names come from translations/<language>.json (entity.<platform>.<key>)
        self._attr_has_entity_name = True
        self._attr_translation_key = attr

        # fixed entity ID <device>_<mac>_<attr>, independent of language and
        # area (HA would otherwise prefix the area for new entities)
        domain = next(
            c.__module__.split(".")[2]
            for c in type(self).__mro__
            if c.__module__.startswith("homeassistant.components.")
        )
        prefix = re.sub(r"[^0-9a-z]+", "_", (device.name or "jura").lower()).strip("_")
        self.entity_id = f"{domain}.{prefix}_{sanitize(self._attr_unique_id)}"

        self.internal_update()

        device.register_update(attr, self.internal_update)

    def internal_update(self):
        pass

    async def async_update(self):
        self.device.client.ping()
