import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import create_baillclim_coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = create_baillclim_coordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        _LOGGER.error("❌ Aucune donnée récupérée pour initialiser les sensors")
        return

    entities = [DebugBaillclimSensor(coordinator)]

    thermostats = coordinator.data.get("data", {}).get("thermostats", [])
    for th in thermostats:
        tid = th.get("id")
        name = th.get("name", f"Thermostat {tid}").strip()
        if tid is not None:
            entities.append(ThermostatTemperatureSensor(coordinator, tid, name))

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
        try:
            thermostats = self.coordinator.data.get("data", {}).get("thermostats", [])
            for th in thermostats:
                if th.get("id") == self._tid:
                    return th.get("temperature")
        except Exception as e:
            _LOGGER.warning("Erreur récupération température pour thermostat %s : %s", self._tid, e)
        return None
