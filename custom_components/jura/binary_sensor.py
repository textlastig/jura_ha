import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .core.entity import JuraEntity

_LOGGER = logging.getLogger(__name__)

# Define alert sensors with their expected alert names and configurations
ALERT_SENSORS = [
    # Maintenance alerts (these are normal maintenance operations)
    {
        "name_pattern": "insert tray",
        "type": "insert_tray",
        "display_name": "Insert Tray",
        "icon": "mdi:tray",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        # on the WE6 the grounds container sits in the drip tray, so pulling
        # the tray raises this together with "insert tray"
        "name_pattern": "insert coffee bin",
        "type": "insert_coffee_bin",
        "display_name": "No Coffee Grounds Container",
        "icon": "mdi:delete-empty",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "fill water",
        "type": "fill_water",
        "display_name": "Fill Water",
        "icon": "mdi:water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "empty grounds",
        "type": "empty_grounds",
        "display_name": "Empty Grounds",
        "icon": "mdi:delete",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "empty tray",
        "type": "empty_tray",
        "display_name": "Empty Tray",
        "icon": "mdi:tray-alert",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "no beans",
        "type": "no_beans",
        "display_name": "No Beans",
        "icon": "mdi:coffee-off",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    # Service alerts (require cleaning or filter replacement)
    {
        "name_pattern": "cleaning alert",
        "type": "cleaning_alert",
        "display_name": "Cleaning Needed",
        "icon": "mdi:washing-machine",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "filter alert",
        "type": "filter_alert",
        "display_name": "Filter Change Needed",
        "icon": "mdi:air-filter",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        # exact: "Info - decalc alert" (pre-warning) must not match
        "name_pattern": "decalc alert",
        "exact": True,
        "type": "decalc_alert",
        "display_name": "Descaling Needed",
        "icon": "mdi:water-alert",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "info - decalc alert",
        "exact": True,
        "type": "decalc_info",
        "display_name": "Descaling Soon",
        "icon": "mdi:water-alert-outline",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "cappu rinse alert",
        "type": "cappu_rinse_alert",
        "milk": True,
        "display_name": "Milk System Rinse Needed",
        "icon": "mdi:cup-water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "cappu clean alert",
        "type": "cappu_clean_alert",
        "milk": True,
        "display_name": "Milk System Cleaning Needed",
        "icon": "mdi:cup-water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    # Create connection sensor
    entities: list = [JuraSensor(device, "connection")]

    # Create alert binary sensors; milk system alerts only for machines with
    # milk products (the machine file lists these alerts for every model)
    milk = has_milk_system(device.products)
    registry = er.async_get(hass)
    for alert_info in ALERT_SENSORS:
        if alert_info.get("milk") and not milk:
            unique_id = f"{device.mac.replace(':', '')}_alert_{alert_info['type']}"
            if entity_id := registry.async_get_entity_id(
                "binary_sensor", DOMAIN, unique_id
            ):
                registry.async_remove(entity_id)  # created by an older version
            continue
        entities.append(JuraAlertBinarySensor(device, alert_info))

    add_entities(entities)


def has_milk_system(products: list) -> bool:
    """True if the machine file has a product with milk (P_Kind M or CM)."""
    return any("M" in p.get("@P_Kind", "") for p in products)


class JuraSensor(JuraEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def internal_update(self):
        self._attr_is_on = self.device.connected
        self._attr_extra_state_attributes = self.device.conn_info

        if self.hass:
            self._async_write_ha_state()


class JuraAlertBinarySensor(JuraEntity, BinarySensorEntity, RestoreEntity):
    """Binary sensor for Jura alerts."""

    def __init__(self, device, alert_info: dict):
        """Initialize the sensor."""
        # Store name pattern before calling super().__init__
        self._name_pattern = alert_info["name_pattern"].lower()
        self._exact = alert_info.get("exact", False)

        super().__init__(device, f"alert_{alert_info['type']}")

        self._attr_icon = alert_info["icon"]
        self._attr_device_class = alert_info["device_class"]
        self._attr_entity_category = alert_info["entity_category"]

        # Register for updates on alerts
        device.register_alert_update(self.internal_update)

    async def async_added_to_hass(self) -> None:
        """Keep the last state while the machine is off."""
        await super().async_added_to_hass()
        if not self.device.alerts_read and (last := await self.async_get_last_state()):
            if last.state in ("on", "off"):
                self._attr_is_on = last.state == "on"
                self.async_write_ha_state()

    def internal_update(self):
        """Update the sensor state."""
        if not self.device.alerts_read and self._attr_is_on is not None:
            return  # keep the restored state until alerts were read
        # Check if any active alert's name contains (or, if exact, equals) our pattern
        self._attr_is_on = any(
            self._name_pattern == alert_name.lower()
            if self._exact
            else self._name_pattern in alert_name.lower()
            for alert_name in self.device.active_alerts.values()
        )

        if self.hass:
            self._async_write_ha_state()
