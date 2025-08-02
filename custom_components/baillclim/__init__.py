"""BaillClim - Intégration BaillConnect pour Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "baillclim"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Initialisation via configuration.yaml (non utilisée)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Initialisation de BaillClim via l'interface (config flow)."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, [
        "sensor",
        "climate",
        "switch",
        "number",
        "select",
    ])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Déchargement de l'intégration."""
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
