from __future__ import annotations
import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, PranaFanType, PranaSwitchType
from .coordinator import PranaCoordinator
from aiohttp import ClientSession
from homeassistant.helpers.device_registry import DeviceInfo
from .switch import PranaSendSwitch


"""Fan platform for Prana integration."""



from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
    FanEntityDescription,
)


_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

class PranaSendSpeed:
    def __init__(self, fan_type: PranaFanType, coordinator: PranaCoordinator):
        self.fan_type = fan_type
        self.coordinator = coordinator

    async def send_speed_percentage(self, percentage: int):
        request_data = {
            "speed": percentage,
            "fanType": self.fan_type
        }

        async with ClientSession() as session:
            async with session.post(f"http://{self.coordinator.entry.data.get('host')}:12345/setSpeed", json=request_data) as resp:
                if resp.status == 200:
                    pass
                else:
                    raise Exception(f"Error {resp.status}")
    async def send_speed_is_on(self, value):
        request_data = {
            "value": value,
            "fanType": self.fan_type
        }
        async with ClientSession() as session:
            async with session.post(f"http://{self.coordinator.entry.data.get('host')}:12345/setSpeedIsOn", json=request_data) as resp:
                if resp.status == 200:
                    pass
                else:
                    raise Exception(f"Error {resp.status}")


class PranaFan(FanEntity):
    _attr_has_entity_name = True
    _attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.PRESET_MODE 
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "fan"
    _attr_unique_id: str

    from homeassistant.helpers.device_registry import DeviceInfo

    def __init__(self, unique_id: str, name: str, coordinator: PranaCoordinator, fan_type: PranaFanType, entry: ConfigEntry) -> None:
        self._attr_unique_id = unique_id
        self._attr_name = name
        self.coordinator = coordinator
        self._attr_is_on = False
        self._attr_percentage = 0
        self.fan_type = fan_type
        self._attr_preset_modes = ["Night", "Boost"]
    
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name", "Prana Device"),
            manufacturer="Prana",
            model="PRANA RECUPERATOR",
        )
        self._attr_icon = self.get_icon()

    def get_icon(self):
        if self.fan_type == PranaFanType.EXTRACT:
            return "mdi:arrow-expand-right"
        elif self.fan_type == PranaFanType.SUPPLY:
            return "mdi:arrow-expand-left"
        elif self.fan_type == PranaFanType.BOUNDED:
            return "mdi:arrow-expand-horizontal"
        return "mdi:help"

    @property
    def is_on(self) -> bool:
        """Return True if the fan is on."""
        if self.coordinator.data:
            return self.coordinator.data.get(self.fan_type, {}).get("is_on", False)
        return False

    @property
    def speed_count(self) -> int:
        return self.coordinator.data.get(self.fan_type, {}).get("max_speed", 10)

    
    async def async_set_preset_mode(self, preset_mode):
        send_switch = None

        if preset_mode == "Night":
            send_switch = PranaSendSwitch(True, PranaSwitchType.NIGHT, coordinator=self.coordinator)

        elif preset_mode == "Boost":
            send_switch = PranaSendSwitch(True, PranaSwitchType.BOOST, coordinator=self.coordinator)

        if send_switch:
            await send_switch.send()
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

        

    @property
    def percentage(self) -> int | None:
        """Return the current speed as percentage."""
        _LOGGER.debug(f"Getting percentage for {self.name} ({self.fan_type})")
        if self.coordinator.data:
            speed = self.coordinator.data.get(self.fan_type, {}).get("speed")
            if speed is not None:
                return int(speed * 10)
        return None

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        self._attr_is_on = True
        send_speed_is_on = PranaSendSpeed(self.fan_type, self.coordinator)
        await send_speed_is_on.send_speed_is_on(True)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        send_speed_is_on = PranaSendSpeed(self.fan_type, self.coordinator)
        await send_speed_is_on.send_speed_is_on(False)
        await self.coordinator.async_refresh()

    async def async_added_to_hass(self):

        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))



    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug(f"Setting {self.name} ({self.fan_type}) speed to {percentage}%")
        send_speed_percentage = PranaSendSpeed(self.fan_type, self.coordinator)
        await send_speed_percentage.send_speed_percentage(percentage)
        await self.coordinator.async_refresh()
        self._attr_percentage = percentage

        self._attr_is_on = percentage > 0
        self.async_write_ha_state()

    @property
    def available(self) -> bool:

        if self.fan_type == PranaFanType.BOUNDED:
            return self.coordinator.data.get("bound")
        else:
            return not self.coordinator.data.get("bound")

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Prana fan entities from config entry."""
    _LOGGER.info("Setting up Prana fan entities... ")
    _LOGGER.debug(f"Config entry: {entry.data}")
    coordinator: PranaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
    PranaFan(unique_id=f"{entry.entry_id}-extractfan", name="Extract Speed", coordinator=coordinator, fan_type=PranaFanType.EXTRACT, entry=entry),
    PranaFan(unique_id=f"{entry.entry_id}-supplyfan", name="Supply Speed", coordinator=coordinator, fan_type=PranaFanType.SUPPLY, entry=entry),
    PranaFan(unique_id=f"{entry.entry_id}-boundedfan", name="Bounded Speed", coordinator=coordinator, fan_type=PranaFanType.BOUNDED, entry=entry),
])
