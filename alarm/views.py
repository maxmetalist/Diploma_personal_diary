from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class AlarmClockView(LoginRequiredMixin, TemplateView):
    """CBV для страницы будильника"""
    template_name = 'alarm/alarm_clock.html'

    def get_context_data(self, **kwargs):
        """Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Будильник'
        context['page_description'] = 'Управление будильниками и напоминаниями'
        return context


# Дополнительные CBV для будущего функционала
class AlarmCreateView(LoginRequiredMixin, TemplateView):
    """CBV для создания будильника"""
    template_name = 'alarm/alarm_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание будильника'
        return context


class AlarmListView(LoginRequiredMixin, TemplateView):
    """CBV для списка будильников"""
    template_name = 'alarm/alarm_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои будильники'
        return context
