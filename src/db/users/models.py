import binascii
import os

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager

from db.config import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email, **kwargs):
        """Creates and saves a generic user with the given email, first_name, surname
        and password.
        """
        if not email:
            raise ValueError('Users must have an email')

        user = self.model(
            email=self.normalize_email(email),
            first_name=kwargs.pop('first_name', ''),
            surname=kwargs.pop('surname', ''),
            **kwargs
        )

        password = kwargs.pop('password', None)
        if not password:
            raise ValueError('Users must have a password')
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, *args, **kwargs):
        user = self.create_user(*args, **kwargs)
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomAbstractBaseUser(AbstractBaseUser, BaseModel):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.TextField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        abstract = True

    @property
    def is_staff(self):
        return False

    @property
    def is_organization_user(self):
        return False

    def get_short_name(self):  # required for subclasses of `AbstractBaseUser`
        return self.full_name

    def __str__(self):
        return self.email


class StaffUser(CustomAbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    @property
    def is_staff(self):
        """Staff users can use Django Admin Site.
        """
        return True


class OrganizationUser(CustomAbstractBaseUser):
    organization = models.ForeignKey('map.Organization')
    set_password_token = models.TextField(db_index=True, default='', blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            self.send_set_password_email()
        else:
            return super().save(*args, **kwargs)

    @property
    def is_organization_user(self):
        return True

    def send_set_password_email(self):
        self.set_password_token = binascii.hexlify(os.urandom(30)).decode()
        self.save()


class TokenBaseModel(models.Model):
    """Abstract token authorization model.
    """
    key = models.TextField(primary_key=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(30)).decode()

    def __str__(self):
        return self.key


class OrganizationUserToken(TokenBaseModel):
    user = models.OneToOneField('OrganizationUser', on_delete=models.CASCADE)
