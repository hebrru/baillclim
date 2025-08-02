from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import asyncio

from .const import DOMAIN
from .coordinator import create_baillclim_coordinator

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    coordinator = create_baillclim_coordinator(hass, entry.data["email"], entry.data["password"])
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = entry.data
    hass.data[DOMAIN][entry.entry_id + "_coordinator"] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, [
        "sensor", "climate", "switch", "number", "select"
    ])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = all(
        await asyncio.gather(*[
            hass.config_entries.async_forward_entry_unload(entry, platform)
            for platform in ["sensor", "climate", "switch", "number", "select"]
        ])
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data[DOMAIN].pop(entry.entry_id + "_coordinator", None)
    return unload_ok