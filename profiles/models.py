from django.db import models



from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
import pgcrypto
from uuid import uuid4, uuid1
from management.models import *


# Enums ------------------------------------------------------------------------
class UserRole(models.TextChoices):
    CUSTOMER = 'customer','customer'
    SYSTEM_ADMIN = 'system_admin', 'System Administrator'
    SUPPORT_STAFF = 'support', 'Support Staff'
    FINANCE_STAFF = 'finance', 'Finance Staff'
    

class UserStatus(models.TextChoices):
    INACTIVE = 'inactive', 'Inactive'    
    ACTIVE = 'active', 'Active'
    PENDING_VERIFICATION = 'pending', 'Pending Verification'
    SUSPENDED = 'suspended', 'Suspended'
    ARCHIVED = 'archived', 'Archived'


class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    NON_BINARY = 'non_binary', 'Non-binary'
    UNDISCLOSED = 'undisclosed', 'Prefer not to say'


# Helper Models ----------------------------------------------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  


def user_directory_path(instance, filename):
    model_name = instance.content_type.model
    user = getattr(instance.content_object, 'user', None)
    username = user.username if user else 'anonymous'
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid1()}.{ext}"
    return f"uploads/{model_name}/{username}/{unique_filename}"       


def validate_image_size(image):
    max_size_kb = 5120  # 5MB limit
    if image.size > max_size_kb * 1024:
        raise ValidationError(f"Image size exceeds {max_size_kb} KB.")


# Main Models -------------------------------------------------------------------
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CUSTOMER, db_index=True)
    status = models.CharField(max_length=20, choices=UserStatus.choices, default=UserStatus.INACTIVE, db_index=True)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.UNDISCLOSED)

    address = models.JSONField(null=True, blank=True)
    profile_image = models.ForeignKey('UserImage', null=True, blank=True, on_delete=models.SET_NULL)
    
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')],
        help_text="International format: +[country code][number]"
    )   


    groups = models.ManyToManyField(Group, related_name="users", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="user_permissions", blank=True)

    class Meta:
        verbose_name = "Healthcare User"
        verbose_name_plural = "Healthcare Users"
        indexes = [
            models.Index(fields=['username', 'email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
            models.Index(fields=['date_of_birth', 'gender']),
        ]
        permissions = [
            ('view_full_profile', "Can view complete user profile"),
            ('emergency_access', "Has emergency access privileges")
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.username} - {self.role}"




class UserImage(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    image = models.ImageField(
        upload_to='user_images/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'png', 'dcm']), validate_image_size]
    )
    caption = models.CharField(max_length=255, blank=True)
    context = models.TextField(blank=True)

    sensitivity_level = models.PositiveSmallIntegerField(
        choices=[(1, 'Public'), (2, 'Internal'), (3, 'Restricted')],
        default=2
    )
    access_log = models.JSONField(default=list)

    class Meta:
        verbose_name = "User Images"
        verbose_name_plural = "User Images"
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f"Image for {self.content_object} - {self.caption or 'No Caption'}"
