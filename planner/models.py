from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', '🔵 Низкий'),
        ('medium', '🟡 Средний'),
        ('high', '🔴 Высокий'),
    ]

    STATUS_CHOICES = [
        ('todo', '📝 К выполнению'),
        ('in_progress', '🔄 В процессе'),
        ('done', '✅ Выполнено'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='Приоритет')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo', verbose_name='Статус')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Срок выполнения')
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата выполнения')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'

    def __str__(self):
        return self.title

    def is_overdue(self):
        if self.due_date and not self.completed_date:
            return timezone.now() > self.due_date
        return False

    def save(self, *args, **kwargs):
        if self.status == 'done' and not self.completed_date:
            self.completed_date = timezone.now()
        elif self.status != 'done' and self.completed_date:
            self.completed_date = None
        super().save(*args, **kwargs)
