from django.db import models


class BaseModel(models.Model):
    """An abstract base class model that provides self-updating `created` and
    `modified` fields.
    """
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)

    def _fields_to_string(self, fields, verbose=False):
        parts = [f'{self.__class__.__name__}('] if verbose else []

        for f in fields:
            if hasattr(self, f):
                parts.append(f'{f}={repr(self.__getattribute__(f))}')
        if verbose:
            parts.append(')')
        return ', '.join(parts)

    def __repr__(self):
        """Reads fields list from model's `REPR_FIELDS` class attribute.
        """
        if not hasattr(self, 'REPR_FIELDS'):
            return super().__repr__()
        return self._fields_to_string(self.REPR_FIELDS, verbose=True)

    def __str__(self):
        """Reads fields list from model's `STR_FIELDS` class attribute.
        """
        if not hasattr(self, 'STR_FIELDS'):
            return super().__str__()
        return self._fields_to_string(self.STR_FIELDS, verbose=False)

    def update_fields(self, **fields):
        """Avoids using `QuerySet.update` method.
        """
        for k, v in fields.items():
            setattr(self, k, v)
        self.save()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """https://stackoverflow.com/questions/4441539/why-doesnt-djangos-model-save-call-full-clean
        """
        self.full_clean()
        return super().save(*args, **kwargs)
