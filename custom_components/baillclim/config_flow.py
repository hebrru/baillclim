import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class BaillClimConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Casts sécurisés
            try:
                user_input["update_interval"] = int(user_input.get("update_interval", 60))
            except ValueError:
                user_input["update_interval"] = 60

            try:
                user_input["timeout"] = int(user_input.get("timeout", 15))
            except ValueError:
                user_input["timeout"] = 15

            return self.async_create_entry(title="BaillConnect", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("email"): str,
                vol.Required("password"): str,
                vol.Optional("update_interval", default=60): int,
                vol.Optional("timeout", default=15): int,
            }),
            errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        from .options_flow import BaillClimOptionsFlowHandler
        return BaillClimOptionsFlowHandler(config_entry)
