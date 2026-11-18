"""Exclusions Recorder pour les anciennes versions de Home Assistant."""

from homeassistant.core import HomeAssistant


def exclude_attributes(_hass: HomeAssistant) -> set[str]:
    """Exclut le JSON de diagnostic sur les versions utilisant cette API."""
    return {"data"}
