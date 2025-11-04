from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser
from users.forms import CustomUserCreationForm, CustomUserChangeForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'first_name', 'country', 'phone', 'is_staff']
    list_filter = ['is_staff', 'is_active', 'country']
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('country', 'phone', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('first_name', 'country', 'phone', 'avatar')}),
    )
    ordering = ['email']
