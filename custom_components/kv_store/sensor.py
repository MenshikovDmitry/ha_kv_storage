"""
Sensor platform for kv_store integration.
"""
import os
import json
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
import pathlib

from . import SENSORS
from .const import (
    DOMAIN,
    DEFAULT_STORE_NAME,
    ATTR_KEY,
    ATTR_VALUE,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)  # Set to DEBUG level for more verbose logging

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the kv_store sensors from discovery_info."""
    _LOGGER.debug(f"Setting up platform with discovery_info: {discovery_info}")
    
    if discovery_info is None:
        _LOGGER.warning("No discovery_info provided, skipping setup")
        return
    
    if "stores" not in discovery_info:
        _LOGGER.error(f"Invalid discovery_info: {discovery_info}, missing 'stores' key")
        return
    
    store_names = discovery_info["stores"]
    _LOGGER.info(f"Setting up sensors for stores: {store_names}")
    
    sensors = []
    for store_name in store_names:
        _LOGGER.debug(f"Creating sensor for store: {store_name}")
        file_name = f".storage/kv_store_{store_name}.json"
        file_path = hass.config.path(file_name)
        
        # Ensure the config directory exists and is writable
        config_dir = hass.config.path()
        if not os.path.exists(config_dir):
            _LOGGER.error(f"Config directory does not exist: {config_dir}")
            continue
        
        if not os.access(config_dir, os.W_OK):
            _LOGGER.error(f"Config directory is not writable: {config_dir}")
            continue
        
        sensor = KeyValueSensor(hass, file_path, store_name)
        await sensor.async_load_data()
        sensors.append(sensor)
        
        # Register in global registry for service access
        SENSORS[store_name] = sensor
        _LOGGER.info(f"Registered sensor for store: {store_name}")
    
    if sensors:
        _LOGGER.info(f"Adding {len(sensors)} entities: {[s._attr_name for s in sensors]}")
        async_add_entities(sensors, True)
    else:
        _LOGGER.warning("No sensors were created")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up kv_store sensors from a config entry."""
    _LOGGER.debug(f"Setting up from config entry: {entry.data}")
    
    store_names = entry.data.get("stores", [DEFAULT_STORE_NAME])
    _LOGGER.info(f"Setting up sensors for stores from config entry: {store_names}")
    
    sensors = []
    for store_name in store_names:
        file_name = f".storage/kv_store_{store_name}.json"
        file_path = hass.config.path(file_name)
        sensor = KeyValueSensor(hass, file_path, store_name)
        await sensor.async_load_data()
        sensors.append(sensor)
        # Register in global registry for service access
        SENSORS[store_name] = sensor
    
    if sensors:
        _LOGGER.info(f"Adding {len(sensors)} entities from config entry")
        async_add_entities(sensors, True)
    else:
        _LOGGER.warning("No sensors were created from config entry")

class KeyValueSensor(Entity):
    """Representation of a Key-Value Store sensor."""
    
    def __init__(self, hass, file_path, store_name):
        """Initialize the sensor."""
        self.hass = hass
        self._file_path = file_path
        self._store_name = store_name
        self._data = {}
        self._attr_name = f"{store_name}"  # Just use the store name for display
        self._attr_unique_id = f"kv_store_{store_name}"
        
        # Ensure the directory exists
        try:
            pathlib.Path(os.path.dirname(self._file_path)).mkdir(parents=True, exist_ok=True)
            _LOGGER.debug(f"Ensured directory exists for: {self._file_path}")
        except Exception as e:
            _LOGGER.error(f"Error creating directory for {self._file_path}: {e}")
        
        # Log initialization
        _LOGGER.info(f"Initializing KV Store sensor: {store_name} at {file_path}")

    async def async_load_data(self):
        """Load data from the persistence file."""
        def _load():
            if os.path.exists(self._file_path):
                with open(self._file_path, "r") as file:
                    return json.load(file)
            else:
                self._save_data()
                return {}
        try:
            self._data = await self.hass.async_add_executor_job(_load)
            _LOGGER.debug(f"Loaded data for {self._store_name}: {self._data}")
        except Exception as e:
            _LOGGER.error(f"Error loading data for {self._store_name}: {e}")
            self._data = {}

    async def async_save_data(self):
        """Save data to the persistence file asynchronously."""
        def _save():
            with open(self._file_path, "w") as file:
                json.dump(self._data, file)
        try:
            await self.hass.async_add_executor_job(_save)
            _LOGGER.debug(f"Saved data for {self._store_name}")
        except Exception as e:
            _LOGGER.error(f"Error saving data for {self._store_name}: {e}")

    def set_value(self, key, value):
        """Set a value in the store and update the entity."""
        _LOGGER.debug(f"Setting value {key}={value} in {self._store_name}")
        self._data[key] = value
        self.hass.async_create_task(self.async_save_data())
        self.async_schedule_update_ha_state()
        _LOGGER.info(f"Set {key}={value} in {self._store_name}")

    def delete_value(self, key):
        """Delete a value from the store and update the entity."""
        _LOGGER.debug(f"Deleting key {key} from {self._store_name}")
        if key in self._data:
            del self._data[key]
            self.hass.async_create_task(self.async_save_data())
            self.async_schedule_update_ha_state()
            _LOGGER.info(f"Deleted {key} from {self._store_name}")
        else:
            _LOGGER.warning(f"Key {key} not found in {self._store_name}")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return f"{len(self._data)} items"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._data

    @property
    def should_poll(self):
        """No polling needed."""
        return False
    
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:database"
    
    @property
    def device_class(self):
        """Return the device class."""
        return None
