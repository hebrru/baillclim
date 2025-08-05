import logging
import re
import requests
import urllib.parse

_LOGGER = logging.getLogger(__name__)


class SessionManager:
    _session = None
    _csrf_token = None
    _xsrf_token = None

    @classmethod
    def initialize(cls, email: str, password: str, reg_id: int = 0, timeout: int = 15):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        login_page = session.get("https://www.baillconnect.com/client/connexion", timeout=timeout)
        token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
        if not token_match:
            raise Exception("❌ Token _token introuvable.")
        login_token = token_match.group(1)

        response = session.post("https://www.baillconnect.com/client/connexion", data={
            "_token": login_token,
            "email": email,
            "password": password
        }, timeout=timeout)

        if response.status_code not in (200, 302):
            raise Exception("❌ Authentification échouée.")

        if reg_id:
            regulations_url = f"https://www.baillconnect.com/client/regulations/{reg_id}"
            page = session.get(regulations_url, timeout=timeout)

            csrf_token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page.text)
            xsrf_cookie = session.cookies.get("XSRF-TOKEN")

            if not csrf_token or not xsrf_cookie:
                raise Exception("❌ Token CSRF/XSRF manquant.")

            cls._csrf_token = csrf_token.group(1)
            cls._xsrf_token = urllib.parse.unquote(xsrf_cookie)

            session.headers.update({
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "X-CSRF-TOKEN": cls._csrf_token,
                "X-XSRF-TOKEN": cls._xsrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://www.baillconnect.com",
                "Referer": regulations_url
            })

        cls._session = session
        _LOGGER.info("✅ Session BaillConnect initialisée")

    @classmethod
    def get_session(cls) -> requests.Session:
        if cls._session is None:
            raise Exception("❌ Session non initialisée.")
        return cls._session
