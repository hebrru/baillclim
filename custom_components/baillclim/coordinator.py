import logging
import re  # ✅ Import nécessaire
from datetime import timedelta
from requests.exceptions import RequestException, ConnectionError

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .utils import create_authenticated_session

_LOGGER = logging.getLogger(__name__)


def create_baillclim_coordinator(hass: HomeAssistant, email: str, password: str):
    async def async_update_data():
        try:
            def sync_fetch():
                regulations = []

                # 🔐 Connexion initiale (récupération de la page listant les régulations)
                session = create_authenticated_session(email, password, 0)
                reg_list_page = session.get("https://www.baillconnect.com/client/regulations", timeout=10)

                # 🔍 Recherche des IDs de régulations via regex
                reg_ids = set(re.findall(r"/client/regulations/(\d+)", reg_list_page.text))
                if not reg_ids:
                    raise Exception("❌ Aucune régulation détectée dans la page de liste.")

                for reg_id in reg_ids:
                    try:
                        session = create_authenticated_session(email, password, reg_id)
                        url = f"https://www.baillconnect.com/api-client/regulations/{reg_id}"
                        response = session.post(url, json={}, timeout=10)
                        response.raise_for_status()
                        data = response.json()
                        data["id"] = int(reg_id)  # 🔧 ID injecté si absent
                        regulations.append(data)
                    except (ConnectionError, RequestException) as e:
                        _LOGGER.warning("⚠️ Erreur POST pour régulation %s : %s", reg_id, e)
                    except Exception as e:
                        _LOGGER.error("❌ Erreur récupération régulation %s : %s", reg_id, e)

                if not regulations:
                    raise Exception("❌ Aucune régulation récupérée correctement.")

                return {"data": {"regulations": regulations}}

            return await hass.async_add_executor_job(sync_fetch)

        except Exception as err:
            _LOGGER.error("❌ Erreur récupération données coordinator : %s", err)
            return None

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )
