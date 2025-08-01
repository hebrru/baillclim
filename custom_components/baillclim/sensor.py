import logging
import re
import aiohttp
import asyncio

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from datetime import timedelta

from .const import DOMAIN, LOGIN_URL, REGULATIONS_URL, COMMAND_URL

_LOGGER = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MODES = {
    0: "Arrêt",
    1: "Froid",
    2: "Chauffage",
    3: "Désumidificateur",
    4: "Ventilation"
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    async def fetch_data():
        try:
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(LOGIN_URL) as resp:
                    html = await resp.text()
                token = re.search(r'name="_token" value="([^"]+)"', html)
                if not token:
                    raise Exception("Token CSRF non trouvé")
                token_val = token.group(1)

                payload = {
                    "_token": token_val,
                    "email": email,
                    "password": password
                }
                headers_login = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": LOGIN_URL
                }
                async with session.post(LOGIN_URL, data=payload, headers=headers_login, allow_redirects=True) as resp2:
                    if "client/connexion" in str(resp2.url):
                        raise Exception("Login échoué")

                async with session.get(REGULATIONS_URL) as resp3:
                    html = await resp3.text()
                csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
                if not csrf_token:
                    raise Exception("Token X-CSRF non trouvé")
                token_val = csrf_token.group(1)

                session.headers.update({
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRF-TOKEN": token_val
                })

                async with session.post(COMMAND_URL) as final:
                    data = await final.json()
                return data
        except Exception as e:
            _LOGGER.error("❌ Erreur récupération sensor : %s", e)
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_sensor",
        update_method=fetch_data,
        update_interval=timedelta(seconds=10),
    )

    await coordinator.async_config_entry_first_refresh()

    entities = [
        ModeClimSensor(coordinator, coordinator.data.get("data", {}).get("uc_mode", -1)),
        DebugBaillclimSensor(coordinator)
    ]

    thermostats = coordinator.data.get("data", {}).get("thermostats", [])
    for th in thermostats:
        tid = th.get("id")
        if XXXXXX <= tid <= XXXXXXXX:  #<<<<<<<<<<<<<<<<<<<<<<<<<<< A MODIFIER AVEC VOTRE ID
            name = th.get("name", f"Thermostat {tid}")
            temp = th.get("temperature")
            is_on = th.get("is_on", None)

            if temp is not None:
                entities.append(ThermostatTemperatureSensor(coordinator, tid, name, temp))
            if is_on is not None:
                entities.append(ThermostatOnOffSensor(coordinator, tid, name))

    async_add_entities(entities)


class ModeClimSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, uc_mode):
        super().__init__(coordinator)
        self._attr_name = "Mode Clim Réel"
        self._attr_unique_id = "baillclim_mode"
        self._state = MODES.get(uc_mode, "Inconnu")

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Indisponible"
        uc_mode = data.get("data", {}).get("uc_mode", -1)
        return MODES.get(uc_mode, "Inconnu")


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
    def __init__(self, coordinator, tid, name, temperature):
        super().__init__(coordinator)
        self._tid = tid
        self._attr_name = f"Température {name.strip()}"
        self._attr_unique_id = f"baillclim_temp_{tid}"
        self._attr_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"

    @property
    def state(self):
        data = self.coordinator.data.get("data", {})
        thermostats = data.get("thermostats", [])
        for th in thermostats:
            if th.get("id") == self._tid:
                return th.get("temperature")
        return None


class ThermostatOnOffSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, tid, name):
        super().__init__(coordinator)
        self._tid = tid
        self._attr_name = f"Thermostat {name.strip()} (État)"
        self._attr_unique_id = f"baillclim_is_on_{tid}"
        self._attr_icon = "mdi:toggle-switch"

    @property
    def state(self):
        data = self.coordinator.data.get("data", {})
        thermostats = data.get("thermostats", [])
        for th in thermostats:
            if th.get("id") == self._tid:
                return "on" if th.get("is_on") else "off"
        return "Indisponible"
