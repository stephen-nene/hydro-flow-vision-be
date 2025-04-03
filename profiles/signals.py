
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserRole, UserStatus


# Signals ----------------------------------------------------------------------

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates role-specific profile when a new user is created.
    Also updates the user's status to active if they're a clinician or admin.
    """
    if created:
        if instance.role == UserRole.CLINICIAN:
            # Doctor.objects.create(user=instance)
            print("will do things here")
            # Automatically activate clinician accounts
            # instance.status = UserStatus.ACTIVE
            # instance.save()
            
        # elif instance.role == UserRole.PATIENT:
        #     Patient.objects.create(user=instance)
            
        # elif instance.role == UserRole.SYSTEM_ADMIN:
        #     # Admins might need special handling
        #     instance.status = UserStatus.ACTIVE
        #     instance.is_staff = True
        #     instance.is_superuser = True
        #     instance.save()
            
        elif instance.role == UserRole.NURSE:
            # Create nurse profile if you have a Nurse model
            pass
            
        elif instance.role == UserRole.SUPPORT_STAFF:
            # Create support staff profile if needed
            pass

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensures the profile is saved when the user is saved.
    """
    if hasattr(instance, 'clinician_profile'):
        instance.clinician_profile.save()
    if hasattr(instance, 'patient_profile'):
        instance.patient_profile.save()