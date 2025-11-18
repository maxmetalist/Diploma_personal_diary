import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from planner.forms import TaskForm
from planner.models import Notification, NotificationPreference, Task


class PlanningView(LoginRequiredMixin, TemplateView):
    """Главная страница планинга"""

    template_name = "planner/planning.html"

    def get_context_data(self, **kwargs):
        """Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        # Статистика задач
        tasks = Task.objects.filter(user=self.request.user)
        context.update(
            {
                "title": "Планинг",
                "page_description": "Планировщик задач и событий",
                "total_tasks": tasks.count(),
                "completed_tasks": tasks.filter(status="done").count(),
                "overdue_tasks": tasks.filter(due_date__lt=timezone.now()).exclude(status="done").count(),
                "today_tasks": tasks.filter(due_date__date=timezone.now().date()).exclude(status="done").count(),
            }
        )
        return context


class TaskListView(LoginRequiredMixin, ListView):
    """Список всех задач"""

    model = Task
    template_name = "planner/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)

        # Фильтрация по статусу
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Фильтрация по приоритету
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Фильтрация по дате создания
        created_date = self.request.GET.get("created_date")
        if created_date:
            queryset = queryset.filter(created_at__date=created_date)

        # Фильтрация по дедлайну
        due_date = self.request.GET.get("due_date")
        if due_date:
            queryset = queryset.filter(due_date__date=due_date)

        # Поиск
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # Сортировка
        sort_by = self.request.GET.get("sort_by", "-created_at")
        if sort_by in ["created_at", "-created_at", "due_date", "-due_date", "priority", "title"]:
            queryset = queryset.order_by(sort_by)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мои задачи"
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Создание новой задачи"""

    model = Task
    form_class = TaskForm
    template_name = "planner/task_form.html"
    success_url = reverse_lazy("planner:task_list")

    def get_initial(self):
        initial = super().get_initial()
        # Предустановка даты из параметра URL
        due_date = self.request.GET.get("due_date")
        if due_date:
            try:
                initial["due_date"] = due_date.replace("T", " ") + ":00"
            except Exception as e:
                print(f"Обнаружена ошибка {e}")

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Создание задачи"
        return context


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование задачи"""

    model = Task
    form_class = TaskForm
    template_name = "planner/task_form.html"
    success_url = reverse_lazy("planner:task_list")

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Редактирование задачи"
        return context


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление задачи"""

    model = Task
    template_name = "planner/task_confirm_delete.html"
    success_url = reverse_lazy("planner:task_list")

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class CalendarView(LoginRequiredMixin, TemplateView):
    """Для интеграции календаря в планинг"""

    template_name = "planner/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.filter(user=self.request.user)

        # События
        calendar_events = []
        for task in tasks:
            if task.due_date:
                event = {
                    "id": task.id,
                    "title": task.title,
                    "start": task.due_date.isoformat(),
                    "url": reverse("planner:task_update", kwargs={"pk": task.id}),
                    "color": self.get_task_color(task),
                    "extendedProps": {
                        "priority": task.priority,
                    },
                }
                calendar_events.append(event)
        context.update(
            {
                "title": "Календарь",
                "calendar_events": json.dumps(calendar_events),
            }
        )
        return context

    def get_task_color(self, task):
        colors = {
            "high": "#dc3545",
            "medium": "#ffc107",
            "low": "#0d6efd",
        }
        return colors.get(task.priority, "#6c757d")


class NotificationView(LoginRequiredMixin, View):
    """Класс для работы с уведомлениями"""

    def get(self, request):
        """Получить список уведомлений"""
        try:
            # Параметры запроса
            unread_only = request.GET.get("unread_only", "false").lower() == "true"
            limit = int(request.GET.get("limit", 10))
            offset = int(request.GET.get("offset", 0))

            # Базовый queryset
            notifications = Notification.objects.filter(user=request.user)

            # Фильтрация по прочитанным
            if unread_only:
                notifications = notifications.filter(is_read=False)

            # Сортировка и ограничение
            notifications = notifications.select_related("task").order_by("-created_at")
            total_count = notifications.count()
            notifications = notifications[offset : offset + limit]

            # Сериализация данных
            notifications_data = []
            for notification in notifications:
                notifications_data.append(
                    {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.notification_type,
                        "type_display": notification.get_notification_type_display(),
                        "is_read": notification.is_read,
                        "is_sent": notification.is_sent,
                        "created_at": notification.created_at.isoformat(),
                        "scheduled_for": notification.scheduled_for.isoformat(),
                        "task": (
                            {
                                "id": notification.task.id if notification.task else None,
                                "title": notification.task.title if notification.task else None,
                                "url": f"/planner/task/{notification.task.id}/edit/" if notification.task else None,
                            }
                            if notification.task
                            else None
                        ),
                    }
                )

            return JsonResponse(
                {
                    "success": True,
                    "notifications": notifications_data,
                    "total_count": total_count,
                    "unread_count": Notification.objects.filter(user=request.user, is_read=False).count(),
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    def post(self, request):
        """Обработать действия с уведомлениями"""
        try:
            data = json.loads(request.body)
            action = data.get("action")
            notification_id = data.get("notification_id")

            if not action or not notification_id:
                return JsonResponse({"success": False, "error": "Не указаны action или notification_id"})

            notification = Notification.objects.get(id=notification_id, user=request.user)

            if action == "mark_as_read":
                notification.mark_as_read()
                return JsonResponse({"success": True})

            elif action == "mark_all_as_read":
                Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
                return JsonResponse({"success": True})

            elif action == "delete":
                notification.delete()
                return JsonResponse({"success": True})

            else:
                return JsonResponse({"success": False, "error": "Неизвестное действие"})

        except Notification.DoesNotExist:
            return JsonResponse({"success": False, "error": "Уведомление не найдено"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


class NotificationPreferenceView(LoginRequiredMixin, View):
    """Настройка уведомлений"""

    def get(self, request):
        """Получить настройки уведомлений"""
        try:
            preferences, created = NotificationPreference.objects.get_or_create(user=request.user)

            return JsonResponse(
                {
                    "success": True,
                    "preferences": {
                        "enable_email_notifications": preferences.enable_email_notifications,
                        "enable_push_notifications": preferences.enable_push_notifications,
                        "enable_browser_notifications": preferences.enable_browser_notifications,
                        "notify_before_deadline": preferences.notify_before_deadline,
                        "deadline_reminder_time": preferences.deadline_reminder_time,
                        "notify_on_overdue": preferences.notify_on_overdue,
                        "quiet_hours_start": (
                            preferences.quiet_hours_start.isoformat() if preferences.quiet_hours_start else None
                        ),
                        "quiet_hours_end": (
                            preferences.quiet_hours_end.isoformat() if preferences.quiet_hours_end else None
                        ),
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    def post(self, request):
        """Обновить настройки уведомлений"""
        try:
            data = json.loads(request.body)
            preferences, created = NotificationPreference.objects.get_or_create(user=request.user)

            # Обновляем настройки
            preferences.enable_email_notifications = data.get(
                "enable_email_notifications", preferences.enable_email_notifications
            )
            preferences.enable_push_notifications = data.get(
                "enable_push_notifications", preferences.enable_push_notifications
            )
            preferences.enable_browser_notifications = data.get(
                "enable_browser_notifications", preferences.enable_browser_notifications
            )
            preferences.notify_before_deadline = data.get("notify_before_deadline", preferences.notify_before_deadline)
            preferences.deadline_reminder_time = data.get("deadline_reminder_time", preferences.deadline_reminder_time)
            preferences.notify_on_overdue = data.get("notify_on_overdue", preferences.notify_on_overdue)

            # Обработка времени тишины
            quiet_hours_start = data.get("quiet_hours_start")
            quiet_hours_end = data.get("quiet_hours_end")

            if quiet_hours_start:
                preferences.quiet_hours_start = quiet_hours_start
            if quiet_hours_end:
                preferences.quiet_hours_end = quiet_hours_end

            preferences.save()

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "config"})
