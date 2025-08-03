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

    # 1. Get CSRF token from login page
    login_page = session.get(LOGIN_URL)
    token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
    if not token_match:
        raise Exception("Token _token introuvable")
    login_token = token_match.group(1)

    # 2. Login
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

    # 3. Get CSRF token from regulations page
    regulations_page = session.get(REGULATIONS_URL)
    token_csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text)
    if not token_csrf_match:
        raise Exception("Token CSRF non trouvé")
    x_csrf_token = token_csrf_match.group(1)

    # 4. Get cookie XSRF
    xsrf_token_cookie = session.cookies.get("XSRF-TOKEN")
    if not xsrf_token_cookie:
        raise Exception("Cookie XSRF-TOKEN manquant")
    x_xsrf_token = urllib.parse.unquote(xsrf_token_cookie)

    # 5. Set headers
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
                _LOGGER.debug("📥 Données JSON reçues : %s", response.text)
                return response.json()
            return await hass.async_add_executor_job(sync_fetch)

        except Exception as err:
            _LOGGER.error("❌ Erreur récupération données coordinator : %s", err)
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    return coordinator