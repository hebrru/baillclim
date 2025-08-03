import logging
import re
import aiohttp
from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGIN_URL, REGULATIONS_URL, COMMAND_URL

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    # Création du coordinator
    coordinator = create_baillclim_coordinator(hass, email, password)
    await coordinator.async_refresh()

    if coordinator.data is None:
        _LOGGER.warning("BaillClim coordinator data is None during setup.")
        thermostats = []
    else:
        thermostats = coordinator.data.get("data", {}).get("thermostats", [])
        _LOGGER.debug(f"BaillClim thermostats data: {thermostats}")

    entities = [DebugBaillclimSensor(coordinator)]

    for th in thermostats:
        tid = th.get("id")
        name = th.get("name", f"Thermostat {tid}")
        if tid is not None and "temperature" in th:
            entities.append(ThermostatTemperatureSensor(coordinator, tid, name.strip()))

    async_add_entities(entities)


class DebugBaillclimSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Debug BaillConnect Data"
        self._attr_unique_id = "baillclim_debug_data"
        self._attr_icon = "mdi:code-json"

    @property
    def state(self):
        return "OK" if self.coordinator.data else "Indisponible"

    @property
    def extra_state_attributes(self):
        return self.coordinator.data or {}


class ThermostatTemperatureSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, tid, name):
        super().__init__(coordinator)
        self._tid = tid
        self._attr_name = f"Température {name}"
        self._attr_unique_id = f"baillclim_temp_{tid}"
        self._attr_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"

    @property
    def state(self):
        if self.coordinator.data is None:
            return None
        data = self.coordinator.data.get("data", {})
        thermostats = data.get("thermostats", [])
        for th in thermostats:
            if th.get("id") == self._tid:
                return th.get("temperature")
        return None
