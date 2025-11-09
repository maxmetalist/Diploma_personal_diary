import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView

from planner.forms import TaskForm
from planner.models import Task


class PlanningView(LoginRequiredMixin, TemplateView):
    """Главная страница планинга"""
    template_name = 'planner/planning.html'

    def get_context_data(self, **kwargs):
        """Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        # Статистика задач
        tasks = Task.objects.filter(user=self.request.user)
        context.update({
            'title': 'Планинг',
            'page_description': 'Планировщик задач и событий',
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='done').count(),
            'overdue_tasks': tasks.filter(due_date__lt=timezone.now()).exclude(status='done').count(),
            'today_tasks': tasks.filter(
                due_date__date=timezone.now().date()
            ).exclude(status='done').count(),
        })
        return context


class TaskListView(LoginRequiredMixin, ListView):
    """Список всех задач"""
    model = Task
    template_name = 'planner/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)

        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Фильтрация по приоритету
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Фильтрация по дате создания
        created_date = self.request.GET.get('created_date')
        if created_date:
            queryset = queryset.filter(created_at__date=created_date)

        # Фильтрация по дедлайну
        due_date = self.request.GET.get('due_date')
        if due_date:
            queryset = queryset.filter(due_date__date=due_date)

        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Сортировка
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['created_at', '-created_at', 'due_date', '-due_date', 'priority', 'title']:
            queryset = queryset.order_by(sort_by)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои задачи'
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Создание новой задачи"""
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'
    success_url = reverse_lazy('planner:task_list')

    def get_initial(self):
        initial = super().get_initial()
        # Предустановка даты из параметра URL
        due_date = self.request.GET.get('due_date')
        if due_date:
            try:
                initial['due_date'] = due_date.replace('T', ' ') + ':00'
            except:
                pass
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание задачи'
        return context


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование задачи"""
    model = Task
    form_class = TaskForm
    template_name = 'planner/task_form.html'
    success_url = reverse_lazy('planner:task_list')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование задачи'
        return context

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление задачи"""
    model = Task
    template_name = 'planner/task_confirm_delete.html'
    success_url = reverse_lazy('planner:task_list')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class CalendarView(LoginRequiredMixin, TemplateView):
    """Для интеграции календаря в планинг"""
    template_name = 'planner/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = Task.objects.filter(user=self.request.user)

        # События
        calendar_events = []
        for task in tasks:
            if task.due_date:
                event = {
                    'id': task.id,
                    'title': task.title,
                    'start': task.due_date.isoformat(),
                    'url': reverse('planner:task_update', kwargs={'pk': task.id}),
                    'color': self.get_task_color(task),
                    'extendedProps': {
                        'priority': task.priority,
                    }
                }
                calendar_events.append(event)
        context.update({
            'title': 'Календарь',
            'calendar_events': json.dumps(calendar_events),
        })
        return context

    def get_task_color(self, task):
        colors = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#0d6efd',
        }
        return colors.get(task.priority, '#6c757d')
