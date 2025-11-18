from django.urls import path

from alarm.views import (
    AlarmClockView,
    AlarmCreateView,
    AlarmDeleteView,
    AlarmDetailView,
    AlarmListView,
    AlarmUpdateView,
    alarm_ring,
    alarm_stop,
    check_active_alarms,
    health_check,
)

app_name = "alarm"

urlpatterns = [
    path("", AlarmClockView.as_view(), name="alarm_clock"),
    path("create/", AlarmCreateView.as_view(), name="alarm_create"),
    path("list/", AlarmListView.as_view(), name="alarm_list"),
    path("<int:pk>/", AlarmDetailView.as_view(), name="alarm_detail"),
    path("<int:pk>/edit/", AlarmUpdateView.as_view(), name="alarm_edit"),
    path("<int:pk>/delete/", AlarmDeleteView.as_view(), name="alarm_delete"),
    path("check-alarms/", check_active_alarms, name="check_alarms"),
    path("<int:pk>/stop/", alarm_stop, name="alarm_stop"),
    path("<int:pk>/ring/", alarm_ring, name="alarm_ring"),
    # Тестирование будильников (раскомментировать пути ниже)
    # path('test-check/', test_alarm_check, name='test_alarm_check'),
    # path('<int:pk>/force-ring/', force_ring_alarm, name='force_ring_alarm'),
    # path('debug/', debug_alarms, name='debug_alarms'),
    path("health/", health_check, name="health_check"),
]
