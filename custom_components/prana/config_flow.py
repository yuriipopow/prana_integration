from pathlib import Path
import aiohttp
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.components import zeroconf
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

import asyncio
from typing import Any
import logging

from .const import CONF_CONFIG, CONF_MDNS

DOMAIN = "prana"
SERVICE_TYPE = "_prana._tcp.local."

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class PranaConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Prana integration via mDNS discovery."""
    VERSION = 1

    def __init__(self):
        self.discovered_hosts = {}
        self.discovered_hosts_config = {}
        self.discovered_mdns = {}

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> data_entry_flow.FlowResult:
        """Handle mDNS discovery."""
        _LOGGER.debug(f"Discovered device via Zeroconf: {discovery_info}")

        
        configured_mdns = {
            entry.data.get(CONF_MDNS)
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }

        

        _LOGGER.debug(f"Configured mDNS names: {configured_mdns}")

        
        name = discovery_info.name
        host = discovery_info.host



        if discovery_info.type != SERVICE_TYPE:
            return self.async_abort(reason="not_prana_device")

        elif name in configured_mdns:
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if name == entry.data.get(CONF_MDNS) and discovery_info.host != entry.data.get(CONF_HOST):
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={**entry.data, CONF_HOST: discovery_info.host}
                    )
                    _LOGGER.debug(f"Updated host for {name} to {discovery_info.host}")
            if name in configured_mdns:
                return self.async_abort(reason="already_configured")
        
        
        


        name = discovery_info.properties.get("label") or host
        config = discovery_info.properties.get("config", {})
    

        self.discovered_hosts[host] = name
        self.discovered_hosts_config[host] = config
        self.discovered_mdns[host] = discovery_info.name
        return await self.async_step_select_device()

    async def async_step_user(self, user_input: dict | None = None) -> data_entry_flow.FlowResult:
        """Step for manual integration start."""
        return await self.async_step_select_device(user_input)

    async def async_step_select_device(self, user_input: dict | None = None) -> data_entry_flow.FlowResult:
        """Let user select one of discovered devices."""
        if not self.discovered_hosts:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            selected_label = user_input[CONF_NAME]
            selected_host = None
            for host, label in self.discovered_hosts.items():
                if label == selected_label:
                    selected_host = host
                    break
            if selected_host is None:
                return self.async_abort(reason="device_not_found")
            await self.async_set_unique_id(self.discovered_mdns[selected_host])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=selected_label,
                data={CONF_NAME: selected_label, CONF_HOST: selected_host, CONF_CONFIG: self.discovered_hosts_config[selected_host], CONF_MDNS: self.discovered_mdns[selected_host]},
                options={},
                description_placeholders={},

            )

        return self.async_show_form(
            step_id="select_device",
            data_schema=self._get_device_schema(),
            description_placeholders={},
        )

    def _get_device_schema(self):
        """Return schema for device selection as 'Name (IP)' choices."""
        import voluptuous as vol
        # Only show labels to user
        return vol.Schema({
            vol.Required(CONF_NAME): vol.In(list(self.discovered_hosts.values())),
        })
    
    async def async_get_suggestions(hass, config_entry):
    # Завантажуємо твій YAML
        from homeassistant.util.yaml import load_yaml
        yaml_path = Path(__file__).parent / "dashboard" / "prana_dashboard.yaml"
        dashboard_yaml = load_yaml(yaml_path)

        return [
            {
                "title": "Ventilation Panel",
                "cards": dashboard_yaml
            }
        ]

    





 
