from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

import logging
from .tools import Tools
from .const import CONF_CONFIG, CONF_MDNS

DOMAIN = "prana"
SERVICE_TYPE = "_prana._tcp.local."

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Prana integration via mDNS discovery."""
    VERSION = 1

    def __init__(self) -> None:
        # Store a single discovered device for this flow (one flow per device)
        self._host: str | None = None
        self._name: str | None = None
        self._config: dict | str | None = None
        self._mdns: str | None = None

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> data_entry_flow.FlowResult:
        """Handle mDNS discovery."""
        _LOGGER.debug("Discovered device via Zeroconf: %s", discovery_info)

        if discovery_info.type != SERVICE_TYPE:
            return self.async_abort(reason="not_prana_device")

        name = discovery_info.name
        host = discovery_info.host

        # Set a stable unique ID so the discovery card can offer "Ignore"
        await self.async_set_unique_id(name)
        # If already configured, update host and abort
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Extract friendly name from the config blob
        raw_config = discovery_info.properties.get("config", "")
        friendly_name = self._get_name_from_config(raw_config) or name or "Prana"

        # Set placeholders so the discovery card subtitle shows device name
        self.context["title_placeholders"] = {"name": friendly_name}

        # Keep details for confirm step
        self._host = host
        self._name = friendly_name
        self._config = raw_config
        self._mdns = name

        return await self.async_step_confirm()

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> data_entry_flow.FlowResult:
        """Manual start is not supported for discovery-only flow."""
        return self.async_abort(reason="no_devices_found")

    async def async_step_confirm(
        self, user_input: dict | None = None
    ) -> data_entry_flow.FlowResult:
        """Confirmation step with a single Submit button."""
        # Safety: ensure we have discovery data
        if not all([self._host, self._name, self._mdns]):
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_NAME: self._name,
                    CONF_HOST: self._host,
                    CONF_CONFIG: self._config,
                    CONF_MDNS: self._mdns,
                },
                options={},
                description_placeholders={},
            )

        # Empty form -> shows only a Submit button
        return self.async_show_form(step_id="confirm")



    def _get_name_from_config(self, config: str) -> str:
        bytes_ = Tools.hex_string_to_int_list(config)
        _LOGGER.debug("Byte array from config: %s", bytes_)
        data = bytearray(bytes_[8:32])
        _LOGGER.debug("Name bytes from config: %s", data)
        name = data.decode("ascii").rstrip("\x00")
        if name.startswith("PRN"):
            name = name[7:]
        return name