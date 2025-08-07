import logging
import re
import time
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)

def create_baillclim_coordinator(
    hass: HomeAssistant,
    email: str,
    password: str,
    update_interval: timedelta = timedelta(seconds=60),
    timeout: int = 25
):
    async def async_update_data():
        async def fetch_data():
            # ✅ Initialisation complète via méthode async (corrige bug session non initialisée)
            await SessionManager.async_initialize(hass, email, password, reg_id=0, timeout=timeout)
            session = await SessionManager.async_get_session(hass)

            regulations = []
            MAX_RETRIES = 3

            # 🔁 Récupération de la liste des régulations
            for attempt in range(MAX_RETRIES):
                try:
                    reg_list_page = await hass.async_add_executor_job(
                        lambda: session.get("https://www.baillconnect.com/client/regulations", timeout=timeout)
                    )
                    reg_ids = set(re.findall(r"/client/regulations/(\d+)", reg_list_page.text))
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        await hass.async_add_executor_job(time.sleep, 2)
                        continue
                    _LOGGER.warning("❌ Impossible de récupérer la liste des régulations : %s", e)
                    return {"data": {"regulations": []}}

            # 🔄 Parcours des régulations
            for reg_id in reg_ids:
                for attempt in range(MAX_RETRIES):
                    try:
                        await hass.async_add_executor_job(SessionManager._initialize_for_regulation, int(reg_id))
                        session = await SessionManager.async_get_session(hass)
                        url = f"https://www.baillconnect.com/api-client/regulations/{reg_id}"

                        response = await hass.async_add_executor_job(
                            lambda: session.post(url=url, json={}, timeout=timeout)
                        )

                        if response.status_code != 200 or not response.content:
                            _LOGGER.warning("🔄 Session possiblement expirée, tentative de reconnexion")
                            await hass.async_add_executor_job(SessionManager._refresh_cookie)
                            session = await SessionManager.async_get_session(hass)
                            response = await hass.async_add_executor_job(
                                lambda: session.post(url=url, json={}, timeout=timeout)
                            )

                        # ✅ CORRECTION : on encapsule le data dans "data"
                        response_data = response.json()
                        regulations.append({
                            "id": int(reg_id),
                            "data": response_data
                        })
                        break

                    except Exception as e:
                        if attempt < MAX_RETRIES - 1:
                            await hass.async_add_executor_job(time.sleep, 2)
                            continue
                        _LOGGER.warning("⚠️ Erreur régulation %s : %s", reg_id, e)

                # 💤 Anti-flood
                await hass.async_add_executor_job(time.sleep, 1)

            return {"data": {"regulations": regulations}}

        return await fetch_data()

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=update_interval,
    )
