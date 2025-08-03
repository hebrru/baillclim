import logging
import re
import urllib.parse
import requests

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGIN_URL, COMMAND_URL
from .coordinator import create_baillclim_coordinator

_LOGGER = logging.getLogger(__name__)


class BaillclimClimate(CoordinatorEntity, ClimateEntity):
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 30.0

    def __init__(self, coordinator, thermostat):
        super().__init__(coordinator)
        self._id = thermostat["id"]
        self._name = thermostat["name"].strip()
        self._attr_name = f"Climatiseur {self._name}"
        self._attr_unique_id = f"baillclim_climate_{self._id}"

    @property
    def _thermostat_data(self):
        for t in self.coordinator.data.get("data", {}).get("thermostats", []):
            if t.get("id") == self._id:
                return t
        return {}

    @property
    def hvac_mode(self):
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
        mode = self.coordinator.data.get("data", {}).get("uc_mode", 0)
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

    async def async_set_hvac_mode(self, hvac_mode):
        is_on = hvac_mode != HVACMode.OFF
        await self._set_api_value(f"thermostats.{self._id}.is_on", is_on)
        await self.coordinator.async_request_refresh()
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        if "target_temp_high" in kwargs:
            await self._set_api_value(f"thermostats.{self._id}.setpoint_cool_t1", kwargs["target_temp_high"])
        await self.coordinator.async_request_refresh()
        if "target_temp_low" in kwargs:
            await self._set_api_value(f"thermostats.{self._id}.setpoint_hot_t1", kwargs["target_temp_low"])
        await self.coordinator.async_request_refresh()
        await self.coordinator.async_request_refresh()

    async def _set_api_value(self, key, value):
        def sync_send():
            session = requests.Session()

            # 1. Login
            login_page = session.get(LOGIN_URL)
            token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
            session.post(LOGIN_URL, data={
                "_token": token,
                "email": self.coordinator.config_entry.data["email"],
                "password": self.coordinator.config_entry.data["password"]
            })

            # 2. Lire ID régulation dynamique
            regulations_id = self.coordinator.data.get("data", {}).get("id")
            if not regulations_id:
                raise Exception("❌ regulations_id manquant dans les données")

            regulations_url = f"https://www.baillconnect.com/client/regulations/{regulations_id}"

            # 3. Lire les tokens nécessaires
            regulations_page = session.get(regulations_url)
            csrf = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text).group(1)
            xsrf = urllib.parse.unquote(session.cookies.get("XSRF-TOKEN"))

            # 4. Headers et POST
            session.headers.update({
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "X-CSRF-TOKEN": csrf,
                "X-XSRF-TOKEN": xsrf,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.baillconnect.com",
                "Referer": regulations_url
            })

            session.post(COMMAND_URL, json={key: value})

        await self.hass.async_add_executor_job(sync_send)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = create_baillclim_coordinator(hass, entry.data["email"], entry.data["password"])
    coordinator.config_entry = entry
    await coordinator.async_config_entry_first_refresh()

    entities = []
    thermostats = coordinator.data.get("data", {}).get("thermostats", [])
    for th in thermostats:
        entities.append(BaillclimClimate(coordinator, th))

    async_add_entities(entities)
