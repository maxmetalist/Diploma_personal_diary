from django.contrib import admin
from diary.models import DiaryEntry

@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'content', 'author__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
