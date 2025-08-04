import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .utils import create_authenticated_session

_LOGGER = logging.getLogger(__name__)

MODES = {
    "Arrêt": 0,
    "Froid": 1,
    "Chauffage": 2,
    "Désumidificateur": 3,
    "Ventilation": 4
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    email = entry.data["email"]
    password = entry.data["password"]
    coordinator.config_entry = entry

    if not coordinator.data:
        _LOGGER.error("❌ Données absentes du coordinator. Abandon du setup.")
        return

    data = coordinator.data.get("data", {})
    if not isinstance(data, dict):
        _LOGGER.error("❌ Format inattendu de coordinator.data['data'] : %s", data)
        return

    entities = []

    for reg in data.get("regulations", []):
        reg_data = reg.get("data", {})
        reg_id = reg_data.get("id")
        if reg_id is not None:
            entities.append(BaillclimModeSelect(coordinator, email, password, reg_id))
        else:
            _LOGGER.warning("❌ Aucune 'id' trouvée dans reg.data : %s", reg)

    async_add_entities(entities, True)


class BaillclimModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, email: str, password: str, regulation_id: int):
        super().__init__(coordinator)
        self._email = email
        self._password = password
        self._regulation_id = regulation_id
        self._attr_name = f"Mode Climatisation {regulation_id}"
        self._attr_unique_id = f"baillclim_mode_clim_{regulation_id}"
        self._attr_options = list(MODES.keys())

    @property
    def current_option(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._regulation_id:
                    uc_mode = reg_data.get("uc_mode")
                    return {v: k for k, v in MODES.items()}.get(uc_mode)
        except Exception as e:
            _LOGGER.warning("⚠️ Erreur accès current_option (reg_id=%s) : %s", self._regulation_id, e)
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in MODES:
            _LOGGER.warning("❌ Mode sélectionné invalide : %s", option)
            return

        await self.hass.async_add_executor_job(self._set_mode_sync, option)
        await self.coordinator.async_request_refresh()

    def _set_mode_sync(self, option: str):
        try:
            session = create_authenticated_session(
                email=self._email,
                password=self._password,
                reg_id=self._regulation_id
            )

            url = f"https://www.baillconnect.com/api-client/regulations/{self._regulation_id}"
            payload = {"uc_mode": MODES[option]}
            response = session.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                _LOGGER.info("✅ Mode changé (reg_id=%s) → %s", self._regulation_id, option)
            else:
                _LOGGER.warning("❌ Échec changement mode (reg_id=%s) : %s", self._regulation_id, response.text)

        except Exception as e:
            _LOGGER.error("❌ Erreur changement de mode (reg_id=%s) : %s", self._regulation_id, e)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"baillclim_reg_{self._regulation_id}")},
            "name": f"BaillClim Régulation {self._regulation_id}",
            "manufacturer": "BaillConnect",
            "model": "Régulation",
            "entry_type": "service",
        }
