SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'reconstructor': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
        'donor': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
    'DEFAULT_AUTO_SCHEMA_CLASS': 'api.openapi.CustomAutoSchema',
}
