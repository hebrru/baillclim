import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    PRESET_COMFORT,
    PRESET_ECO,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .session_manager import SessionManager

_LOGGER = logging.getLogger(__name__)


class BaillclimClimate(CoordinatorEntity, ClimateEntity):
    # Ajout du support des presets (ECO / CONFORT)
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 30.0

    # Liste des presets disponibles
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO]

    def __init__(self, coordinator, thermostat, reg_id):
        super().__init__(coordinator)
        self._reg_id = reg_id
        self._id = thermostat.get("id")
        self._name = thermostat.get("name", f"Thermostat {self._id}").strip()
        self._attr_name = f"Climatiseur {self._name}"
        self._attr_unique_id = f"baillclim_climate_{self._reg_id}_{self._id}"

        # cache local pour le preset (si jamais l'API ne renvoie pas une valeur claire)
        self._preset_mode = PRESET_COMFORT

    # ------------------ Lecture des données ------------------

    @property
    def _thermostat_data(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {}).get("data", {})
                if reg_data.get("id") == self._reg_id:
                    for t in reg_data.get("thermostats", []):
                        if t.get("id") == self._id:
                            return t
        except Exception as e:
            _LOGGER.warning("Erreur lecture thermostat_data : %s", e)
        return {}

    @property
    def hvac_mode(self):
        return HVACMode.AUTO if self._thermostat_data.get("is_on") else HVACMode.OFF

    @property
    def target_temperature_low(self):
        """
        Consigne de chauffage affichée dans HA.

        - En mode CONFORT (t1_t2 = 1) → setpoint_hot_t1
        - En mode ECO     (t1_t2 = 2) → setpoint_hot_t2
        """
        th = self._thermostat_data
        t1_t2 = th.get("t1_t2", 1)

        if t1_t2 == 2:
            return th.get("setpoint_hot_t2")
        return th.get("setpoint_hot_t1")

    @property
    def target_temperature_high(self):
        """
        Consigne de froid affichée dans HA.

        - En mode CONFORT (t1_t2 = 1) → setpoint_cool_t1
        - En mode ECO     (t1_t2 = 2) → setpoint_cool_t2
        """
        th = self._thermostat_data
        t1_t2 = th.get("t1_t2", 1)

        if t1_t2 == 2:
            return th.get("setpoint_cool_t2")
        return th.get("setpoint_cool_t1")

    @property
    def current_temperature(self):
        return self._thermostat_data.get("temperature")

    # ------------------ ECO / CONFORT (presets) ------------------

    @property
    def preset_mode(self):
        """
        Retourne le mode ECO / CONFORT actuel.
        On lit directement t1_t2 :
          1 = T1 = Confort
          2 = T2 = Eco
        """
        th = self._thermostat_data
        t1_t2 = th.get("t1_t2")

        if t1_t2 == 2:
            return PRESET_ECO
        if t1_t2 == 1:
            return PRESET_COMFORT

        # fallback si valeur bizarre / absente
        return self._preset_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Bascule ECO / CONFORT côté BaillConnect via t1_t2."""
        if preset_mode not in self._attr_preset_modes:
            _LOGGER.warning("Preset inconnu demandé : %s", preset_mode)
            return

        # mémorisation locale
        self._preset_mode = preset_mode

        # 1 = confort (T1), 2 = éco (T2)
        t1_t2_value = 2 if preset_mode == PRESET_ECO else 1
        key = f"thermostats.{self._id}.t1_t2"

        await self._set_api_value(key, t1_t2_value)
        await self.coordinator.async_request_refresh()

    # ------------------ Attributs supplémentaires ------------------

    @property
    def extra_state_attributes(self):
        try:
            data = self.coordinator.data.get("data", {})
            for reg in data.get("regulations", []):
                reg_data = reg.get("data", {}).get("data", {})
                if reg_data.get("id") == self._reg_id:
                    mode = reg_data.get("uc_mode", 0)
                    MODES = {
                        0: "Arrêt",
                        1: "Froid",
                        2: "Chauffage",
                        3: "Désumidificateur",
                        4: "Ventilation"
                    }

                    th = self._thermostat_data
                    t1_t2 = th.get("t1_t2")

                    return {
                        "uc_mode": mode,
                        "mode_nom": MODES.get(mode, "Inconnu"),
                        "t1_t2": t1_t2,
                        "preset_mode": self.preset_mode,
                    }
        except Exception as e:
            _LOGGER.warning("Erreur extra_state_attributes : %s", e)
        return {}

    @property
    def device_info(self):
        return {
            'identifiers': {(DOMAIN, f'baillclim_reg_{self._reg_id}')},
            'name': f'BaillClim Régulation {self._reg_id}',
            'manufacturer': 'BaillConnect',
            'model': 'Régulation',
            'entry_type': 'service'
        }

    # ------------------ Commandes ------------------

    async def async_set_hvac_mode(self, hvac_mode):
        is_on = hvac_mode != HVACMode.OFF
        await self._set_api_value(f"thermostats.{self._id}.is_on", is_on)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        """
        Change les consignes en fonction du mode actif :

        - si t1_t2 = 1 (CONFORT) → écrit dans T1
        - si t1_t2 = 2 (ECO)     → écrit dans T2
        """
        th = self._thermostat_data
        t1_t2 = th.get("t1_t2", 1)

        # Chauffage
        if "target_temp_low" in kwargs:
            key = "setpoint_hot_t2" if t1_t2 == 2 else "setpoint_hot_t1"
            await self._set_api_value(
                f"thermostats.{self._id}.{key}",
                kwargs["target_temp_low"],
            )

        # Froid
        if "target_temp_high" in kwargs:
            key = "setpoint_cool_t2" if t1_t2 == 2 else "setpoint_cool_t1"
            await self._set_api_value(
                f"thermostats.{self._id}.{key}",
                kwargs["target_temp_high"],
            )

        await self.coordinator.async_request_refresh()

    async def _set_api_value(self, key, value):
        await SessionManager.async_initialize(
            self.hass,
            self.coordinator.config_entry.data["email"],
            self.coordinator.config_entry.data["password"],
            reg_id=self._reg_id
        )
        session = await SessionManager.async_get_session(self.hass)
        url = f"https://www.baillconnect.com/api-client/regulations/{self._reg_id}"
        payload = {key: value}

        def send():
            try:
                response = session.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    _LOGGER.info("✅ API OK : %s = %s", key, value)
                else:
                    _LOGGER.warning(
                        "❌ API ERROR (%s = %s) : %s",
                        key,
                        value,
                        response.text,
                    )
            except Exception as e:
                _LOGGER.error("Erreur requête API %s : %s", key, e)

        await self.hass.async_add_executor_job(send)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.config_entry = entry

    if not coordinator.data:
        _LOGGER.error("❌ Données manquantes dans le coordinator.")
        return

    data = coordinator.data.get("data", {})
    regulations = data.get("regulations", [])

    entities = []
    for reg in regulations:
        reg_data = reg.get("data", {}).get("data", {})
        reg_id = reg_data.get("id")
        if reg_id is None:
            continue
        for th in reg_data.get("thermostats", []):
            entities.append(BaillclimClimate(coordinator, th, reg_id))

    async_add_entities(entities)
