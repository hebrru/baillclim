import logging
import json
import re
import time
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)


def _extract_js_object(text: str, marker: str) -> str | None:
    start = text.find(marker)
    if start == -1:
        return None

    start = text.find("{", start)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    return None


def _extract_regulation_from_page(page_text: str, reg_id: int) -> dict | None:
    raw_regulation = (
        _extract_js_object(page_text, "assets.regulation")
        or _extract_js_object(page_text, "window.assets.regulation")
    )
    if not raw_regulation:
        return None

    try:
        regulation = json.loads(raw_regulation)
    except json.JSONDecodeError as err:
        _LOGGER.warning("Impossible de parser assets.regulation pour %s : %s", reg_id, err)
        return None

    if regulation.get("id") != reg_id:
        _LOGGER.debug(
            "Régulation ignorée : page %s, données %s",
            reg_id,
            regulation.get("id"),
        )
        return None

    return regulation


def _normalize_regulation_payload(payload: dict, reg_id: int) -> dict | None:
    if not isinstance(payload, dict):
        return None

    if isinstance(payload.get("data"), dict) and payload["data"].get("id") == reg_id:
        return payload["data"]

    if payload.get("id") == reg_id:
        return payload

    return None


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
                    raise UpdateFailed("Failed to retrieve regulations list")

            # 🔄 Parcours des régulations
            for reg_id in reg_ids:
                reg_id_int = int(reg_id)
                for attempt in range(MAX_RETRIES):
                    try:
                        page_text = await hass.async_add_executor_job(
                            SessionManager._initialize_for_regulation,
                            reg_id_int,
                        )
                        session = await SessionManager.async_get_session(hass)
                        regulation_data = _extract_regulation_from_page(
                            page_text,
                            reg_id_int,
                        )
                        if regulation_data is None:
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

                            regulation_data = _normalize_regulation_payload(
                                response.json(),
                                reg_id_int,
                            )

                        if regulation_data is None:
                            raise UpdateFailed(f"No usable data for regulation {reg_id}")

                        regulations.append({
                            "id": reg_id_int,
                            "data": {"data": regulation_data},
                        })
                        break

                    except Exception as e:
                        if attempt < MAX_RETRIES - 1:
                            await hass.async_add_executor_job(time.sleep, 2)
                            continue
                        _LOGGER.warning("⚠️ Erreur régulation %s : %s", reg_id, e)

                # 💤 Anti-flood
                await hass.async_add_executor_job(time.sleep, 1)

            if not regulations:
                raise UpdateFailed("No regulations data retrieved")

            return {"data": {"regulations": regulations}}

        return await fetch_data()

    return DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="baillclim_data",
        update_method=async_update_data,
        update_interval=update_interval,
    )
