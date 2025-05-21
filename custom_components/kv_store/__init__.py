"""
Custom integration to manage a key-value store as a sensor in Home Assistant.
"""

import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.discovery import async_load_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import template

from .const import (
    DOMAIN,
    DEFAULT_STORE_NAME,
    SERVICE_SET,
    SERVICE_DELETE,
    ATTR_KEY,
    ATTR_VALUE,
    ATTR_STORE_NAME,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)  # Set to DEBUG level for more verbose logging

# Service schema
SERVICE_SET_SCHEMA = vol.Schema({
    vol.Required(ATTR_KEY): cv.string,
    vol.Required(ATTR_VALUE): cv.match_all,
    vol.Required(ATTR_STORE_NAME): cv.string,
})

SERVICE_DELETE_SCHEMA = vol.Schema({
    vol.Required(ATTR_KEY): cv.string,
    vol.Required(ATTR_STORE_NAME): cv.string,
})

# Global registry of sensors to update when services are called
SENSORS = {}

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up kv_store from configuration.yaml."""
    _LOGGER.debug(f"Setting up {DOMAIN} integration with config: {config.get(DOMAIN)}")
    
    if DOMAIN not in config:
        _LOGGER.debug(f"{DOMAIN} not found in configuration, using default")
        store_names = [DEFAULT_STORE_NAME]
    else:
        store_names = config.get(DOMAIN)
        if not store_names:
            _LOGGER.debug(f"{DOMAIN} configuration is empty, using default")
            store_names = [DEFAULT_STORE_NAME]
        elif isinstance(store_names, str):
            _LOGGER.debug(f"{DOMAIN} configuration is a string: {store_names}")
            store_names = [store_names]
        elif not isinstance(store_names, list):
            _LOGGER.debug(f"{DOMAIN} configuration is not a list, converting: {store_names}")
            store_names = [store_names]
    
    _LOGGER.info(f"Setting up {DOMAIN} with stores: {store_names}")

    # Forward setup to the sensor platform
    hass.async_create_task(
        async_load_platform(
            hass,
            "sensor",
            DOMAIN,
            {"stores": store_names},
            config
        )
    )

    # Register global services
    async def set_service(call):
        # Get values from call data
        key_template = call.data.get(ATTR_KEY)
        value_template = call.data.get(ATTR_VALUE)
        store_name_template = call.data.get(ATTR_STORE_NAME)
        
        # Render templates
        key = template.Template(key_template, hass).async_render()
        value = template.Template(str(value_template), hass).async_render()
        store_name = template.Template(store_name_template, hass).async_render()
        
        # Extract store name from entity ID if needed
        if store_name.startswith("sensor."):
            store_name = store_name.split(".", 1)[1]
        
        _LOGGER.debug(f"Service call: set {key}={value} in store {store_name}")
        
        if store_name in SENSORS:
            sensor = SENSORS[store_name]
            sensor.set_value(key, value)
            _LOGGER.info(f"Set {key}={value} in store {store_name}")
        else:
            _LOGGER.error(f"Store {store_name} not found. Available stores: {list(SENSORS.keys())}")

    async def delete_service(call):
        # Get values from call data
        key_template = call.data.get(ATTR_KEY)
        store_name_template = call.data.get(ATTR_STORE_NAME)
        
        # Render templates
        key = template.Template(key_template, hass).async_render()
        store_name = template.Template(store_name_template, hass).async_render()
        
        # Extract store name from entity ID if needed
        if store_name.startswith("sensor."):
            store_name = store_name.split(".", 1)[1]
        
        _LOGGER.debug(f"Service call: delete {key} from store {store_name}")
        
        if store_name in SENSORS:
            sensor = SENSORS[store_name]
            sensor.delete_value(key)
            _LOGGER.info(f"Deleted {key} from store {store_name}")
        else:
            _LOGGER.error(f"Store {store_name} not found. Available stores: {list(SENSORS.keys())}")

    hass.services.async_register(
        DOMAIN, SERVICE_SET, set_service, schema=SERVICE_SET_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE, delete_service, schema=SERVICE_DELETE_SCHEMA
    )

    _LOGGER.info(f"{DOMAIN} integration setup completed")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up kv_store from a config entry (UI)."""
    _LOGGER.debug(f"Setting up {DOMAIN} from config entry: {entry.data}")
    store_names = entry.data.get("stores", [DEFAULT_STORE_NAME])
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True