from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .core.device import AUTO_OFF, AUTO_OFF_ARGUMENT
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    entities: list = [JuraSelect(device, select) for select in device.selects()]
    entities.append(JuraAutoOffSelect(device, "auto_off"))
    add_entities(entities)


class JuraSelect(JuraEntity, SelectEntity):
    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        self._attr_current_option = attribute.get("default")
        self._attr_options = attribute.get("options", [])
        self._attr_available = "default" in attribute

        if self.hass:
            self._async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        self.device.select_option(self.attr, option)
        self._attr_current_option = option
        self._async_write_ha_state()


class JuraAutoOffSelect(JuraEntity, SelectEntity, RestoreEntity):
    """Auto-off timer (experimental).

    The machine does not report the timer, so the state is the last value
    set from Home Assistant, unknown until then.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:timer-off-outline"
    _attr_options = list(AUTO_OFF)
    _attr_assumed_state = True
    _attr_current_option = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in AUTO_OFF:
            self._attr_current_option = last.state
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        if not await self.device.write_setting(AUTO_OFF_ARGUMENT, AUTO_OFF[option]):
            raise HomeAssistantError("Machine not reachable, timer not set")
        self._attr_current_option = option
        self.async_write_ha_state()
