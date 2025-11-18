from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from alarm.forms import AlarmForm
from alarm.models import Alarm

# from alarm.tasks import check_alarms_task, trigger_alarm_task


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
    try:
        if request.user.is_authenticated:
            from django.utils import timezone

            print("\n" + "=" * 50)
            print(f" 🔍 ПРОВЕРКА БУДИЛЬНИКОВ ДЛЯ: {request.user}")
            print(f" ⏰ ТЕКУЩЕЕ ВРЕМЯ СЕРВЕРА: {timezone.now()}")
            print(f" 📅 ТЕКУЩАЯ ДАТА: {timezone.now().date()}")
            print(f" 📆 ДЕНЬ НЕДЕЛИ: {timezone.now().weekday()}")
            print("=" * 50)

            active_alarms = Alarm.objects.filter(user=request.user, is_active=True)
            # print(f"📋 НАЙДЕНО АКТИВНЫХ БУДИЛЬНИКОВ: {active_alarms.count()}")

            for alarm in active_alarms:
                print(f"\n--- БУДИЛЬНИК: {alarm.name} ---")
                print(f"   Время: {alarm.alarm_time}")
                print(f"   Повторяющийся: {alarm.is_recurring}")
                print(f"   Дни недели: {alarm.days_of_week}")
                print(f"   Дата создания: {alarm.created_at.date()}")

            ringing_alarms = []
            for alarm in active_alarms:
                print(f"\n🔔 ПРОВЕРЯЕМ: {alarm.name}")
                should_ring = alarm.should_ring_now()
                print(f"🎯 РЕЗУЛЬТАТ: {should_ring}")

                if should_ring:
                    # print(f"🚨 БУДИЛЬНИК ДОЛЖЕН ЗВОНИТЬ!")
                    ringing_alarms.append(
                        {
                            "id": alarm.id,
                            "name": alarm.name,
                            "reminder_text": alarm.reminder_text,
                            "sound_url": "/static/alarm_sounds/classic.mp3",
                        }
                    )

            print(f"\n🎊 ИТОГО СРАБОТАВШИХ: {len(ringing_alarms)}")
            print("=" * 50 + "\n")

            return JsonResponse({"ringing_alarms": ringing_alarms})

        return JsonResponse({"ringing_alarms": []})

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        return JsonResponse({"ringing_alarms": [], "error": str(e)})


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


"""
def test_alarm_check(request):
    # Ручной запуск проверки будильников (для тестирования)
    if request.user.is_superuser:
        result = check_alarms_task.delay()
        return JsonResponse({"status": "Задача запущена", "task_id": result.id})
    return JsonResponse({"status": "Доступ запрещен"})

def force_ring_alarm(request, pk):
    # Принудительное срабатывание будильника (для тестирования)
    if request.user.is_superuser:
        result = trigger_alarm_task.delay(pk)
        return JsonResponse({"status": "Будильник запущен", "task_id": result.id})
    return JsonResponse({"status": "Доступ запрещен"})


def debug_alarms(request):
    # Страница отладки будильников
    if request.user.is_authenticated:
        alarms = Alarm.objects.filter(user=request.user)

        debug_info = []
        for alarm in alarms:
            debug_info.append({
                'id': alarm.id,
                'name': alarm.name,
                'alarm_time': alarm.alarm_time,
                'is_active': alarm.is_active,
                'is_recurring': alarm.is_recurring,
                'days_of_week': alarm.days_of_week,
                'created_at': alarm.created_at,
            })

        return JsonResponse({
            'user': str(request.user),
            'current_time': timezone.now().isoformat(),
            'alarms': debug_info
        })
    return JsonResponse({'error': 'Not authenticated'})
"""


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "config"})
