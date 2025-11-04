from django.db import models
from django.urls import reverse
from users.models import CustomUser


class DiaryEntry(models.Model):
    title = models.CharField('title', max_length=200)
    content = models.TextField('content')
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='diary_entries')

    class Meta:
        verbose_name = 'diary entry'
        verbose_name_plural = 'diary entries'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('diary:entry_detail', kwargs={'pk': self.pk})
