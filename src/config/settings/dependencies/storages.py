from storages.backends.s3boto import S3BotoStorage

from pipeline.storage import PipelineMixin


class StaticStorage(PipelineMixin, S3BotoStorage):
    location = 'static'


class MediaStorage(S3BotoStorage):
    location = 'media'
