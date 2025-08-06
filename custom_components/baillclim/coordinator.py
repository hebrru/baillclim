import logging
import re
import time
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)

def create_baillclim_coordinator(hass: HomeAssistant, email: str, password: str,
                                  update_interval: timedelta = timedelta(seconds=60),
                                  timeout: int = 25):
    async def async_update_data():
        def fetch_data():
            SessionManager.initialize(email, password, reg_id=0, timeout=timeout)
            session = SessionManager.get_session()

            regulations = []

            MAX_RETRIES = 3
            for attempt in range(MAX_RETRIES):
                try:
                    reg_list_page = session.get("https://www.baillconnect.com/client/regulations", timeout=timeout)
                    reg_ids = set(re.findall(r"/client/regulations/(\d+)", reg_list_page.text))
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2)
                        continue
                    _LOGGER.warning("❌ Impossible de récupérer la liste des régulations : %s", e)
                    return {"data": {"regulations": []}}

            for reg_id in reg_ids:
                for attempt in range(MAX_RETRIES):
                    try:
                        SessionManager._initialize_for_regulation(int(reg_id))
                        session = SessionManager.get_session()
                        url = f"https://www.baillconnect.com/api-client/regulations/{reg_id}"
                        response = session.post(url, json={}, timeout=timeout)

                        if response.status_code != 200 or not response.content:
                            _LOGGER.warning("🔄 Session possiblement expirée, tentative de reconnexion")
                            SessionManager._refresh_cookie()
                            session = SessionManager.get_session()
                            response = session.post(url, json={}, timeout=timeout)

                        data = response.json()
                        data["id"] = int(reg_id)
                        regulations.append(data)
                        break  # success → stop retrying

                    except Exception as e:
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2)
                            continue
                        _LOGGER.warning("⚠️ Erreur régulation %s : %s", reg_id, e)

                time.sleep(1)  # 💤 Délai anti-flood API

            return {"data": {"regulations": regulations}}

        return await hass.async_add_executor_job(fetch_data)

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=update_interval,
    )
