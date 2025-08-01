
import logging
import requests
import re
import urllib.parse

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGIN_URL, REGULATIONS_URL, COMMAND_URL

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
    async_add_entities([BaillclimModeSelect(email, password)], True)


class BaillclimModeSelect(SelectEntity):
    def __init__(self, email, password):
        self._attr_name = "Mode Climatisation"
        self._attr_options = list(MODES.keys())
        self._attr_current_option = None
        self._email = email
        self._password = password

    def _login_and_get_session(self):
        session = requests.Session()

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

        regulations_page = session.get(REGULATIONS_URL)
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
            "Referer": REGULATIONS_URL
        })

        return session

    def select_option(self, option: str) -> None:
        if option not in MODES:
            _LOGGER.warning("Mode inconnu : %s", option)
            return

        try:
            session = self._login_and_get_session()
            payload = { "uc_mode": MODES[option] }
            response = session.post(COMMAND_URL, json=payload)
            if response.status_code == 200:
                self._attr_current_option = option
                _LOGGER.info("Mode changé vers : %s", option)
            else:
                _LOGGER.warning("Échec changement mode : %s", response.text)
        except Exception as e:
            _LOGGER.error("Erreur select_option : %s", e)

    def update(self):
        try:
            session = self._login_and_get_session()
            res = session.get(REGULATIONS_URL)
            if res.status_code == 200:
                match = re.search(r"uc_mode:\s*(\d+)", res.text)
                if match:
                    mode_code = int(match.group(1))
                    reverse_modes = {v: k for k, v in MODES.items()}
                    current_mode = reverse_modes.get(mode_code)
                    if current_mode:
                        self._attr_current_option = current_mode
                        _LOGGER.debug("Mode détecté : %s", current_mode)
        except Exception as e:
            _LOGGER.warning("Erreur récupération mode : %s", e)
