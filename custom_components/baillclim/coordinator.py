import logging
import re
import urllib.parse
import requests

from datetime import timedelta
from requests.exceptions import RequestException, ConnectionError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGIN_URL

_LOGGER = logging.getLogger(__name__)


def get_authenticated_session(email, password):
    session = requests.Session()

    # 1. Page de login → récupération token CSRF
    login_page = session.get(LOGIN_URL)
    token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
    if not token_match:
        raise Exception("Token _token introuvable")
    login_token = token_match.group(1)

    # 2. Connexion
    login_response = session.post(LOGIN_URL, data={
        "_token": login_token,
        "email": email,
        "password": password
    }, allow_redirects=True)

    if login_response.status_code not in (200, 302):
        raise Exception(f"Erreur login : {login_response.status_code}")
    if "client/connexion" in login_response.url:
        raise Exception("Login échoué")

    # 3. Récupération de l’ID de régulation
    match = re.search(r"/client/regulations/(\d+)", login_response.url)
    if not match:
        raise Exception("Impossible de trouver regulations_id dans l'URL de redirection après login")
    regulations_id = match.group(1)
    regulations_url = f"https://www.baillconnect.com/client/regulations/{regulations_id}"
    command_url = f"https://www.baillconnect.com/api-client/regulations/{regulations_id}"

    # 4. Page de régulation → récupération CSRF token
    regulations_page = session.get(regulations_url)
    token_csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)">', regulations_page.text)
    if not token_csrf_match:
        raise Exception("Token CSRF non trouvé")
    x_csrf_token = token_csrf_match.group(1)

    # 5. Cookie XSRF
    xsrf_token_cookie = session.cookies.get("XSRF-TOKEN")
    if not xsrf_token_cookie:
        raise Exception("Cookie XSRF-TOKEN manquant")
    x_xsrf_token = urllib.parse.unquote(xsrf_token_cookie)

    # 6. Headers obligatoires
    session.headers.update({
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "X-CSRF-TOKEN": x_csrf_token,
        "X-XSRF-TOKEN": x_xsrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://www.baillconnect.com",
        "Referer": regulations_url
    })

    return session, regulations_id, command_url


def create_baillclim_coordinator(hass: HomeAssistant, email: str, password: str):
    async def async_update_data():
        try:
            def sync_fetch():
                session, regulations_id, command_url = get_authenticated_session(email, password)

                try:
                    # ✅ Important : envoie un JSON vide pour éviter les erreurs
                    response = session.post(command_url, json={})
                    response.raise_for_status()
                except (ConnectionError, RequestException) as e:
                    raise Exception(f"Erreur lors de l'appel POST : {e}")

                _LOGGER.debug("📥 Données JSON reçues : %s", response.text)
                data = response.json()
                data["id"] = regulations_id
                return data

            return await hass.async_add_executor_job(sync_fetch)

        except Exception as err:
            _LOGGER.error("❌ Erreur récupération données coordinator : %s", err)
            return None

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=10),
    )
