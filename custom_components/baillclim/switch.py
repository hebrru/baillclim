import logging
import requests
import re
import urllib.parse

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import create_baillclim_coordinator

_LOGGER = logging.getLogger(__name__)


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, zone_id, zone_name, email, password):
        super().__init__(coordinator)
        self._id = zone_id
        self._name = zone_name
        self._email = email
        self._password = password
        self._attr_name = f"Zone {self._name} Active"
        self._attr_unique_id = f"baillclim_zone_{self._id}"
        self._attr_icon = "mdi:vector-polyline"

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def is_on(self):
        try:
            zones = self.coordinator.data.get("data", {}).get("zones", [])
            for zone in zones:
                if zone.get("id") == self._id:
                    return zone.get("mode") == 3
        except Exception as e:
            _LOGGER.warning("Erreur accès is_on pour zone %s : %s", self._id, e)
        return False

    def _set_zone_mode(self, value: int):
        try:
            regulations_id = self.coordinator.data.get("data", {}).get("id")
            if not regulations_id:
                raise Exception("❌ regulations_id manquant dans les données du coordinator")

            session = requests.Session()
            session.headers.update({"User-Agent": "Mozilla/5.0"})

            # 🔑 Connexion
            login_page = session.get("https://www.baillconnect.com/client/connexion")
            token = re.search(r'name="_token" value="([^"]+)"', login_page.text).group(1)
            session.post("https://www.baillconnect.com/client/connexion", data={
                "_token": token,
                "email": self._email,
                "password": self._password
            })

            # 🔐 Récupération des tokens sécurisés
            regulations_url = f"https://www.baillconnect.com/client/regulations/{regulations_id}"
            regulations_page = session.get(regulations_url)
            csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)">', regulations_page.text).group(1)
            xsrf_token = urllib.parse.unquote(session.cookies.get("XSRF-TOKEN"))

            session.headers.update({
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "X-CSRF-TOKEN": csrf_token,
                "X-XSRF-TOKEN": xsrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.baillconnect.com",
                "Referer": regulations_url
            })

            url = f"https://www.baillconnect.com/api-client/regulations/{regulations_id}"
            payload = {f"zones.{self._id}.mode": value}
            response = session.post(url, json=payload)

            if response.status_code == 200:
                _LOGGER.info("✅ Zone %s mode changé vers %s", self._id, value)
            else:
                _LOGGER.warning("❌ Échec changement zone %s : %s", self._id, response.text)

        except Exception as e:
            _LOGGER.error("❌ Erreur lors du changement d'état de la zone %s : %s", self._id, e)

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 3)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 0)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = create_baillclim_coordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.data:
        _LOGGER.error("❌ Données manquantes : impossible de configurer les zones")
        return

    entities = []
    zones = coordinator.data.get("data", {}).get("zones", [])
    for zone in zones:
        zone_id = zone.get("id")
        name = zone.get("name", f"Zone {zone_id}")
        if zone_id is not None:
            entities.append(ZoneSwitch(coordinator, zone_id, name.strip(), email, password))

    async_add_entities(entities)
