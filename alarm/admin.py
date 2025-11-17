from django.contrib import admin

from .models import Alarm, AlarmSound


@admin.register(AlarmSound)
class AlarmSoundAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "created_at"]
    list_filter = ["is_default", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    fieldsets = (
        ("Основная информация", {"fields": ("name", "file", "is_default")}),
        ("Дополнительно", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "alarm_time", "is_active", "is_recurring", "created_at"]
    list_filter = ["is_active", "is_recurring", "created_at", "alarm_time"]
    search_fields = ["name", "reminder_text", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 20

    fieldsets = (
        ("Основная информация", {"fields": ("user", "name", "reminder_text", "alarm_time", "is_active")}),
        ("Повторение", {"fields": ("is_recurring", "days_of_week"), "classes": ("collapse",)}),
        ("Звук", {"fields": ("sound", "custom_sound"), "classes": ("collapse",)}),
        ("Даты", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "sound")
