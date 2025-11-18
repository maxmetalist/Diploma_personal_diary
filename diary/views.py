from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from diary.forms import DiaryEntryForm
from diary.models import DiaryEntry, MediaFile

User = get_user_model()


def home(request):
    return render(request, "home.html")


class EntryListView(LoginRequiredMixin, ListView):
    model = DiaryEntry
    template_name = "diary/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        return DiaryEntry.objects.filter(author=self.request.user).order_by("-created_at")

    def get_template_names(self):
        # Если это AJAX-запрос, возвращаем частичный шаблон
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return ["diary/entries_partial.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Получаем медиафайлы пользователя
        user_images = MediaFile.objects.filter(user=user, file_type__startswith="image").order_by("-created_at")

        user_audio = MediaFile.objects.filter(user=user, file_type__startswith="audio").order_by("-created_at")

        # Статистика
        context.update(
            {
                "user_images": user_images,
                "user_audio": user_audio,
                "images_count": user_images.count(),
                "audio_count": user_audio.count(),
                "recent_activities": self.get_recent_activities(user),
            }
        )
        return context

    def get_recent_activities(self, user):
        """Генерирует список последних активностей"""
        activities = []

        # Последние записи
        recent_entries = DiaryEntry.objects.filter(author=user).order_by("-created_at")[:3]
        for entry in recent_entries:
            activities.append(
                {
                    "icon": "edit",
                    "color": "primary",
                    "description": f"Создана запись: {entry.title}",
                    "time": entry.created_at.strftime("%H:%M"),
                }
            )

        # Последние загрузки медиа
        recent_media = MediaFile.objects.filter(user=user).order_by("-created_at")[:2]
        for media in recent_media:
            icon = "image" if media.file_type.startswith("image") else "music"
            color = "success" if media.file_type.startswith("image") else "info"
            activities.append(
                {
                    "icon": icon,
                    "color": color,
                    "description": f"Загружен {media.file_type} файл",
                    "time": media.created_at.strftime("%H:%M"),
                }
            )

        return activities


class EntryDetailView(LoginRequiredMixin, DetailView):
    model = DiaryEntry
    template_name = "diary/entry_detail.html"
    context_object_name = "entry"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем отладочную информацию
        entry = self.object
        print(f"Запись: {entry.title}")
        print(f"Изображения: {entry.images.all()}")
        print(f"Количество изображений: {entry.images.count()}")
        return context


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/entry_form.html"
    success_url = reverse_lazy("diary:entry_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Сохраняем связь ManyToMany с изображениями
        if form.cleaned_data["images"]:
            self.object.images.set(form.cleaned_data["images"])
            print(f"Создана запись с {form.cleaned_data['images'].count()} изображениями")
        return response


class EntryUpdateView(LoginRequiredMixin, UpdateView):
    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/entry_form.html"
    context_object_name = "entry"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if self.request.method == "GET":
            kwargs.update({"initial": {"images": self.object.images.all()}})
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Обновляем связь с изображениями
        self.object.images.set(form.cleaned_data["images"])
        print(f"Обновлена запись с {form.cleaned_data['images'].count()} изображениями")
        return response

    def get_success_url(self):
        return reverse_lazy("diary:entry_detail", kwargs={"pk": self.object.pk})


class EntryDeleteView(LoginRequiredMixin, DeleteView):
    model = DiaryEntry
    template_name = "diary/entry_confirm_delete.html"
    success_url = reverse_lazy("diary:entry_list")
    context_object_name = "entry"

    def get_queryset(self):
        return super().get_queryset().filter(author=self.request.user)


def load_entries_ajax(request):
    """AJAX endpoint для загрузки списка записей"""

    if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.user.is_authenticated:
        try:
            # Получаем параметры фильтрации
            search_query = request.GET.get("search", "")
            date_filter = request.GET.get("date_filter", "all")
            page_number = request.GET.get("page", 1)

            entries = DiaryEntry.objects.filter(author=request.user).order_by("-created_at")

            if search_query:
                entries = entries.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))

            # Применяем фильтр по дате
            now = timezone.now()
            if date_filter == "week":
                week_ago = now - timedelta(days=7)
                entries = entries.filter(created_at__gte=week_ago)
            elif date_filter == "month":
                month_ago = now - timedelta(days=30)
                entries = entries.filter(created_at__gte=month_ago)
            elif date_filter == "year":
                year_ago = now - timedelta(days=365)
                entries = entries.filter(created_at__gte=year_ago)
            elif date_filter == "today":
                today = now.date()
                entries = entries.filter(created_at__date=today)

            # Сортировка и пагинация
            entries = entries.order_by("-created_at")
            paginator = Paginator(entries, 9)
            page_obj = paginator.get_page(page_number)

            # Рендерим частичный шаблон
            html = render_to_string(
                "diary/entries_partial.html",
                {
                    "entries": page_obj,
                    "paginator": paginator,
                    "is_paginated": page_obj.has_other_pages(),
                    "search_query": search_query,
                    "date_filter": date_filter,
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                    "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
                    "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
                },
            )

            return JsonResponse({"success": True, "html": html})
        except Exception as e:
            print(f"Error in load_entries_ajax: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Неверный запрос"})


def upload_media(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            uploaded_files = []

            # Обработка изображений
            images = request.FILES.getlist("images")
            for image in images:
                if image.content_type.startswith("image/"):
                    media_file = MediaFile.objects.create(user=request.user, file=image, file_type="image")
                    uploaded_files.append(media_file.file.name)

            # Обработка аудио
            audio_files = request.FILES.getlist("audio")
            for audio in audio_files:
                if audio.content_type.startswith("audio/"):
                    media_file = MediaFile.objects.create(user=request.user, file=audio, file_type="audio")
                    uploaded_files.append(media_file.file.name)

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Успешно загружено {len(uploaded_files)} файлов",
                    "files": uploaded_files,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Неверный запрос"})


def delete_media(request, pk):
    if request.method == "DELETE" and request.user.is_authenticated:
        try:
            media_file = get_object_or_404(MediaFile, pk=pk, user=request.user)
            media_file.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Неверный запрос"})

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "config"})
