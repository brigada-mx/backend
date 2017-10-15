import os

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = '{}.s3.amazonaws.com'.format(AWS_STORAGE_BUCKET_NAME)

AWS_ACCESS_KEY_ID = os.getenv('ASISTIA_AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('ASISTIA_AWS_SECRET_KEY')

AWS_PRELOAD_METADATA = True

STATICFILES_STORAGE = 'config.settings.dependencies.storages.StaticStorage'

DEFAULT_FILE_STORAGE = 'config.settings.dependencies.storages.MediaStorage'
