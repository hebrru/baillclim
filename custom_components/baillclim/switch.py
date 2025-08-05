import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, reg_id: int, zone_id: int, zone_name: str):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._zone_id = zone_id
        self._zone_name = zone_name or f"Zone {zone_id}"

        self._attr_name = f"Zone {self._zone_name.strip()} Active"
        self._attr_unique_id = f"baillclim_zone_{self._reg_id}_{self._zone_id}"
        self._attr_icon = "mdi:vector-polyline"

    @property
    def is_on(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for zone in reg_data.get("zones", []):
                        if zone.get("id") == self._zone_id:
                            return zone.get("mode") == 3  # 3 = actif
        except Exception as e:
            _LOGGER.warning("⚠️ Erreur is_on pour zone %s (reg %s) : %s", self._zone_id, self._reg_id, e)
        return False

    def _set_zone_mode(self, value: int):
        try:
            SessionManager.initialize(
                self.coordinator.config_entry.data["email"],
                self.coordinator.config_entry.data["password"],
                reg_id=self._reg_id
            )
            session = SessionManager.get_session()
            url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
            payload = {f"zones.{self._zone_id}.mode": value}
            response = session.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                _LOGGER.info("✅ Zone %s (reg %s) changée en mode %s", self._zone_id, self._reg_id, value)
            else:
                _LOGGER.warning("❌ Échec requête API zone %s : %s", self._zone_id, response.text)
        except Exception as e:
            _LOGGER.debug(f"⏱️ Données zone manquantes, retry... zone_id={self._zone_id}, reg_id={self._reg_id}, erreur={e}")

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 3)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 0)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            'identifiers': {(DOMAIN, f'baillclim_reg_{self._reg_id}')},
            'name': f'BaillClim Régulation {self._reg_id}',
            'manufacturer': 'BaillConnect',
            'model': 'Régulation',
            'entry_type': 'service'
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.data:
        _LOGGER.debug("⏱️ Données zone manquantes, retry...")
        return

    entities = []
    data = coordinator.data.get("data", {})

    for reg in data.get("regulations", []):
        reg_data = reg.get("data", {})
        reg_id = reg_data.get("id")
        if not reg_id:
            continue

        for zone in reg_data.get("zones", []):
            zone_id = zone.get("id")
            name = zone.get("name", f"Zone {zone_id}")
            if zone_id is not None:
                entities.append(
                    ZoneSwitch(coordinator, reg_id, zone_id, name.strip())
                )

    async_add_entities(entities)
