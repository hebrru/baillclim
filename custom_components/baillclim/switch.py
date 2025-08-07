import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)

BACKUP_SCHEDULES = {}
BOOST_SWITCHES = {}
BOOST_ACTIVATION_TRACKER = set()


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, reg_id, zone_id, zone_name):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._attr_name = f"Activation Zone {zone_name.strip()}"
        self._attr_unique_id = f"baillclim_zone_{reg_id}_{zone_id}"
        self._attr_icon = "mdi:vector-polyline"

    @property
    def is_on(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {}).get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for zone in reg_data.get("zones", []):
                        if zone.get("id") == self._zone_id:
                            return zone.get("mode") == 3
        except Exception as e:
            _LOGGER.warning("Erreur is_on pour zone %s (reg %s) : %s", self._zone_id, self._reg_id, e)
        return False

    async def _set_zone_mode(self, hass: HomeAssistant, value: int):
        await SessionManager.async_initialize(
            hass,
            self.coordinator.config_entry.data["email"],
            self.coordinator.config_entry.data["password"],
            reg_id=self._reg_id
        )
        session = await SessionManager.async_get_session(hass)
        url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
        payload = {f"zones.{self._zone_id}.mode": value}
        await hass.async_add_executor_job(lambda: session.post(url, json=payload, timeout=10))

    async def async_turn_on(self, **kwargs):
        await self._set_zone_mode(self.hass, 3)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._set_zone_mode(self.hass, 0)
        await self.coordinator.async_request_refresh()
        for mode in ["confort", "eco"]:
            switch = BOOST_SWITCHES.get((self._reg_id, self._zone_id, mode))
            if switch and switch.is_on:
                switch._is_on = False
                switch.async_write_ha_state()
                await switch.force_restore_if_needed(force_restore=True)

    async def async_update(self):
        await super().async_update()
        data = self.coordinator.data.get("data", {})
        for reg in data.get("regulations", []):
            reg_data = reg.get("data", {}).get("data", {})
            if reg_data.get("id") == self._reg_id:
                uc_mode = reg_data.get("uc_mode")
                for zone in reg_data.get("zones", []):
                    if zone.get("id") == self._zone_id:
                        if uc_mode == 0 or zone.get("mode") != 3:
                            for mode in ["confort", "eco"]:
                                switch = BOOST_SWITCHES.get((self._reg_id, self._zone_id, mode))
                                if switch and switch.is_on:
                                    _LOGGER.info(f"❌ Désactivation du boost {mode} car uc_mode=0 ou zone inactive")
                                    switch._is_on = False
                                    switch.async_write_ha_state()
                                    await switch.force_restore_if_needed(force_restore=True)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"baillclim_reg_{self._reg_id}")},
            "name": f"BaillClim Régulation {self._reg_id}",
            "manufacturer": "BaillConnect",
            "model": "Régulation",
            "entry_type": "service",
        }


class BoostBaseSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, reg_id, zone_id, zone_name, mode):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._mode = mode
        self._attr_name = f"Boost {mode.capitalize()} {zone_name.strip()}"
        self._attr_unique_id = f"baillclim_boost_{mode}_{reg_id}_{zone_id}"
        self._attr_icon = "mdi:rocket-launch" if mode == "confort" else "mdi:leaf"
        self._is_on = False
        BOOST_SWITCHES[(reg_id, zone_id, mode)] = self

    @property
    def is_on(self):
        return self._is_on

    def _get_current_schedule(self):
        data = self.coordinator.data.get("data", {})
        for reg in data.get("regulations", []):
            reg_data = reg.get("data", {}).get("data", {})
            if reg_data.get("id") == self._reg_id:
                for zone in reg_data.get("zones", []):
                    if zone.get("id") == self._zone_id:
                        return {
                            f"zones.{self._zone_id}.schedule_{j}_{h}": zone.get(f"schedule_{j}_{h}")
                            for j in range(7) for h in range(24)
                        }
        return {}

    def _set_schedule(self, value):
        return {f"zones.{self._zone_id}.schedule_{j}_{h}": value for j in range(7) for h in range(24)}

    async def _post_api(self, hass: HomeAssistant, payload):
        await SessionManager.async_initialize(
            hass,
            self.coordinator.config_entry.data["email"],
            self.coordinator.config_entry.data["password"],
            reg_id=self._reg_id
        )
        session = await SessionManager.async_get_session(hass)
        url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
        await hass.async_add_executor_job(lambda: session.post(url, json=payload, timeout=10))

    async def async_turn_on(self, **kwargs):
        boost_key = (self._reg_id, self._zone_id)

        data = self.coordinator.data.get("data", {})
        zone_active = False
        uc_mode = None
        for reg in data.get("regulations", []):
            reg_data = reg.get("data", {}).get("data", {})
            if reg_data.get("id") == self._reg_id:
                uc_mode = reg_data.get("uc_mode")
                for zone in reg_data.get("zones", []):
                    if zone.get("id") == self._zone_id:
                        zone_active = zone.get("mode") == 3

        if uc_mode == 0:
            _LOGGER.warning(f"⛔ Boost {self._mode} refusé car le mode général (uc_mode) est sur 'Arrêt'")
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Le système est actuellement en mode 'Arrêt'. Veuillez le repasser en Chauffage ou Froid avant d'activer le Boost {self._mode.capitalize()}.",
                    "title": f"Boost {self._mode.capitalize()} refusé",
                    "notification_id": f"boost_blocked_ucmode_{self._reg_id}_{self._zone_id}_{self._mode}"
                },
                blocking=True
            )
            return

        if not zone_active:
            _LOGGER.warning(f"❌ Impossible d'activer le Boost {self._mode} car la zone {self._zone_id} est désactivée")
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": f"Activez d'abord la zone avant d'activer le Boost {self._mode.capitalize()}.",
                    "title": f"Boost {self._mode.capitalize()} refusé",
                    "notification_id": f"boost_{self._reg_id}_{self._zone_id}_{self._mode}"
                },
                blocking=True
            )
            return

        if boost_key not in BACKUP_SCHEDULES:
            BACKUP_SCHEDULES[boost_key] = self._get_current_schedule()

        other_mode = "eco" if self._mode == "confort" else "confort"
        other_switch = BOOST_SWITCHES.get((self._reg_id, self._zone_id, other_mode))
        if other_switch and other_switch.is_on:
            other_switch._is_on = False
            other_switch.async_write_ha_state()

        self._is_on = True
        BOOST_ACTIVATION_TRACKER.add(self._attr_unique_id)
        await self._post_api(self.hass, self._set_schedule(1 if self._mode == "confort" else 2))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()
        BOOST_ACTIVATION_TRACKER.discard(self._attr_unique_id)
        await self.force_restore_if_needed()
        await self.coordinator.async_request_refresh()

    async def force_restore_if_needed(self, force_restore=False):
        boost_key = (self._reg_id, self._zone_id)
        other_mode = "eco" if self._mode == "confort" else "confort"
        other_switch = BOOST_SWITCHES.get((self._reg_id, self._zone_id, other_mode))
        other_on = other_switch.is_on if other_switch else False

        if (force_restore or not other_on) and boost_key in BACKUP_SCHEDULES:
            await self._post_api(self.hass, BACKUP_SCHEDULES.pop(boost_key))

    async def async_update(self):
        data = self.coordinator.data.get("data", {})
        for reg in data.get("regulations", []):
            reg_data = reg.get("data", {}).get("data", {})
            if reg_data.get("id") == self._reg_id:
                for zone in reg_data.get("zones", []):
                    if zone.get("id") == self._zone_id:
                        boost_id = self._attr_unique_id
                        if zone.get("mode") != 3 and (self._is_on or boost_id in BOOST_ACTIVATION_TRACKER):
                            _LOGGER.info(f"Zone {self._zone_id} désactivée → désactivation du boost {self._mode}")
                            self._is_on = False
                            self.async_write_ha_state()
                            BOOST_ACTIVATION_TRACKER.discard(boost_id)
                            await self.force_restore_if_needed(force_restore=True)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"baillclim_reg_{self._reg_id}")},
            "name": f"BaillClim Régulation {self._reg_id}",
            "manufacturer": "BaillConnect",
            "model": "Régulation",
            "entry_type": "service",
        }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if not coordinator.data:
        _LOGGER.debug("Données manquantes, attente...")
        return

    entities = []
    data = coordinator.data.get("data", {})
    for reg in data.get("regulations", []):
        reg_data = reg.get("data", {}).get("data", {})
        reg_id = reg_data.get("id")
        if not reg_id:
            continue
        for zone in reg_data.get("zones", []):
            zone_id = zone.get("id")
            name = zone.get("name", f"Zone {zone_id}")
            if zone_id is not None:
                entities.append(ZoneSwitch(coordinator, reg_id, zone_id, name.strip()))
                entities.append(BoostBaseSwitch(coordinator, reg_id, zone_id, name.strip(), "confort"))
                entities.append(BoostBaseSwitch(coordinator, reg_id, zone_id, name.strip(), "eco"))

    async_add_entities(entities)

    for entity in entities:
        hass.async_create_task(entity.async_update())
