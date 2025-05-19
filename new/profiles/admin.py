from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email', 
        'username', 
        'get_full_name', 
        'status', 
        'role',
        'email_verified',
        'is_active', 
        'is_staff',
        'last_login',
        'created_at'
    )
    
    list_filter = (
        'status',
        'role',
        'is_active',
        'is_staff',
        'email_verified',
        'gender',
        ('created_at', admin.DateFieldListFilter),
        ('last_login', admin.DateFieldListFilter),
    )
    
    search_fields = (
        'email',
        'username',
        'first_name',
        'last_name',
        'phone_number',
    )
    
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_login_ip')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'username',
                'first_name', 
                'last_name',
                'phone_number',
                'birth_date',
                'gender',
                'bio',
                'profile',
                'avatar_url',
                'address',
            )
        }),
        (_('Status & Role'), {
            'fields': (
                'status',
                'role',
                'email_verified',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {
            'fields': (
                'last_login',
                'last_login_ip',
                'created_at',
                'updated_at',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'status',
                'role',
                'is_active',
                'is_staff',
            ),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion, instead use status = DELETED
        return False

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }