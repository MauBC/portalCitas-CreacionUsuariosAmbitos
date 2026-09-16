COUNTRY_TEMPLATE_CONFIG = {
    "SLV": {
        "pais": "EL SALVADOR",
        "sociedad": "RANSA COMERCIAL",
        "perfil_usuario": "PERFIL CLIENTE",
        "tipo_documento": "DUI",
        "servicio_acceso": "PORTAL ACCESO CAM",
        "cliente_default": "DOCTOR SV",
        "force_default_client": False,
    },
    "PER": {
        "pais": "PERU",
        "sociedad": "RANSA COMERCIAL",
        "perfil_usuario": "PERFIL CLIENTE",
        "tipo_documento": "DNI",
        "servicio_acceso": "PORTAL ACCESO",
        "cliente_default": "",
        "force_default_client": False,
    },
}


USER_TYPE_CONFIG = {
    "PROVEEDOR": {
        "tipo_usuario": "USUARIO PROVEEDOR",
        "servicio": 1,
        "parametro": "PACCESO_PROVEEDOR",
    },
    "CLIENTE": {
        "tipo_usuario": "USUARIO CLIENTE",
        "servicio": 2,
        "parametro": "PACCESO_CLIENTE",
    },
}


SERVICES_SHEET_BY_COUNTRY = {
    country_code: [
        {
            "SERVICIO": country_config["servicio_acceso"],
            "PARAMETRO": USER_TYPE_CONFIG["PROVEEDOR"]["parametro"],
            "GRUPO": USER_TYPE_CONFIG["PROVEEDOR"]["servicio"],
        },
        {
            "SERVICIO": country_config["servicio_acceso"],
            "PARAMETRO": USER_TYPE_CONFIG["CLIENTE"]["parametro"],
            "GRUPO": USER_TYPE_CONFIG["CLIENTE"]["servicio"],
        },
    ]
    for country_code, country_config
    in COUNTRY_TEMPLATE_CONFIG.items()
}
