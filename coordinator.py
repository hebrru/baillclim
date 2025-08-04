import logging
import re
from datetime import timedelta
from requests.exceptions import RequestException, ConnectionError

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .utils import create_authenticated_session

_LOGGER = logging.getLogger(__name__)


def create_baillclim_coordinator(
    hass: HomeAssistant,
    email: str,
    password: str,
    update_interval: timedelta = timedelta(seconds=60),  # 🔁 Valeur par défaut
    timeout: int = 15  # ⏱️ Timeout par défaut
):
    """Crée un DataUpdateCoordinator pour récupérer les données BaillConnect."""

    async def async_update_data():
        try:
            def sync_fetch():
                regulations = []

                # 🔐 Connexion initiale pour récupérer les régulations disponibles
                session = create_authenticated_session(
                    email=email,
                    password=password,
                    reg_id=0,
                    timeout=timeout
                )
                reg_list_page = session.get("https://www.baillconnect.com/client/regulations", timeout=timeout)

                reg_ids = set(re.findall(r"/client/regulations/(\d+)", reg_list_page.text))
                if not reg_ids:
                    raise Exception("❌ Aucune régulation détectée dans la page de liste.")

                for reg_id in reg_ids:
                    try:
                        session = create_authenticated_session(
                            email=email,
                            password=password,
                            reg_id=int(reg_id),
                            timeout=timeout
                        )
                        url = f"https://www.baillconnect.com/api-client/regulations/{reg_id}"
                        response = session.post(url, json={}, timeout=timeout)
                        response.raise_for_status()
                        data = response.json()
                        data["id"] = int(reg_id)
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
        update_interval=update_interval,
    )
