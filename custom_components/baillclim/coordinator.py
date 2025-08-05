import logging
import re
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)


def create_baillclim_coordinator(hass: HomeAssistant, email: str, password: str,
                                  update_interval: timedelta = timedelta(seconds=60),
                                  timeout: int = 15):
    async def async_update_data():
        def fetch_data():
            SessionManager.initialize(email, password, reg_id=0, timeout=timeout)
            session = SessionManager.get_session()

            regulations = []

            reg_list_page = session.get("https://www.baillconnect.com/client/regulations", timeout=timeout)
            reg_ids = set(re.findall(r"/client/regulations/(\d+)", reg_list_page.text))

            for reg_id in reg_ids:
                try:
                    SessionManager.initialize(email, password, reg_id=int(reg_id), timeout=timeout)
                    session = SessionManager.get_session()
                    url = f"https://www.baillconnect.com/api-client/regulations/{reg_id}"
                    response = session.post(url, json={}, timeout=timeout)
                    data = response.json()
                    data["id"] = int(reg_id)
                    regulations.append(data)
                except Exception as e:
                    _LOGGER.warning("⚠️ Erreur régulation %s : %s", reg_id, e)

            return {"data": {"regulations": regulations}}

        return await hass.async_add_executor_job(fetch_data)

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=update_interval,
    )
