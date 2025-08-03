
import logging
import re
import urllib.parse
import requests

from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from .const import DOMAIN, LOGIN_URL, REGULATIONS_URL, COMMAND_URL

_LOGGER = logging.getLogger(__name__)

def get_authenticated_session(email, password):
    session = requests.Session()
    login_page = session.get(LOGIN_URL)
    token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
    if not token_match:
        raise Exception("Token _token introuvable")
    login_token = token_match.group(1)

    login_data = {
        "_token": login_token,
        "email": email,
        "password": password
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

def create_baillclim_coordinator(hass: HomeAssistant, email: str, password: str):
    async def async_update_data():
        try:
            def sync_fetch():
                session = get_authenticated_session(email, password)
                response = session.post(COMMAND_URL)
                raw = response.json()

                data = raw.get("data", {})
                result = {}

                # Stocker les infos principales
                result["uc_mode"] = data.get("uc_mode")
                result["uc_hot_min"] = data.get("uc_hot_min")
                result["uc_hot_max"] = data.get("uc_hot_max")
                result["uc_cold_min"] = data.get("uc_cold_min")
                result["uc_cold_max"] = data.get("uc_cold_max")

                # Extraire les thermostats
                for th in data.get("thermostats", []):
                    tid = th["id"]
                    result[f"thermostats.{tid}.is_on"] = th.get("is_on", False)
                    result[f"thermostats.{tid}.temperature"] = th.get("temperature")
                    result[f"thermostats.{tid}.setpoint_cool_t1"] = th.get("setpoint_cool_t1")
                    result[f"thermostats.{tid}.setpoint_hot_t1"] = th.get("setpoint_hot_t1")
                    result[f"thermostats.{tid}.name"] = th.get("name", f"Thermostat {tid}")

                return result

            data = await hass.async_add_executor_job(sync_fetch)
            return data
        except Exception as err:
            _LOGGER.error("Erreur lors de la récupération des données thermostats : %s", err)
            return {}

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=25),
    )
