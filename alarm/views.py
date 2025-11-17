from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from alarm.forms import AlarmForm
from alarm.models import Alarm


class AlarmClockView(LoginRequiredMixin, TemplateView):
    """Контроллер для главной страницы будильника"""

    template_name = "alarm/alarm_clock.html"

    def get_context_data(self, **kwargs):
        """Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        context["title"] = "Будильник"
        context["page_description"] = "Управление будильниками и напоминаниями"
        return context


class AlarmCreateView(LoginRequiredMixin, CreateView):
    model = Alarm
    form_class = AlarmForm
    template_name = "alarm/alarm_form.html"
    success_url = reverse_lazy("alarm:alarm_list")

    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Обработка валидной формы"""
        form.instance.user = self.request.user

        # Обработка дней недели
        days_of_week = self.request.POST.getlist("days_of_week")
        if days_of_week:
            form.instance.days_of_week = [int(day) for day in days_of_week]

        # Обработка своей мелодии
        use_custom_sound = self.request.POST.get("use_custom_sound") == "on"
        if not use_custom_sound:
            form.instance.custom_sound = None

        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
        """Обработка невалидной формы"""
        print("Form errors:", form.errors)
        return super().form_invalid(form)


class AlarmListView(LoginRequiredMixin, ListView):
    """Список будильников"""

    model = Alarm
    template_name = "alarm/alarm_list.html"
    context_object_name = "alarms"
    paginate_by = 10

    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user).order_by("alarm_time")


class AlarmUpdateView(LoginRequiredMixin, UpdateView):
    model = Alarm
    form_class = AlarmForm
    template_name = "alarm/alarm_form.html"
    success_url = reverse_lazy("alarm:alarm_list")

    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        initial["days_of_week"] = self.object.days_of_week
        initial["use_custom_sound"] = bool(self.object.custom_sound)
        return initial


class AlarmDeleteView(LoginRequiredMixin, DeleteView):
    model = Alarm
    template_name = "alarm/alarm_confirm_delete.html"
    success_url = reverse_lazy("alarm:alarm_list")

    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user)


class AlarmDetailView(LoginRequiredMixin, DetailView):
    model = Alarm
    template_name = "alarm/alarm_detail.html"
    context_object_name = "alarm"

    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user)


def check_active_alarms(request):
    """Проверяет активные будильники для текущего пользователя"""
    if request.user.is_authenticated:
        print(f"🔍 Проверка будильников для пользователя: {request.user}")

        active_alarms = Alarm.objects.filter(user=request.user, is_active=True)

        print(f"📋 Найдено активных будильников: {active_alarms.count()}")

        ringing_alarms = []
        for alarm in active_alarms:
            if alarm.should_ring_now():
                print(f"🎯 Будильник {alarm.name} должен звонить!")
                ringing_alarms.append(
                    {
                        "id": alarm.id,
                        "name": alarm.name,
                        "reminder_text": alarm.reminder_text,
                        "sound_url": alarm.get_sound_url(),
                    }
                )
            else:
                print(f"❌ Будильник {alarm.name} не должен звонить")

        print(f"🎊 Итого сработавших будильников: {len(ringing_alarms)}")
        return JsonResponse({"ringing_alarms": ringing_alarms})

    return JsonResponse({"ringing_alarms": []})


def alarm_stop(request, pk):
    """Останавливает сработавший будильник"""
    if request.method == "POST":
        alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
        alarm.is_active = False
        alarm.save()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False})


def alarm_ring(request, pk):
    """Страница срабатывания будильника"""
    alarm = get_object_or_404(Alarm, pk=pk, user=request.user)
    return render(request, "alarm/alarm_ring.html", {"alarm": alarm})
