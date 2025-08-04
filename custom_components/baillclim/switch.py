import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .utils import create_authenticated_session

_LOGGER = logging.getLogger(__name__)


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, reg_id, zone_id, zone_name, email, password):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._zone_id = zone_id
        self._name = zone_name or f"Zone {zone_id}"
        self._email = email
        self._password = password
        self._attr_name = f"Zone {self._name.strip()} Active"
        self._attr_unique_id = f"baillclim_zone_{reg_id}_{zone_id}"
        self._attr_icon = "mdi:vector-polyline"

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def is_on(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for zone in reg_data.get("zones", []):
                        if zone.get("id") == self._zone_id:
                            return zone.get("mode") == 3
        except Exception as e:
            _LOGGER.warning("❌ Erreur is_on pour zone %s (reg %s) : %s", self._zone_id, self._reg_id, e)

        return False

    def _set_zone_mode(self, value: int):
        try:
            session = create_authenticated_session(
                email=self._email,
                password=self._password,
                reg_id=self._reg_id
            )

            url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
            payload = {f"zones.{self._zone_id}.mode": value}
            response = session.post(url, json=payload)

            if response.status_code == 200:
                _LOGGER.info("✅ Zone %s (reg %s) changée en mode %s", self._zone_id, self._reg_id, value)
            else:
                _LOGGER.warning("❌ Échec requête API zone %s : %s", self._zone_id, response.text)

        except Exception as e:
            _LOGGER.error("❌ Erreur envoi changement zone %s (reg %s) : %s", self._zone_id, self._reg_id, e)

    async def async_turn_on(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 3)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hass.async_add_executor_job(self._set_zone_mode, 0)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    email = entry.data["email"]
    password = entry.data["password"]

    if not coordinator.data:
        _LOGGER.error("❌ Données manquantes : impossible de configurer les zones.")
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
                entities.append(ZoneSwitch(coordinator, reg_id, zone_id, name.strip(), email, password))

    async_add_entities(entities)
