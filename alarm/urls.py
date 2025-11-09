from django.urls import path

from alarm.views import AlarmClockView, AlarmCreateView, AlarmListView

app_name = 'alarm'

urlpatterns= [
    path('', AlarmClockView.as_view(), name='alarm_clock'),
    path('create/', AlarmCreateView.as_view(), name='alarm_create'),
    path('list/', AlarmListView.as_view(), name='alarm_list'),
]