from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


# Enums

class UserStatus(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
    PENDING = 'pending', _('Pending')
    SUSPENDED = 'suspended', _('Suspended')
    DELETED = 'deleted', _('Deleted')


class UserRole(models.TextChoices):
    ADMIN = 'admin', _('Admin')
    USER = 'user', _('User')
    MODERATOR = 'moderator', _('Moderator')
    
class UserGender(models.TextChoices):
    MALE = 'male', _('Male')
    FEMALE = 'female', _('Female')
    NON_BINARY = 'non_binary', _('Non-binary')
    TRANSGENDER = 'transgender', _('Transgender')
    OTHER = 'other', _('Other')


# Abstract Timestamped Model

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Custom User Manager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', UserStatus.ACTIVE)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


# Custom User Model

class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(
        _('email address'),
        max_length=255,
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    username = models.CharField(_('username'), max_length=150, unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    bio = models.TextField(_('bio'), blank=True)
    profile = models.FileField(_('profile picture'), upload_to='profiles/', blank=True)
    avatar_url = models.URLField(_('avatar URL'), blank=True)
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    address = models.JSONField(_('address'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=20, choices=UserGender.choices, blank=True)
    email_verified = models.BooleanField(_('email verified'), default=False)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), null=True, blank=True)

    status = models.CharField(
        _('status'),
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.INACTIVE
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER
    )

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name or self.email
