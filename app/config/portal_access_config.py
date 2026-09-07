from app.config.portal_template_config import (
    COUNTRY_TEMPLATE_CONFIG,
)


PORTAL_ACCESS_SERVICE = {
    country_code:
        config["servicio_acceso"]
    for country_code, config
    in COUNTRY_TEMPLATE_CONFIG.items()
}
