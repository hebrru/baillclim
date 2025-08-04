import logging
import requests
import re
import urllib.parse

_LOGGER = logging.getLogger(__name__)


def create_authenticated_session(email: str, password: str, reg_id: int = 0) -> requests.Session:
    """Crée une session authentifiée pour BaillConnect.
    
    Si reg_id > 0, configure les headers pour les requêtes API sécurisées.
    """
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        # 🔐 Étape 1 : Token _token pour le formulaire de login
        login_page = session.get("https://www.baillconnect.com/client/connexion", timeout=10)
        token_match = re.search(r'name="_token" value="([^"]+)"', login_page.text)
        if not token_match:
            raise Exception("❌ Token _token introuvable sur la page de connexion.")
        login_token = token_match.group(1)

        # 🔐 Étape 2 : Connexion
        login_response = session.post(
            "https://www.baillconnect.com/client/connexion",
            data={"_token": login_token, "email": email, "password": password},
            timeout=10
        )

        if login_response.status_code not in (200, 302) or "client/connexion" in login_response.url:
            raise Exception("❌ Échec de connexion à BaillConnect")

        # 🧱 Si reg_id == 0 → utilisé uniquement pour explorer la liste des régulations
        if not reg_id:
            return session

        # 🔐 Étape 3 : Récupération des tokens CSRF/XSRF pour cette régulation
        regulations_url = f"https://www.baillconnect.com/client/regulations/{reg_id}"
        regulations_page = session.get(regulations_url, timeout=10)

        csrf_token_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', regulations_page.text)
        xsrf_cookie = session.cookies.get("XSRF-TOKEN")

        if not csrf_token_match or not xsrf_cookie:
            raise Exception(f"❌ Tokens CSRF ou XSRF manquants pour régulation {reg_id}")

        x_csrf_token = csrf_token_match.group(1)
        x_xsrf_token = urllib.parse.unquote(xsrf_cookie)

        # 🔐 Étape 4 : Headers pour les requêtes API POST
        session.headers.update({
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-CSRF-TOKEN": x_csrf_token,
            "X-XSRF-TOKEN": x_xsrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.baillconnect.com",
            "Referer": regulations_url
        })

        return session

    except Exception as e:
        _LOGGER.error("❌ Erreur lors de la création de session (reg_id=%s) : %s", reg_id, e)
        raise
