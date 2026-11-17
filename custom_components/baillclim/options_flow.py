import voluptuous as vol
from homeassistant import config_entries


class BaillClimOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # Keep supporting releases before OptionsFlow provided config_entry.
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        options = self._entry.options
        if user_input is not None:
            return self.async_create_entry(title="", data={**options, **user_input})

        data = self._entry.data
        update_interval = options.get("update_interval", data.get("update_interval", 60))
        timeout = options.get("timeout", data.get("timeout", 15))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("update_interval", default=update_interval): vol.All(
                        int, vol.Range(min=10, max=600)
                    ),
                    vol.Required("timeout", default=timeout): vol.All(
                        int, vol.Range(min=5, max=60)
                    ),
                }
            ),
        )
