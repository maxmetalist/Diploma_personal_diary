import os

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class DiaryEntry(models.Model):
    title = models.CharField('title', max_length=200)
    content = models.TextField('content')
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='diary_entries')
    images = models.ManyToManyField(
        'MediaFile',
        blank=True,
        related_name='diary_entries',
        verbose_name='images',
        limit_choices_to={'file_type__startswith': 'image'}
    )

    class Meta:
        verbose_name = 'diary entry'
        verbose_name_plural = 'diary entries'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('diary:entry_detail', kwargs={'pk': self.pk})


class MediaFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField(max_length=20)  # 'image', 'audio', etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.file.name}"

    def filename(self):
        return os.path.basename(self.file.name)

    def is_image(self):
        return self.file_type.startswith('image')
