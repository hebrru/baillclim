import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class BaillClimOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # 🔄 Recharge l'intégration avec les nouvelles options
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("update_interval", default=self.config_entry.options.get("update_interval", 60)): vol.All(int, vol.Range(min=10, max=600)),
                vol.Required("timeout", default=self.config_entry.options.get("timeout", 15)): vol.All(int, vol.Range(min=5, max=60)),
            }),
        )
