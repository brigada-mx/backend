from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, **kwargs):
        if not email:
            raise ValueError('Users must have an email')

        user = self.model(
            email=self.normalize_email(email),
            full_name=kwargs.pop('full_name', ''),
            **kwargs
        )

        password = kwargs.pop('password', None)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, *args, **kwargs):
        user = self.create_user(*args, **kwargs)
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
