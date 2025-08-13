import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .coordinator import PranaCoordinator
from .const import CONF_CONFIG

_LOGGER = logging.getLogger(__name__)

DOMAIN = "prana"
PLATFORMS = [Platform.FAN, Platform.SWITCH, Platform.SENSOR]
from homeassistant.exceptions import ConfigEntryNotReady

async def async_setup_entry(hass, entry):
    try:
        coordinator = PranaCoordinator(hass, entry, entry.data.get(CONF_CONFIG))
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Device not ready: {err}") from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Prana integration."""
    _LOGGER.info("Unloading Prana integration...")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok