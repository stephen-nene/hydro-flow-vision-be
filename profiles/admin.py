from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User,UserImage


# Customizing UserAdmin for HealthcareUser
@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'date_of_birth', 'mfa_enabled', 'is_active', 'is_staff')
    list_filter = ('role', 'status', 'is_active', 'is_staff', 'date_of_birth')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username',)
    fieldsets = (
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth','blood_group', 'gender')}),
        (_('Access Control'), {'fields': ('role', 'status', 'mfa_enabled', 'groups', 'user_permissions')}),
        (_('Security'), {'fields': ('password', 'last_login', 'is_active', 'is_staff', 'is_superuser')}),
        (_('Audit Info'), {'fields': ('terms_accepted_at', 'privacy_policy_version')}),
    )


# Clinical Image Admin
@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'caption', 'sensitivity_level', 'image')
    search_fields = ('caption', 'content_object__username')
    list_filter = ('sensitivity_level',)
    ordering = ('-id',)
    fieldsets = (
        ('Image Details', {'fields': ('content_object', 'image', 'caption', 'context')}),
        ('Security', {'fields': ('sensitivity_level', 'access_log')}),
    )
