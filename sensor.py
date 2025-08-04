import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.config_entry = entry

    if not coordinator.data:
        _LOGGER.error("❌ Aucune donnée récupérée pour initialiser les capteurs.")
        return

    entities = [DebugBaillclimSensor(coordinator)]

    data = coordinator.data.get("data", {})

    if isinstance(data, dict):
        for reg in data.get("regulations", []):
            reg_data = reg.get("data", {})
            reg_id = reg_data.get("id")
            if reg_id is None:
                continue

            for th in reg_data.get("thermostats", []):
                tid = th.get("id")
                name = th.get("name", f"Thermostat {tid}" if tid else "Inconnu").strip()
                if tid is not None:
                    entities.append(ThermostatTemperatureSensor(coordinator, reg_id, tid, name))
    else:
        _LOGGER.warning("❌ Aucune régulation détectée dans les données : %s", data)

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
    def __init__(self, coordinator, reg_id, tid, name):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._tid = tid
        self._attr_name = f"Température {name}"
        self._attr_unique_id = f"baillclim_temp_{reg_id}_{tid}"
        self._attr_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"

    @property
    def state(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for th in reg_data.get("thermostats", []):
                        if th.get("id") == self._tid:
                            return th.get("temperature")
        except Exception as e:
            _LOGGER.warning(
                "⚠️ Erreur récupération température (reg_id=%s, tid=%s) : %s", self._reg_id, self._tid, e
            )
        return None

    @property
    def device_info(self):
        return {
            'identifiers': {(DOMAIN, f'baillclim_reg_{self._reg_id}')},
            'name': f'BaillClim Régulation {self._reg_id}',
            'manufacturer': 'BaillConnect',
            'model': 'Régulation',
            'entry_type': 'service'
        }
