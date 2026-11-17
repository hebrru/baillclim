import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
from .const import DOMAIN

class BaillClimOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # 🔄 Le rechargement est fait par l'update listener (__init__.py)
            user_input["timeout"] = int(user_input["timeout"])
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("update_interval", default=self.config_entry.options.get("update_interval", 60)): vol.All(int, vol.Range(min=10, max=600)),
                vol.Required("timeout", default=self.config_entry.options.get("timeout", 15)): NumberSelector(
                    NumberSelectorConfig(min=5, max=60, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
            }),
        )
