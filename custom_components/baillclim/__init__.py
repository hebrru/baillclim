import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import create_baillclim_coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up BaillClim from configuration.yaml (non utilisé, mais requis)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BaillClim from a config entry."""

    email = entry.data["email"]
    password = entry.data["password"]

    coordinator = create_baillclim_coordinator(hass, email, password)

    # Appel initial pour récupérer les données
    await coordinator.async_config_entry_first_refresh()

    if coordinator.data is None:
        _LOGGER.error("❌ Les données du coordinator sont vides. Abandon du setup.")
        return False

    data = coordinator.data.get("data", {})

    if not isinstance(data, dict):
        _LOGGER.error(
            "❌ Format inattendu pour coordinator.data['data'] : type=%s, contenu=%s",
            type(data), data
        )
        return False

    if "regulations" in data and not isinstance(data["regulations"], list):
        _LOGGER.error(
            "❌ 'regulations' devrait être une liste. Contenu : %s",
            data["regulations"]
        )
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, [
        "sensor",
        "climate",
        "switch",
        "number",
        "select",
    ])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [
        "sensor",
        "climate",
        "switch",
        "number",
        "select",
    ])

    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
