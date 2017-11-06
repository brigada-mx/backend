from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from db.config import BaseModel
from db.users.manager import UserManager


class CustomAbstractBaseUser(AbstractBaseUser, BaseModel, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        # This model should not be created in the database
        abstract = True

    @property
    def is_staff(self):
        return False

    def get_short_name(self):  # required for subclasses of `AbstractBaseUser`
        return self.full_name

    def __str__(self):
        return self.email


class StaffUser(CustomAbstractBaseUser):

    @property
    def is_staff(self):
        """Staff users can use Django Admin Site.
        """
        return True
