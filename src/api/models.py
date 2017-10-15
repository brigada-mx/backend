import binascii
import os

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class TokenBaseModel(models.Model):
    """Abstract token authorization model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


@python_2_unicode_compatible
class NurseUserToken(TokenBaseModel):
    user = models.OneToOneField('nurses.NurseUser', related_name='nurse_auth_token', on_delete=models.CASCADE)

    class Meta:
        # Work around for a bug in Django, https://code.djangoproject.com/ticket/19422
        # Also see corresponding ticket, https://github.com/tomchristie/django-rest-framework/issues/705
        verbose_name = _("Nurse Token")
        verbose_name_plural = _("Nurse Tokens")


@python_2_unicode_compatible
class ClientUserToken(TokenBaseModel):
    user = models.OneToOneField('clients.ClientUser', related_name='client_auth_token', on_delete=models.CASCADE)

    class Meta:
        # Work around for a bug in Django, https://code.djangoproject.com/ticket/19422
        # Also see corresponding ticket, https://github.com/tomchristie/django-rest-framework/issues/705
        verbose_name = _("Client Token")
        verbose_name_plural = _("Client Tokens")
