from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PranaFanType, PranaSwitchType, PranaSensorType
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)

class PranaCoordinator(DataUpdateCoordinator):
    """Universal coordinator for Prana integration (fan, switch, sensor, etc)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, prana_config: str) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN} Coordinator",
            update_interval=timedelta(seconds=10),
            update_method=self._async_update_data,
            config_entry=entry,
        )
        self.entry = entry
        self.max_speed = None
        self.parseConfig(prana_config)


    
    async def _async_update_data(self):
        """Fetch all data from the device for all platforms."""
        _LOGGER.warning("Fetching data from Prana device...")
        try:

            # TODO: Replace with real fetch logic
            # Example: return await self.client.get_all_states()
                max_speed = 5  # Replace with dynamic value if needed
                state = self.hex_string_to_int_list(await self.async_get_state())

                parsed_state ={
                    PranaFanType.EXTRACT: {"speed": state[25] // 10 if state[23] == 1 else 0, "is_on": state[23] == 1 , "max_speed": self.max_speed},
                    PranaFanType.SUPPLY: {"speed": state[21] // 10 if state[19] == 1 else 0, "is_on": state[19] == 1, "max_speed": self.max_speed},
                    PranaFanType.BOUNDED: {"speed": state[17] // 10 if state[15] == 1 else 0, "is_on": state[15] == 1, "max_speed": self.max_speed},
                    PranaSwitchType.BOUND: state[13] == 1,
                    PranaSwitchType.HEATER: state[5] == 1,
                    PranaSwitchType.AUTO: state[11] == 1,
                    PranaSwitchType.AUTO_PLUS: state[11] == 2,
                    PranaSwitchType.WINTER: state[33] == 1,
                    PranaSensorType.INSIDE_TEMPERATURE: self.parse_temperature(state[45], state[46]),
                    PranaSensorType.INSIDE_TEMPERATURE_2: self.parse_temperature(state[48], state[49]),
                    PranaSensorType.OUTSIDE_TEMPERATURE: self.parse_temperature(state[42], state[43]),
                    PranaSensorType.OUTSIDE_TEMPERATURE_2: self.parse_temperature(state[39], state[40]),
                    PranaSensorType.HUMIDITY: self.parse_sensor_value(state[51], 0, False),
                    PranaSensorType.VOC: self.parse_sensor_value(state[54], state[55], True),
                    PranaSensorType.AIR_PRESSURE: self.parse_sensor_value(state[68], state[69], True),
                    PranaSensorType.CO2: self.parse_sensor_value(state[52], state[53], True),

                }

                _LOGGER.warning(f"End fetching data from Prana device. {parsed_state}")

                return parsed_state
                
        except Exception as err:
            raise UpdateFailed(f"Error updating Prana device: {err}")

    def parseConfig(self, config: str) -> None:
        config_list_int = self.hex_string_to_int_list(config)
        self.max_speed = config_list_int[61] // 10

    async def async_get_state(self):
        async with ClientSession() as session:
            async with session.get(f"http://{self.entry.data.get('host')}:12345/getState") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["state"]
                else:
                    raise Exception(f"Error {resp.status}")
    
        
    def hex_string_to_int_list(self, hex_str: str) -> list[int]:
        # Remove spaces and make sure it's uppercase (optional)
        hex_str = hex_str.replace(" ", "").strip()
        
        # Split every 2 characters and convert to int
        return [int(hex_str[i:i+2], 16) for i in range(0, len(hex_str), 2)]
    
    def parse_sensor_value(self, high_byte: int, low_byte: int, is_16bit: bool):
        """Parse sensor value from high/low bytes."""
        data = (high_byte << 8) + low_byte if is_16bit else high_byte

        mask = 0x8000 if is_16bit else 0x80
        value_mask = 0x7FFF if is_16bit else 0x7F

        if (data & mask) == mask:
            return data & value_mask
        return None
  
    def parse_temperature(self, high_byte: int, low_byte: int):
        data = (high_byte << 8) + low_byte

        if (data & 0x8000) == 0x8000:
            sign = -1 if (data & 0x4000) == 0x4000 else 1
            return sign * ((data & 0x3FFF) / 10)
        else:
            return None
