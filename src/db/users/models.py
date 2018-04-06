import binascii
import os

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

from db.config import BaseModel
from jobs.messages import send_email


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
    first_name = models.TextField(max_length=100, db_index=True)
    surnames = models.TextField(max_length=100, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'surnames']

    class Meta:
        abstract = True

    @property
    def is_staff(self):
        return False

    @property
    def is_organization_user(self):
        return False

    @property
    def is_donor_user(self):
        return False

    @property
    def full_name(self):
        return ' '.join(f'{self.first_name} {self.surnames}'.split())

    def get_short_name(self):  # required for subclasses of `AbstractBaseUser`
        return self.first_name

    def __str__(self):
        return self.email


class StaffUser(CustomAbstractBaseUser, PermissionsMixin):
    password = models.CharField(max_length=128, blank=True)
    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.pk is None:
            if not self.password:
                self.set_unusable_password()
        return super().save(*args, **kwargs)

    @property
    def is_staff(self):
        """Staff users can use Django Admin Site.
        """
        return True


class CustomAbstractPublicUser(CustomAbstractBaseUser):
    password = models.CharField(max_length=128, blank=True)
    set_password_token = models.TextField(db_index=True, default='', blank=True)
    set_password_token_created = models.DateTimeField(null=True, blank=True)
    is_mainuser = models.BooleanField(blank=True, default=False, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        """
        if self.pk is None:
            if not self.password:
                self.set_unusable_password()
            self.is_mainuser = self.is_mainuser_on_create()
            return self.send_set_password_email(save=True, reset=False)
        return super().save(*args, **kwargs)

    def send_set_password_email(self, save=True, reset=True):
        self.set_password_token_created = timezone.now()
        self.set_password_token = binascii.hexlify(os.urandom(30)).decode()
        if save:
            super().save()

        if reset:
            self.reset_password_email()
        else:
            self.activate_account_email()


class OrganizationUser(CustomAbstractPublicUser):
    organization = models.ForeignKey('map.Organization')

    @property
    def is_organization_user(self):
        return True

    def is_mainuser_on_create(self):
        return OrganizationUser.objects.filter(organization=self.organization).first() is None

    def reset_password_email(self):
        subject = 'Restablecer tu contraseña Brigada'
        body = """
        <a href="{}/establecer?token={}&email={}" target="_blank">Haz clic aquí para restablecer tu contraseña</a>.<br><br>
        Si no pediste restablecer tu contraseña puedes borrar este mail.<br><br>
        """.format(os.getenv('CUSTOM_SITE_URL'), self.set_password_token, self.email)
        send_email.delay([self.email], subject, body)

    def activate_account_email(self):
        subject = 'Activa tu cuenta Brigada'
        body = """¡Gracias por crear tu cuenta con Brigada!<br><br>
        Te faltan dos pasos para activar tu cuenta y convertirte en un usuario experto:<br><br>
        1. <a href="{}/establecer?token={}&email={}" target="_blank">Activar tu cuenta</a><br><br>
        2. <a href="https://calendly.com/brigada/capacitacion" target="_blank">Agendar tu capacitación virtual</a><br><br>
        Saludos,<br><br>
        Eduardo Mancera<br>
        Director de Brigada<br>
        <a href="mailto:eduardo@fortana.co">eduardo@fortana.co</a>
        """.format(os.getenv('CUSTOM_SITE_URL'), self.set_password_token, self.email)
        send_email.delay([self.email], subject, body)


class DonorUser(CustomAbstractPublicUser):
    donor = models.ForeignKey('map.Donor')

    @property
    def is_donor_user(self):
        return True

    def is_mainuser_on_create(self):
        return DonorUser.objects.filter(donor=self.donor).first() is None

    def reset_password_email(self):
        subject = 'Restablecer tu contraseña de donador Brigada'
        body = """
        <a href="{}/establecer?token={}&email={}&type=donor" target="_blank">Haz clic aquí para restablecer tu contraseña de donador</a>.<br><br>
        Si no pediste restablecer tu contraseña puedes borrar este mail.<br><br>
        """.format(os.getenv('CUSTOM_SITE_URL'), self.set_password_token, self.email)
        send_email.delay([self.email], subject, body)

    def activate_account_email(self):
        subject = 'Activa tu cuenta Brigada'
        body = """¡Gracias por crear tu cuenta de donador con Brigada!<br><br>
        Te faltan dos pasos para activar tu cuenta y convertirte en un usuario experto:<br><br>
        1. <a href="{}/establecer?token={}&email={}&type=donor" target="_blank">Activar tu cuenta</a><br><br>
        2. <a href="https://calendly.com/brigada/capacitacion-donador" target="_blank">Agendar tu capacitación</a><br><br>
        Saludos,<br><br>
        Eduardo Mancera<br>
        Director de Brigada<br>
        <a href="mailto:eduardo@fortana.co">eduardo@fortana.co</a>
        """.format(os.getenv('CUSTOM_SITE_URL'), self.set_password_token, self.email)
        send_email.delay([self.email], subject, body)


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
    user = models.OneToOneField('OrganizationUser', related_name='auth_token', on_delete=models.CASCADE)


class DonorUserToken(TokenBaseModel):
    user = models.OneToOneField('DonorUser', related_name='auth_token', on_delete=models.CASCADE)
