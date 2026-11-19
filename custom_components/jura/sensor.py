"""Sensor platform for Jura integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN
from .core.entity import JuraEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jura sensor based on a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]

    # Create the total coffees sensor
    entities: list = [JuraTotalCoffeeSensor(device)]

    # Create sensors for each product
    for product in device.products:
        product_name = product["@Name"]
        if product.get("@Active") != "false":
            entities.append(
                JuraProductCountSensor(device, product_name, product.get("@Text"))
            )

    # Maintenance counters and percents (if the machine file lists them)
    for kind in ("counters", "percents"):
        for mtype in device.maintenance.get(kind, []):
            entities.append(JuraMaintenanceSensor(device, kind, mtype))

    # Create alert sensors
    entities.append(JuraAlertSensor(device))

    async_add_entities(entities)

    # Set up automatic refresh
    update_interval = hass.data[DOMAIN].get("update_interval", 60)

    async def refresh_statistics(*_):
        """Refresh statistics regularly."""
        try:
            await device.read_statistics()
            await device.read_alerts()
        except Exception as ex:
            # we log as info as this is expected if the device is off
            _LOGGER.info(f"Error refreshing statistics: {ex}")

    # Schedule regular updates
    entry.async_on_unload(
        async_track_time_interval(
            hass, refresh_statistics, timedelta(seconds=update_interval)
        )
    )

    # Do an initial refresh
    hass.async_create_task(refresh_statistics())


class JuraStatisticsSensor(JuraEntity, RestoreSensor):
    """Base class for Jura statistics sensors."""

    _restored = None

    def __init__(self, device, attr: str):
        """Initialize the sensor."""
        super().__init__(device, attr)

        # Register for updates on statistics
        device.register_statistics_update(self.internal_update)

    async def async_added_to_hass(self) -> None:
        """Keep the last value while the machine is off."""
        await super().async_added_to_hass()
        if self.device.statistics_read:
            return
        if last := await self.async_get_last_sensor_data():
            self._restored = last.native_value
        elif (last := await self.async_get_last_state()) is not None:
            # state saved by a version without restore data
            try:
                self._restored = int(float(last.state))
            except ValueError:
                pass
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.device.statistics_read:
            return self._restored
        return self._get_value()

    def _get_value(self) -> Any:
        """Get the value for this sensor from statistics."""
        raise NotImplementedError("Subclasses must implement this method")

    def internal_update(self):
        """Override parent method to ensure statistics are refreshed."""
        _LOGGER.debug(f"Updating sensor {self.entity_id}")
        if self.hass is not None:
            self.async_write_ha_state()


# Unit of the product counters per system language. Home Assistant takes
# translated units only from the English file, so the unit is set here.
PRODUCT_UNITS = {"de": "Bezüge"}


class JuraProductUnitSensor(JuraStatisticsSensor):
    """Statistics sensor counting products ("Bezüge" in German)."""

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit in the system language."""
        lang = (self.hass.config.language if self.hass else None) or "en"
        return PRODUCT_UNITS.get(lang.split("-")[0].lower(), "products")


class JuraTotalCoffeeSensor(JuraProductUnitSensor):
    """Sensor for total coffee count."""

    _attr_icon = "mdi:coffee"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, device):
        """Initialize the sensor."""
        super().__init__(device, "total_product")

    def _get_value(self) -> int:
        """Get the total coffee count."""
        value = self.device.statistics.get("total_products", 0)
        _LOGGER.debug(f"Total coffee value: {value}")
        return value


class JuraProductCountSensor(JuraProductUnitSensor):
    """Sensor for individual product count."""

    _attr_icon = "mdi:coffee-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, device, product_name: str, text: str | None = None):
        """Initialize the sensor."""
        self.product_name = product_name
        attr_name = f"product_{product_name.lower().replace(' ', '_')}"
        super().__init__(device, attr_name)
        if text in PRODUCT_TEXTS:
            # the name the JURA app and the machine display use
            self._attr_translation_key = f"product_{text}"
        else:
            self._attr_translation_key = "product_count"
            self._attr_translation_placeholders = {"product": product_name}

    def _get_value(self) -> int:
        """Get the count for this specific product."""
        value = self.device.statistics.get("product_counts", {}).get(
            self.product_name, None
        )
        _LOGGER.debug(f"Product {self.product_name} count: {value}")
        return value


# Text numbers of the products in the JURA machine files. Names per language
# come from the JURA J.O.E. app (string "joe_<number>", app 4.6.16) and are in
# translations/*.json as "product_<number>".
PRODUCT_TEXTS = frozenset({"8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "52", "53", "73", "74", "75", "76", "77", "86", "87", "149", "150", "151", "152", "153", "154", "155", "156", "157", "160", "283", "284", "317", "340", "356", "357", "406", "408"})


MAINTENANCE_NAMES = {
    "Cleaning": "Cleaning",
    "FilterChange": "Filter Change",
    "Decalc": "Descaling",
    "CoffeeRinse": "Coffee Rinse",
    "CappuRinse": "Milk System Rinse",
    "CappuClean": "Milk System Cleaning",
}


class JuraMaintenanceSensor(JuraStatisticsSensor):
    """Maintenance counter (times done) or percent (progress until due)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, kind: str, mtype: str):
        self.kind = kind
        self.mtype = mtype
        name = MAINTENANCE_NAMES.get(mtype, mtype)
        if kind == "counters":
            attr = f"maintenance_count_{mtype.lower()}"
            self._attr_icon = "mdi:counter"
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            label = f"{name} Count"
        else:
            attr = f"maintenance_percent_{mtype.lower()}"
            self._attr_icon = "mdi:progress-wrench"
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = PERCENTAGE
            label = f"{name} Percent"
        super().__init__(device, attr)
        if mtype not in MAINTENANCE_NAMES:
            self._attr_name = label  # no translation for unknown types

    def _get_value(self) -> int | None:
        return self.device.statistics.get(f"maintenance_{self.kind}", {}).get(
            self.mtype
        )


class JuraAlertSensor(JuraEntity, RestoreSensor):
    """Sensor for machine alerts."""

    _attr_icon = "mdi:alert"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "alert"]

    def __init__(self, device):
        """Initialize the sensor."""
        super().__init__(device, "alerts")
        self._attr_extra_state_attributes = {"active_alerts": []}

        # Register for updates on alerts
        device.register_alert_update(self.internal_update)

    async def async_added_to_hass(self) -> None:
        """Keep the last alerts while the machine is off."""
        await super().async_added_to_hass()
        if not self.device.alerts_read and (last := await self.async_get_last_state()):
            if last.state in self._attr_options:
                self._restored = last.state
                self._attr_extra_state_attributes = {
                    "active_alerts": last.attributes.get("active_alerts", [])
                }
                self.async_write_ha_state()

    _restored = None

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.device.alerts_read and self._restored:
            return self._restored
        return self._get_value()

    def _get_value(self) -> str:
        """Get the alert status."""
        active_alerts = []
        # Filter out specific alert bits that we don't want to show
        filtered_bits = {12, 13, 36, 37, 148, 149, 150, 151}
        for bit, name in self.device.active_alerts.items():
            if bit not in filtered_bits:
                active_alerts.append({"bit": bit, "name": name})
        self._attr_extra_state_attributes["active_alerts"] = active_alerts
        return "alert" if active_alerts else "ok"

    def internal_update(self):
        """Override parent method to ensure alerts are refreshed."""
        _LOGGER.debug(f"Updating alert sensor {self.entity_id}")
        if self.hass is not None:
            self.async_write_ha_state()
