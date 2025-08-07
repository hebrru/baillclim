import re
import logging
import requests
import urllib.parse
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)


class SessionManager:
    _session = None
    _csrf_token = None
    _xsrf_token = None
    _email = None
    _password = None
    _timeout = 15
    _last_cookie_refresh = None
    _cookie_ttl = timedelta(minutes=8)

    @classmethod
    async def async_initialize(cls, hass, email: str, password: str, reg_id: int = 0, timeout: int = 15):
        cls._email = email
        cls._password = password
        cls._timeout = timeout

        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers.update({"User-Agent": "HomeAssistant-BaillClim/1.0"})

        now = datetime.now()
        if cls._last_cookie_refresh is None or (now - cls._last_cookie_refresh > cls._cookie_ttl):
            await hass.async_add_executor_job(cls._refresh_cookie)

        if reg_id:
            await hass.async_add_executor_job(cls._initialize_for_regulation, reg_id)

    @classmethod
    def _refresh_cookie(cls):
        _LOGGER.debug("🔁 Tentative de vérification de la validité du cookie...")
        response = cls._session.get("https://www.baillconnect.com/client/connexion", timeout=cls._timeout)

        if response.status_code != 200:
            raise Exception(f"❌ Échec GET /connexion – code HTTP {response.status_code}")

        token_match = re.search(r'name="_token" value="([^"]+)"', response.text)
        if not token_match:
            _LOGGER.info("✅ Session toujours valide — pas de login nécessaire.")
            cls._last_cookie_refresh = datetime.now()
            return

        _LOGGER.debug("🔐 Reconnexion nécessaire, token trouvé dans page de login.")
        login_token = token_match.group(1)

        response = cls._session.post("https://www.baillconnect.com/client/connexion", data={
            "_token": login_token,
            "email": cls._email,
            "password": cls._password
        }, timeout=cls._timeout)

        if response.status_code not in (200, 302):
            raise Exception("❌ Authentification échouée.")

        cls._last_cookie_refresh = datetime.now()
        _LOGGER.info("🍪 Cookie renouvelé avec succès à %s", cls._last_cookie_refresh)

    @classmethod
    def _initialize_for_regulation(cls, reg_id: int):
        regulations_url = f"https://www.baillconnect.com/client/regulations/{reg_id}"
        page = cls._session.get(regulations_url, timeout=cls._timeout)

        csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)">', page.text)
        xsrf_cookie = cls._session.cookies.get("XSRF-TOKEN")

        if not csrf_token or not xsrf_cookie:
            raise Exception("❌ Token CSRF/XSRF manquant.")

        cls._csrf_token = csrf_token.group(1)
        cls._xsrf_token = urllib.parse.unquote(xsrf_cookie)

        cls._session.headers.update({
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-CSRF-TOKEN": cls._csrf_token,
            "X-XSRF-TOKEN": cls._xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.baillconnect.com",
            "Referer": regulations_url
        })

    @classmethod
    async def async_get_session(cls, hass) -> requests.Session:
        if cls._session is None:
            raise Exception("❌ Session non initialisée.")
        return cls._session
