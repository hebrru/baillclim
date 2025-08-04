import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import create_baillclim_coordinator
from .utils import create_authenticated_session

_LOGGER = logging.getLogger(__name__)


class BaillclimClimate(CoordinatorEntity, ClimateEntity):
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 30.0

    def __init__(self, coordinator, thermostat, reg_id):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._id = thermostat.get("id")
        self._name = thermostat.get("name", f"Thermostat {self._id}").strip()
        self._attr_name = f"Climatiseur {self._name}"
        self._attr_unique_id = f"baillclim_climate_{self._reg_id}_{self._id}"

    @property
    def _thermostat_data(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for t in reg_data.get("thermostats", []):
                        if t.get("id") == self._id:
                            return t
        except Exception as e:
            _LOGGER.warning("Erreur lecture thermostat_data : %s", e)
        return {}

    @property
    def hvac_mode(self):
        if self._thermostat_data.get("is_on") is None:
            return HVACMode.OFF
        return HVACMode.AUTO if self._thermostat_data.get("is_on") else HVACMode.OFF

    @property
    def target_temperature_high(self):
        return self._thermostat_data.get("setpoint_cool_t1")

    @property
    def target_temperature_low(self):
        return self._thermostat_data.get("setpoint_hot_t1")

    @property
    def current_temperature(self):
        return self._thermostat_data.get("temperature")

    @property
    def extra_state_attributes(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._reg_id:
                    mode = reg_data.get("uc_mode", 0)
                    MODES = {
                        0: "Arrêt",
                        1: "Froid",
                        2: "Chauffage",
                        3: "Désumidificateur",
                        4: "Ventilation"
                    }
                    return {
                        "uc_mode": mode,
                        "mode_nom": MODES.get(mode, "Inconnu")
                    }
        except Exception as e:
            _LOGGER.warning("Erreur extra_state_attributes : %s", e)
        return {}

    async def async_set_hvac_mode(self, hvac_mode):
        is_on = hvac_mode != HVACMode.OFF
        await self._set_api_value(f"thermostats.{self._id}.is_on", is_on)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        if "target_temp_high" in kwargs:
            await self._set_api_value(f"thermostats.{self._id}.setpoint_cool_t1", kwargs["target_temp_high"])
        if "target_temp_low" in kwargs:
            await self._set_api_value(f"thermostats.{self._id}.setpoint_hot_t1", kwargs["target_temp_low"])
        await self.coordinator.async_request_refresh()

    async def _set_api_value(self, key, value):
        def sync_send():
            try:
                session = create_authenticated_session(
                    email=self.coordinator.config_entry.data["email"],
                    password=self.coordinator.config_entry.data["password"],
                    reg_id=self._reg_id
                )
                url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
                response = session.post(url, json={key: value}, timeout=10)

                if response.status_code == 200:
                    _LOGGER.info("✅ Requête API réussie : %s = %s", key, value)
                else:
                    _LOGGER.warning("❌ Échec requête API (%s = %s) : %s", key, value, response.text)
            except Exception as e:
                _LOGGER.error("Erreur dans _set_api_value : %s", e)

        await self.hass.async_add_executor_job(sync_send)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = create_baillclim_coordinator(hass, entry.data["email"], entry.data["password"])
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        _LOGGER.error("❌ coordinator.data est vide.")
        return

    data = coordinator.data.get("data", {})
    regulations = data.get("regulations", [])

    entities = []
    for reg in regulations:
        reg_data = reg.get("data", {})
        reg_id = reg_data.get("id")
        if reg_id is None:
            continue
        for th in reg_data.get("thermostats", []):
            entities.append(BaillclimClimate(coordinator, th, reg_id))

    async_add_entities(entities)
