
import logging
import requests
import re
import urllib.parse

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGIN_URL, REGULATIONS_URL, COMMAND_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]
    zones = await hass.async_add_executor_job(fetch_zones, email, password)

    entities = [ZoneSwitch(z, email, password) for z in zones]
    async_add_entities(entities)


def fetch_zones(email, password):
    session = requests.Session()
    login_page = session.get(LOGIN_URL)
    token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
    session.post(LOGIN_URL, data={"_token": token, "email": email, "password": password})
    regulations_page = session.get(REGULATIONS_URL)
    csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text).group(1)
    xsrf_token = urllib.parse.unquote(session.cookies.get("XSRF-TOKEN"))
    session.headers.update({
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "X-CSRF-TOKEN": csrf_token,
        "X-XSRF-TOKEN": xsrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.baillconnect.com",
        "Referer": REGULATIONS_URL
    })

    data = session.post(COMMAND_URL).json()
    return data.get("data", {}).get("zones", [])


class ZoneSwitch(SwitchEntity):
    def __init__(self, zone, email, password):
        self._id = zone["id"]
        self._name = zone["name"]
        self._is_on = zone.get("mode") == 3
        self._email = email
        self._password = password

    @property
    def name(self):
        return f"Zone {self._name} Active"

    @property
    def unique_id(self):
        return f"baillclim_zone_{self._id}"

    @property
    def is_on(self):
        return self._is_on

    def _set_zone_mode(self, value):
        session = requests.Session()
        login_page = session.get(LOGIN_URL)
        token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
        session.post(LOGIN_URL, data={"_token": token, "email": self._email, "password": self._password})
        regulations_page = session.get(REGULATIONS_URL)
        csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text).group(1)
        xsrf_token = urllib.parse.unquote(session.cookies.get("XSRF-TOKEN"))
        session.headers.update({
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-CSRF-TOKEN": csrf_token,
            "X-XSRF-TOKEN": xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.baillconnect.com",
            "Referer": REGULATIONS_URL
        })
        session.post(COMMAND_URL, json={f"zones.{self._id}.mode": value})

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 3)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 0)
        self._is_on = False
        self.async_write_ha_state()
