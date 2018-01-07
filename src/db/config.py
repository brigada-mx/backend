from django.db import models


class BaseModel(models.Model):
    """An abstract base class model that provides self-updating `created` and
    `modified` fields, along with some methods for uniquely identifying instances.
    """
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def __repr__(self):
        """Reads fields list from model's `REPR_FIELDS` class attribute.
        """
        if not hasattr(self, 'REPR_FIELDS'):
            return super().__repr__()
        fields = self.REPR_FIELDS
        parts = ['{}('.format(self.__class__.__name__)]

        for f in fields:
            if hasattr(self, f):
                parts.append('{}={}, '.format(f, repr(self.__getattribute__(f))))
        parts.append(')')
        return ''.join(parts)

    def update_fields(self, **fields):
        """Avoids using `QuerySet.update` method.
        """
        for k, v in fields.items():
            setattr(self, k, v)
        self.save()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
