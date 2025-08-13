from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .coordinator import PranaCoordinator
from .const import PranaSwitchType
from aiohttp import ClientSession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry



class PranaSendSwitch:
    def __init__(self, value: bool, switch_type: PranaSwitchType, coordinator: PranaCoordinator):
        self.value = value
        self.switch_type = switch_type
        self.coordinator = coordinator

    async def send(self):
        request_data = {
            "switchType": self.switch_type,
            "value": self.value
        }

        async with ClientSession() as session:
            async with session.post(f"http://{self.coordinator.entry.data.get('host')}:12345/setSwitch", json=request_data) as resp:
                if resp.status == 200:
                    pass
                else:
                    raise Exception(f"Error {resp.status}")


class PranaSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "switch"

    def __init__(self, unique_id: str, name: str, coordinator: PranaCoordinator, switch_key: str, switch_type: PranaSwitchType, entry: ConfigEntry) -> None:
        self._attr_unique_id = unique_id
        self._attr_name = name
        self.coordinator = coordinator
        self.switch_key = switch_key

        self.switch_type = switch_type
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get("name", "Prana Device"),
            manufacturer="Prana",
            model="PRANA RECUPERATOR",
        )
        self._attr_icon = self.get_icon()

    def get_icon(self):
        if self.switch_type == PranaSwitchType.BOUND:
            return "mdi:link"
        elif self.switch_type == PranaSwitchType.HEATER:
            return "mdi:radiator"
        elif self.switch_type == PranaSwitchType.AUTO or self.switch_type == PranaSwitchType.AUTO_PLUS:
            return "mdi:fan-auto"
        elif self.switch_type == PranaSwitchType.WINTER:
            return "mdi:snowflake"
        return "mdi:help"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get(self.switch_type)

    async def async_turn_on(self, **kwargs):
        prana_send_switch = PranaSendSwitch(True, self.switch_type, self.coordinator)
        await prana_send_switch.send()
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs):
        prana_send_switch = PranaSendSwitch(False, self.switch_type, self.coordinator)
        await prana_send_switch.send()
        await self.coordinator.async_refresh()

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: PranaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        PranaSwitch(unique_id=f"{entry.entry_id}-bound", name="Bound", coordinator=coordinator, switch_key="bounded", switch_type=PranaSwitchType.BOUND, entry=entry),
        PranaSwitch(unique_id=f"{entry.entry_id}-heater", name="Heater", coordinator=coordinator, switch_key="heater", switch_type=PranaSwitchType.HEATER, entry=entry),
        PranaSwitch(unique_id=f"{entry.entry_id}-auto", name="Auto", coordinator=coordinator, switch_key="Auto", switch_type=PranaSwitchType.AUTO, entry=entry),
        PranaSwitch(unique_id=f"{entry.entry_id}-auto_plus", name="Auto Plus", coordinator=coordinator, switch_key="Auto Plus", switch_type=PranaSwitchType.AUTO_PLUS, entry=entry),
        PranaSwitch(unique_id=f"{entry.entry_id}-winter", name="Winter", coordinator=coordinator, switch_key="winter", switch_type=PranaSwitchType.WINTER, entry=entry),
    ])
