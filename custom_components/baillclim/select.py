import logging
import re
import urllib.parse
import requests

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGIN_URL, COMMAND_URL
from .coordinator import create_baillclim_coordinator

_LOGGER = logging.getLogger(__name__)

MODES = {
    "Arrêt": 0,
    "Froid": 1,
    "Chauffage": 2,
    "Désumidificateur": 3,
    "Ventilation": 4
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = create_baillclim_coordinator(hass, email, password)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([BaillclimModeSelect(coordinator, email, password)], True)


class BaillclimModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, email: str, password: str):
        super().__init__(coordinator)
        self._email = email
        self._password = password
        self._attr_name = "Mode Climatisation"
        self._attr_unique_id = "baillclim_mode_general"
        self._attr_options = list(MODES.keys())
        self._attr_current_option = None

    @property
    def current_option(self):
        try:
            uc_mode = self.coordinator.data.get("data", {}).get("uc_mode")
            reverse_modes = {v: k for k, v in MODES.items()}
            return reverse_modes.get(uc_mode)
        except Exception as e:
            _LOGGER.warning("Erreur accès current_option : %s", e)
            return None

    def select_option(self, option: str) -> None:
        """Écriture via API"""
        if option not in MODES:
            _LOGGER.warning("Mode inconnu : %s", option)
            return

        try:
            session = requests.Session()

            # 🔑 LOGIN
            login_page = session.get(LOGIN_URL)
            token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
            if not token_match:
                raise Exception("Token _token introuvable")
            login_token = token_match.group(1)

            login_data = {
                "_token": login_token,
                "email": self._email,
                "password": self._password
            }

            login_response = session.post(LOGIN_URL, data=login_data)
            if login_response.status_code not in (200, 302):
                raise Exception(f"Erreur login : {login_response.status_code}")
            if "client/connexion" in login_response.url:
                raise Exception("Login échoué")

            # 🔄 Récupération ID dynamique
            regulations_id = self.coordinator.data.get("data", {}).get("id")
            if not regulations_id:
                raise Exception("ID regulations introuvable dans coordinator")

            regulations_url = f"https://www.baillconnect.com/client/regulations/{regulations_id}"
            regulations_page = session.get(regulations_url)
            token_csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text)
            if not token_csrf_match:
                raise Exception("Token CSRF non trouvé")
            x_csrf_token = token_csrf_match.group(1)

            xsrf_token_cookie = session.cookies.get("XSRF-TOKEN")
            if not xsrf_token_cookie:
                raise Exception("Cookie XSRF-TOKEN manquant")
            x_xsrf_token = urllib.parse.unquote(xsrf_token_cookie)

            session.headers.update({
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "X-CSRF-TOKEN": x_csrf_token,
                "X-XSRF-TOKEN": x_xsrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.baillconnect.com",
                "Referer": regulations_url
            })

            payload = {"uc_mode": MODES[option]}
            response = session.post(COMMAND_URL, json=payload)
            if response.status_code == 200:
                _LOGGER.info("✅ Mode changé via API : %s", option)
                self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning("❌ Échec changement mode : %s", response.text)
        except Exception as e:
            _LOGGER.error("Erreur lors du changement de mode : %s", e)
