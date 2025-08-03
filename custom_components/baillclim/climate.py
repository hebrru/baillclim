import logging
import re
import requests
import urllib.parse
import asyncio

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGIN_URL, REGULATIONS_URL, COMMAND_URL

_LOGGER = logging.getLogger(__name__)

MODES = {
    "Arrêt": 0,
    "Froid": 1,
    "Chauffage": 2,
    "Désumidificateur": 3,
    "Ventilation": 4
}

class BaillclimClimate(ClimateEntity):
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 30.0

    def __init__(self, thermostat_data, email, password):
        self._id = thermostat_data["id"]
        self._email = email
        self._password = password
        name = thermostat_data.get("name", f"Thermostat {self._id}").strip()
        self._attr_name = f"Climatiseur {name}"
        self._attr_unique_id = f"baillclim_climate_{self._id}"
        self._hvac_mode = HVACMode.AUTO if thermostat_data.get("is_on") else HVACMode.OFF
        self._target_temp_high = thermostat_data.get("setpoint_cool_t1")
        self._target_temp_low = thermostat_data.get("setpoint_hot_t1")
        self._current_temp = thermostat_data.get("temperature")
        self._is_on = thermostat_data.get("is_on", False)
        self._uc_mode = thermostat_data.get("uc_mode", 0)
        self._pending_temp_task = None
        self._last_temp_high = None
        self._last_temp_low = None

    @property
    def hvac_mode(self):
        return HVACMode.AUTO if self._is_on else HVACMode.OFF

    @property
    def target_temperature_high(self):
        return self._target_temp_high

    @property
    def target_temperature_low(self):
        return self._target_temp_low

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def extra_state_attributes(self):
        return {
            "uc_mode": self._uc_mode,
            "mode_nom": next((k for k, v in MODES.items() if v == self._uc_mode), "Inconnu")
        }

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        self._is_on = hvac_mode != HVACMode.OFF
        await self._set_api_value(f"thermostats.{self._id}.is_on", self._is_on)

    async def async_set_temperature(self, **kwargs):
        self._last_temp_high = kwargs.get("target_temp_high", self._target_temp_high)
        self._last_temp_low = kwargs.get("target_temp_low", self._target_temp_low)

        if self._pending_temp_task:
            self._pending_temp_task.cancel()

        self._pending_temp_task = asyncio.create_task(self._delayed_send_temperature())

    async def _delayed_send_temperature(self):
        try:
            await asyncio.sleep(1)
            if self._is_on:
                if self._last_temp_high is not None:
                    self._target_temp_high = self._last_temp_high
                    await self._set_api_value(f"thermostats.{self._id}.setpoint_cool_t1", self._last_temp_high)
                if self._last_temp_low is not None:
                    self._target_temp_low = self._last_temp_low
                    await self._set_api_value(f"thermostats.{self._id}.setpoint_hot_t1", self._last_temp_low)
                _LOGGER.debug(f"Température envoyée pour {self.name} : froid={self._last_temp_high}, chaud={self._last_temp_low}")
        except asyncio.CancelledError:
            _LOGGER.debug("Annulation en attente de température pour %s", self.name)

    async def async_update(self):
        def sync_update():
            session = self._authenticated_session()
            response = session.post(COMMAND_URL)
            data = response.json()
            for t in data.get("data", {}).get("thermostats", []):
                if t.get("id") == self._id:
                    return {
                        "temp": t.get("temperature"),
                        "is_on": t.get("is_on"),
                        "cool": t.get("setpoint_cool_t1"),
                        "hot": t.get("setpoint_hot_t1"),
                        "uc_mode": data.get("data", {}).get("uc_mode", 0)
                    }
            return None

        try:
            data = await self.hass.async_add_executor_job(sync_update)
            if data:
                self._current_temp = data["temp"]
                self._is_on = data["is_on"]
                self._target_temp_high = data["cool"]
                self._target_temp_low = data["hot"]
                self._uc_mode = data["uc_mode"]
                self._hvac_mode = HVACMode.AUTO if self._is_on else HVACMode.OFF
        except Exception as e:
            _LOGGER.error(f"Erreur update thermostat {self._id} : {e}")

    def _authenticated_session(self):
        session = requests.Session()
        login_page = session.get(LOGIN_URL)
        token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)

        login_data = {
            "_token": token,
            "email": self._email,
            "password": self._password
        }

        login_response = session.post(LOGIN_URL, data=login_data)
        if login_response.status_code not in (200, 302) or "client/connexion" in login_response.url:
            raise Exception("Échec de la connexion")

        regulations_page = session.get(REGULATIONS_URL)
        token_csrf = re.search(r'<meta name="csrf-token" content="([^"]+)">', regulations_page.text).group(1)
        xsrf_token_cookie = session.cookies.get("XSRF-TOKEN")
        x_xsrf_token = urllib.parse.unquote(xsrf_token_cookie)

        session.headers.update({
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-CSRF-TOKEN": token_csrf,
            "X-XSRF-TOKEN": x_xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.baillconnect.com",
            "Referer": REGULATIONS_URL
        })

        return session

    async def _set_api_value(self, key, value):
        def sync_set():
            try:
                session = self._authenticated_session()
                payload = {key: value}
                session.post(COMMAND_URL, json=payload)
            except Exception as e:
                _LOGGER.error(f"Erreur API pour {key} : {e}")

        try:
            await self.hass.async_add_executor_job(sync_set)
        except Exception as e:
            _LOGGER.error(f"Erreur API pour {key} : {e}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    def fetch_all_thermostats():
        session = requests.Session()
        login_page = session.get(LOGIN_URL)
        token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)

        login_data = {
            "_token": token,
            "email": email,
            "password": password
        }

        login_response = session.post(LOGIN_URL, data=login_data)
        if login_response.status_code not in (200, 302) or "client/connexion" in login_response.url:
            raise Exception("Échec de la connexion")

        regulations_page = session.get(REGULATIONS_URL)
        token_csrf = re.search(r'<meta name="csrf-token" content="([^"]+)">', regulations_page.text).group(1)
        xsrf_token_cookie = session.cookies.get("XSRF-TOKEN")
        x_xsrf_token = urllib.parse.unquote(xsrf_token_cookie)

        session.headers.update({
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-CSRF-TOKEN": token_csrf,
            "X-XSRF-TOKEN": x_xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.baillconnect.com",
            "Referer": REGULATIONS_URL
        })

        response = session.post(COMMAND_URL)
        data = response.json()
        return data.get("data", {}).get("thermostats", [])

    thermostats = await hass.async_add_executor_job(fetch_all_thermostats)

    entities = []
    for t in thermostats:
        if "id" in t and "name" in t:
            entities.append(BaillclimClimate(t, email, password))

    async_add_entities(entities)
