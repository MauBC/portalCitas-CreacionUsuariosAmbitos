COUNTRY_TEMPLATE_CONFIG = {
    "SLV": {
        "pais": "EL SALVADOR",
        "sociedad": "RANSA COMERCIAL",
        "perfil_usuario": "PERFIL CLIENTE",
        "tipo_documento": "DUI",

        # TEMPORAL.
        # En el futuro puede venir del formulario,
        # SharePoint, BD o alguna regla de negocio.
        "cliente_default": "DOCTOR SV",
        "force_default_client": False,
    },

    "PER": {
        "pais": "PERU",
        "sociedad": "RANSA COMERCIAL",
        "perfil_usuario": "PERFIL CLIENTE",
        "tipo_documento": "DNI",
        "cliente_default": "",
    },
}


USER_TYPE_CONFIG = {
    "PROVEEDOR": {
        "tipo_usuario": "USUARIO PROVEEDOR",
        "servicio": 1,
    },

    "CLIENTE": {
        "tipo_usuario": "USUARIO CLIENTE",
        "servicio": 2,
    },
}


SERVICES_SHEET = [
    {
        "SERVICIO": "PORTAL ACCESO CAM",
        "PARAMETRO": "PACCESO_PROVEEDOR",
        "GRUPO": 1,
    },
    {
        "SERVICIO": "PORTAL ACCESO CAM",
        "PARAMETRO": "PACCESO_CLIENTE",
        "GRUPO": 2,
    },
]


