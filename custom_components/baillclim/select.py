import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .session_manager import SessionManager

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

    if not coordinator.data:
        _LOGGER.debug("⏱️ Données mode manquantes, retry...")
        return

    data = coordinator.data.get("data", {})
    if not isinstance(data, dict):
        _LOGGER.debug("⏱️ Données mode manquantes, retry...")
        return

    entities = []

    for reg in data.get("regulations", []):
        reg_data = reg.get("data", {}).get("data", {})
        reg_id = reg_data.get("id")
        if reg_id is not None:
            entities.append(BaillclimModeSelect(coordinator, reg_id, entry))
        else:
            _LOGGER.warning("❌ Aucune 'id' trouvée dans reg.data : %s", reg)

    async_add_entities(entities, True)


class BaillclimModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, regulation_id: int, config_entry: ConfigEntry):
        super().__init__(coordinator)
        self._regulation_id = regulation_id
        self._config_entry = config_entry
        self._attr_name = f"Mode Climatisation {regulation_id}"
        self._attr_unique_id = f"baillclim_mode_clim_{regulation_id}"
        self._attr_options = list(MODES.keys())

    @property
    def current_option(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {}).get("data", {})
                if reg_data.get("id") == self._regulation_id:
                    uc_mode = reg_data.get("uc_mode")
                    return {v: k for k, v in MODES.items()}.get(uc_mode)
        except Exception as e:
            _LOGGER.warning("⚠️ Erreur current_option (reg_id=%s) : %s", self._regulation_id, e)
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in MODES:
            _LOGGER.warning("❌ Mode sélectionné invalide : %s", option)
            return

        try:
            await SessionManager.async_initialize(
                self.hass,
                self._config_entry.data["email"],
                self._config_entry.data["password"],
                reg_id=self._regulation_id
            )
            session = await SessionManager.async_get_session(self.hass)
            url = f"https://www.baillconnect.com/api-client/regulations/{self._regulation_id}"
            payload = {"uc_mode": MODES[option]}

            response = await self.hass.async_add_executor_job(
                lambda: session.post(url, json=payload, timeout=10)
            )

            if response.status_code == 200:
                _LOGGER.info("✅ Mode changé (reg_id=%s) → %s", self._regulation_id, option)
            else:
                _LOGGER.warning("❌ Échec changement mode (reg_id=%s) : %s", self._regulation_id, response.text)

        except Exception as e:
            _LOGGER.warning("⚠️ async_select_option error (reg_id=%s): %s", self._regulation_id, e)

        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"baillclim_reg_{self._regulation_id}")},
            "name": f"BaillClim Régulation {self._regulation_id}",
            "manufacturer": "BaillConnect",
            "model": "Régulation",
            "entry_type": "service",
        }
